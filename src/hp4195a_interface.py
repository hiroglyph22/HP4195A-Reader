import sys
import os
import time
import multiprocessing
import numpy as np
import logging
import logging.handlers
import pyvisa
import csv

class hp4195a_interface(multiprocessing.Process):


    def __init__(self, command_queue, message_queue, data_queue, logger_queue):
        super(hp4195a_interface, self).__init__()
        self.command_queue = command_queue
        self.message_queue = message_queue
        self.data_queue = data_queue
        self.logging_queue = logger_queue

        self.mag_data = []
        self.phase_data = []
        self.freq_data = []

        self.visa_resource_name = 'GPIB0::17::INSTR' 
        self.device_id = 'HP4195A'
        self.instrument = None
        self.rm = None # This is the pyvisa resource manager


    """Processes a single command from the queue."""
    def handle_command(self, command):
        
        self.logger.info('Received \"{}\" from GUI'.format(command))

        if command == 'connect':
            self.visa_connect()

        elif command == 'disconnect':
            self.visa_disconnect()

        elif command == 'start_acquisition':
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

        elif command == 'set_center_and_span':
            center_freq = self.command_queue.get()
            span_freq = self.command_queue.get()

            self.send_command(f"CENTER = {center_freq} HZ")
            self.send_command(f"SPAN = {span_freq} HZ")

            # Send a confirmation message back to the UI
            self.message_queue.put(True)

        elif command == 'set_start_stop':
            start_freq = self.command_queue.get()
            stop_freq = self.command_queue.get()
            self.send_command(f"START = {start_freq} HZ")
            self.send_command(f"STOP = {stop_freq} HZ")
            # Send a confirmation message back to the UI
            self.message_queue.put(True)

        elif command == 'set_center_frequency':
            center_freq_hz = self.command_queue.get()
            command_string = f"CENTER = {center_freq_hz} HZ"
            self.send_command(command_string)

        elif command == 'send_command':
            self.command = self.command_queue.get()
            self.logger.info('Sending GPIB command: {}'.format(self.command))
            self.response = self.send_query(self.command)
            self.logger.info('Response: {}'.format(self.response))
            self.data_queue.put(self.response)

        elif command == 'low_res_sweep':
            self.logger.info('Starting low resolution sweep')
            self.send_command('RBW = 100 HZ')
            if self.single_sweep(45):
                self.message_queue.put(True)
            self.send_command('RBW = 300 HZ')

        elif command == 'sweeping_range_of_amplitudes':
            params = self.command_queue.get()
            start_amp = params["start"]
            stop_amp = params["stop"]
            step_amp = params["step"]
            save_dir = params["dir"]

            self.logger.info(f"Starting amplitude sweep from {start_amp} to {stop_amp} dBm.")

            for amp in np.arange(start_amp, stop_amp + step_amp, step_amp):
                self.logger.info(f"Setting amplitude to {amp} dBm.")
                self.send_command(f"OSC1 = {amp} DBM")
                
                # Perform a single sweep and acquire data manually
                self.send_command('SWM2')
                self.send_command('SWTRG')
                time.sleep(45)

                mag_ok = self.acquire_mag_data()
                phase_ok = self.acquire_phase_data()
                freq_ok = self.acquire_freq_data()

                if mag_ok and phase_ok and freq_ok:
                    # Send FREQUENCY then MAGNITUDE to the GUI queue
                    self.data_queue.put(self.freq_data)
                    self.data_queue.put(self.mag_data)

                    # Save all data to the CSV file
                    file_name = os.path.join(save_dir, f"amplitude_sweep_{amp}dBm.csv")
                    self.logger.info(f"Saving data to {file_name}")
                    try:
                        with open(file_name, "w", newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow(['Frequency', 'Magnitude', 'Phase'])
                            rows = zip(self.freq_data, self.mag_data, self.phase_data)
                            writer.writerows(rows)
                        # Clear data for the next loop
                        self.mag_data, self.phase_data, self.freq_data = [], [], []
                    except IOError as e:
                        self.logger.error(f"Could not write to file {file_name}: {e}")
                        self.message_queue.put(False)
                        return
                else:
                    self.logger.error(f"Data acquisition failed at amplitude {amp} dBm.")
                    self.message_queue.put(False)
                    return
            
            self.logger.info("Amplitude sweep finished successfully.")
            self.message_queue.put(True)


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
            command = self.command_queue.get()
            self.logger.info('Received \"{}\" from GUI'.format(command))
            self.handle_command(command)


    def visa_connect(self):
        self.logger.info('Starting VISA communications')
        try:
            self.rm = pyvisa.ResourceManager()
            self.instrument = self.rm.open_resource(self.visa_resource_name)
            # Set a timeout (in milliseconds)
            self.instrument.timeout = 5000 

            # Check instrument ID
            # Query the instrument for its full identity string
            identity_full = self.instrument.query('ID?')
            
            # The instrument response can be verbose, so we split it into lines
            # and take only the first line for a clean ID.
            identity_clean = identity_full.splitlines()[0]
            
            self.logger.info(f"Connected to: {identity_clean}")
            if self.device_id in identity_clean:
                self.logger.info('Successfully found {}'.format(self.device_id))
                self.message_queue.put(True)
            else:
                self.logger.warning(f'Device ID mismatch. Expected {self.device_id}, got {identity_clean}')
                self.instrument.close()
                self.message_queue.put(False)
                
        except pyvisa.errors.VisaIOError as e:
            self.logger.error(f"VISA Error: {e}")
            self.message_queue.put(False)

    def visa_disconnect(self):
        self.logger.info('Disconnecting VISA connection')
        if self.instrument:
            self.instrument.close()
            self.instrument = None
        self.rm = None
        self.message_queue.put(True)

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

    def acquire_all_data(self):
        """Acquires mag, phase, and freq data and checks for validity."""
        if self.acquire_mag_data() and self.acquire_phase_data() and self.acquire_freq_data():
            if len(self.mag_data) == len(self.freq_data) and len(self.phase_data) == len(self.freq_data):
                self.logger.info('Data length check passed.')
                self.data_queue.put(self.mag_data)
                self.data_queue.put(self.phase_data)
                self.data_queue.put(self.freq_data)
                return True
            else:
                self.logger.warning('Data length check failed.')
                return False
        self.logger.error('Failed to acquire all data types.')
        return False

    def send_command(self, command):
        self.logger.info('Sent \"{}\"'.format(command))
        if self.instrument:
            self.instrument.write(command)

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
    
    def single_sweep(self, sleepDuration):
        self.logger.info('Starting single sweep')

        self.send_command('SWM2')
        self.send_command('SWTRG')

        time.sleep(sleepDuration)

        self.logger.info('Sweep complete. Acquiring data.')

        # Returns True on success, False on failure
        return self.acquire_all_data()