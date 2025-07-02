import sys
import os
import time
# Telnetlib is no longer needed
import multiprocessing
import numpy as np
import logging
import logging.handlers
import pyvisa # Import the new library
import csv # <-- ADDED: Import the csv module

class hp4195a(multiprocessing.Process):
    def __init__(self, command_queue, message_queue, data_queue, logger_queue):
        super(hp4195a, self).__init__()
        self.command_queue = command_queue
        self.message_queue = message_queue
        self.data_queue = data_queue
        self.logging_queue = logger_queue

        self.mag_data = []
        self.phase_data = []
        self.freq_data = []

        # --- MODIFIED: Replaced Telnet/GPIB attributes with VISA resource name ---
        # Replace this with the address you found in Step 2
        self.visa_resource_name = 'GPIB0::17::INSTR' 
        self.device_id = 'HP4195A'
        self.instrument = None # This will hold the connection to the instrument
        self.rm = None # This is the pyvisa resource manager

    def run(self):
        '''
        This function will run when the class is launched as a separate
        process.
        '''
        self.qh = logging.handlers.QueueHandler(self.logging_queue)
        self.root = logging.getLogger()
        self.root.setLevel(logging.DEBUG)
        self.root.addHandler(self.qh)
        self.logger = logging.getLogger(__name__)

        while True:
            self.command = self.command_queue.get()
            self.logger.info('Received \"{}\" from GUI'.format(self.command))
            
            # --- MODIFIED: Calls new connect/disconnect methods ---
            if self.command == 'connect':
                self.logger.info('Connecting to HP4195A via VISA')
                self.visa_connect()

            elif self.command == 'disconnect':
                self.logger.info('Disconnecting from HP4195A')
                self.visa_disconnect()

            elif self.command == 'start_acquisition':
                # This part of the logic remains the same
                self.logger.info('Starting data acquisition')
                if self.acquire_mag_data():
                    if self.acquire_phase_data():
                        if self.acquire_freq_data():
                            self.logger.info('Acquired data OK')
                        else:
                            self.logger.warning('Frequency data acquisition failed')
                            self.message_queue.put(False)
                    else:
                        self.logger.warning('Phase data acquisition failed')
                        self.message_queue.put(False)
                else:
                    self.logger.warning('Magnitude data acquisition failed')
                    self.message_queue.put(False)

                mag_check = len(self.mag_data) == len(self.freq_data)
                phase_check = len(self.phase_data) == len(self.freq_data)

                if mag_check and phase_check:
                    self.logger.info('Data length check passed ({}, {}, {})'.format(len(self.mag_data),len(self.phase_data),len(self.freq_data)))

                    self.message_queue.put(True)
                    self.data_queue.put(self.mag_data)
                    self.data_queue.put(self.phase_data)
                    self.data_queue.put(self.freq_data)
                    self.mag_data = []
                    self.phase_data = []
                    self.freq_data = []
                else:
                    self.logger.warning('Data length check failed ({}, {}, {})'.format(len(self.mag_data),len(self.phase_data),len(self.freq_data)))
                    self.message_queue.put(False)

            elif self.command == 'set_center_frequency':
                center_freq_hz = self.command_queue.get()
                command_string = f"CENTER = {center_freq_hz} HZ"
                self.send_command(command_string)

            elif self.command == 'send_command':
                self.command =  self.command_queue.get()
                self.logger.info('Sending GPIB command: {}'.format(self.command))
                self.response = self.send_query(self.command)
                self.logger.info('Response: {}'.format(self.response))
                self.data_queue.put(self.response)

    # --- NEW METHOD: Replaces telnet_connect ---
    def visa_connect(self):
        self.logger.info('Starting VISA communications')
        try:
            self.rm = pyvisa.ResourceManager()
            self.instrument = self.rm.open_resource(self.visa_resource_name)
            # Set a timeout (in milliseconds)
            self.instrument.timeout = 5000 
            # Check instrument ID
            identity = self.instrument.query('ID?')
            self.logger.info(f"Connected to: {identity}")
            if self.device_id in identity:
                self.logger.info('Successfully found {}'.format(self.device_id))
                self.message_queue.put(True)
            else:
                self.logger.warning(f'Device ID mismatch. Expected {self.device_id}, got {identity}')
                self.instrument.close()
                self.message_queue.put(False)
        except pyvisa.errors.VisaIOError as e:
            self.logger.error(f"VISA Error: {e}")
            self.message_queue.put(False)

    # --- NEW METHOD: Replaces telnet_disconnect ---
    def visa_disconnect(self):
        self.logger.info('Disconnecting VISA connection')
        if self.instrument:
            self.instrument.close()
            self.instrument = None
        self.rm = None
        self.message_queue.put(True)

    # --- MODIFIED: These methods now use VISA commands ---
    def acquire_mag_data(self):
        raw_mag_data = self.send_query('A?')
        mag_data = np.fromstring(raw_mag_data, dtype=float, sep=',')
        if len(mag_data) > 0:
            self.mag_data = mag_data
            return True

    def acquire_phase_data(self):
        raw_phase_data = self.send_query('B?')
        phase_data = np.fromstring(raw_phase_data, dtype=float, sep=',')
        if len(phase_data) > 0:
            self.phase_data = phase_data
            return True

    def acquire_freq_data(self):
        raw_freq_data = self.send_query('X?')
        freq_data = np.fromstring(raw_freq_data, dtype=float, sep=',')
        if len(freq_data) > 0:
            self.freq_data = freq_data
            return True

    # --- MODIFIED: Replaces telnet command with VISA write ---
    def send_command(self, command):
        self.logger.info('Sent \"{}\"'.format(command))
        if self.instrument:
            self.instrument.write(command)

    # --- MODIFIED: Replaces telnet query with VISA query ---
    def send_query(self, command):
        self.logger.info('Querying \"{}\"'.format(command))
        if self.instrument:
            try:
                response = self.instrument.query(command)
                self.logger.info('Received {} of {}'.format(len(response), type(response)))
                return response.strip()
            except pyvisa.errors.VisaIOError as e:
                self.logger.error(f"VISA Query Error: {e}")
                return "Query failed"
        return "Not connected"
