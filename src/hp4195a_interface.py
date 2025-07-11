"""
HP4195A Network/Spectrum Analyzer Interface Module.

This module provides a multiprocessing interface for communicating with
an HP4195A Network/Spectrum Analyzer via GPIB/VISA.
"""

import os
import time
import multiprocessing
import numpy as np
import logging
import logging.handlers
import pyvisa
import csv
from typing import Optional, List

try:
    # Try relative imports first (for when running as a module/package)
    from .constants import Commands, GPIBCommands, SweepTimings, DefaultValues
except ImportError:
    # Fall back to absolute imports (for when running directly)
    from constants import Commands, GPIBCommands, SweepTimings, DefaultValues


class HP4195AInterface(multiprocessing.Process):
    """
    Interface class for HP4195A Network/Spectrum Analyzer.
    
    This class runs as a separate process and handles all communication
    with the HP4195A instrument via GPIB/VISA. It processes commands from
    a queue and sends responses back through message and data queues.
    
    ARCHITECTURE:
    ┌─────────────────────────────────────────────────────────────────┐
    │ GUI Process                                                     │
    │    ↓ (Commands via Queue)                                       │
    │ run() method ← Process entry point & command loop               │
    │    ↓                                                            │
    │ Command Handlers ← Business logic & multi-step workflows       │
    │    ↓                                                            │
    │ Instrument Interface ← Low-level VISA/GPIB communication       │
    │    ↓                                                            │
    │ HP4195A Hardware                                                │
    └─────────────────────────────────────────────────────────────────┘
    """


    def __init__(self, command_queue: multiprocessing.Queue, 
                 message_queue: multiprocessing.Queue, 
                 data_queue: multiprocessing.Queue, 
                 logger_queue: multiprocessing.Queue):
        """
        Initialize the HP4195A interface.
        
        Args:
            command_queue: Queue for receiving commands from GUI
            message_queue: Queue for sending status messages to GUI
            data_queue: Queue for sending measurement data to GUI
            logger_queue: Queue for logging messages
        """
        super(HP4195AInterface, self).__init__()
        self.command_queue = command_queue
        self.message_queue = message_queue
        self.data_queue = data_queue
        self.logging_queue = logger_queue

        # Data storage
        self.mag_data: List[float] = []
        self.phase_data: List[float] = []
        self.freq_data: List[float] = []

        # VISA configuration
        self.visa_resource_name = DefaultValues.VISA_RESOURCE_NAME
        self.device_id = DefaultValues.DEVICE_ID
        self.instrument: Optional[pyvisa.Resource] = None
        self.rm: Optional[pyvisa.ResourceManager] = None
        
        # Logger will be initialized in run() method
        self.logger: Optional[logging.Logger] = None

    # =========================================================================
    # COMMAND HANDLERS AND APPLICATION LOGIC LAYER
    # =========================================================================
    # The methods below handle commands received from the GUI and orchestrate
    # multi-step workflows. They implement the application's business logic
    # and call the low-level instrument methods (defined after run()) as needed.
    # This separation keeps high-level workflows separate from hardware details.

    def handle_command(self, command: str) -> None:
        """
        Process a single command from the command queue.
        
        Args:
            command: The command string to process
        """
        self.logger.info(f'Received "{command}" from GUI')

        if command == Commands.CONNECT.value:
            self._handle_connect()
        elif command == Commands.DISCONNECT.value:
            self._handle_disconnect()
        elif command == Commands.START_ACQUISITION.value:
            self._handle_start_acquisition()
        elif command == Commands.SET_CENTER_AND_SPAN.value:
            self._handle_set_center_and_span()
        elif command == Commands.SET_START_STOP.value:
            self._handle_set_start_stop()
        elif command == Commands.SET_CENTER_FREQUENCY.value:
            self._handle_set_center_frequency()
        elif command == Commands.SEND_COMMAND.value:
            self._handle_send_command()
        elif command == Commands.LOW_RES_SWEEP.value:
            self._handle_low_res_sweep()
        elif command == Commands.SWEEPING_RANGE_OF_AMPLITUDES.value:
            self._handle_sweeping_range_of_amplitudes()
        else:
            self.logger.warning(f'Unknown command: {command}')

    def _handle_connect(self) -> None:
        """Handle connection to the instrument."""
        self.visa_connect()

    def _handle_disconnect(self) -> None:
        """Handle disconnection from the instrument."""
        self.visa_disconnect()

    def _handle_start_acquisition(self) -> None:
        """Handle data acquisition request."""
        self.logger.info('Starting data acquisition')
        
        success = (self.acquire_mag_data() and 
                  self.acquire_phase_data() and 
                  self.acquire_freq_data())
        
        if not success:
            self.logger.warning('Data acquisition failed')
            self.message_queue.put(False)
            return

        # Validate data consistency
        if self._validate_data_consistency():
            self.logger.info(f'Data acquisition successful. Lengths: mag={len(self.mag_data)}, '
                           f'phase={len(self.phase_data)}, freq={len(self.freq_data)}')
            self.message_queue.put(True)
            self._send_data_to_queue()
            self._clear_data()
        else:
            self.logger.warning(f'Data length validation failed. Lengths: mag={len(self.mag_data)}, '
                              f'phase={len(self.phase_data)}, freq={len(self.freq_data)}')
            self.message_queue.put(False)

    def _handle_set_center_and_span(self) -> None:
        """Handle setting center frequency and span."""
        center_freq = self.command_queue.get()
        span_freq = self.command_queue.get()

        self.send_command(GPIBCommands.CENTER.value.format(center_freq))
        self.send_command(GPIBCommands.SPAN.value.format(span_freq))
        self.message_queue.put(True)

    def _handle_set_start_stop(self) -> None:
        """Handle setting start and stop frequencies."""
        start_freq = self.command_queue.get()
        stop_freq = self.command_queue.get()
        
        self.send_command(GPIBCommands.START.value.format(start_freq))
        self.send_command(GPIBCommands.STOP.value.format(stop_freq))
        self.message_queue.put(True)

    def _handle_set_center_frequency(self) -> None:
        """Handle setting center frequency only."""
        center_freq_hz = self.command_queue.get()
        self.send_command(GPIBCommands.CENTER.value.format(center_freq_hz))

    def _handle_send_command(self) -> None:
        """Handle sending a raw GPIB command."""
        command = self.command_queue.get()
        self.logger.info(f'Sending GPIB command: {command}')
        response = self.send_query(command)
        self.logger.info(f'Response: {response}')
        self.data_queue.put(response)

    def _handle_low_res_sweep(self) -> None:
        """Handle low resolution sweep."""
        self.logger.info('Starting low resolution sweep')
        self.send_command(GPIBCommands.RBW.value.format(DefaultValues.DEFAULT_RBW_LOW_RES))
        
        if self.single_sweep(SweepTimings.RBW_100_HZ.value):
            self.message_queue.put(True)
        else:
            self.message_queue.put(False)
            
        self.send_command(GPIBCommands.RBW.value.format(DefaultValues.DEFAULT_RBW_NORMAL))

    def _handle_sweeping_range_of_amplitudes(self) -> None:
        """Handle sweeping through a range of amplitudes."""
        params = self.command_queue.get()
        start_amp = params["start"]
        stop_amp = params["stop"]
        step_amp = params["step"]
        save_dir = params["dir"]
        resolution = params["resolution"]

        sleep_duration = (SweepTimings.RBW_10_HZ.value if resolution == 10 
                         else SweepTimings.RBW_100_HZ.value)

        self.logger.info(f"Starting amplitude sweep from {start_amp} to {stop_amp} dBm "
                        f"with {resolution} Hz resolution.")
        self.send_command(GPIBCommands.RBW.value.format(resolution))

        # Perform amplitude sweep
        for amp in np.arange(start_amp, stop_amp + 1e-9, step_amp):
            if not self._perform_amplitude_sweep_step(amp, sleep_duration, save_dir):
                return

        self.logger.info("Amplitude sweep finished successfully.")
        self.message_queue.put(True)

    def _perform_amplitude_sweep_step(self, amp: float, sleep_duration: int, save_dir: str) -> bool:
        """
        Perform a single step in the amplitude sweep.
        
        Args:
            amp: Amplitude value in dBm
            sleep_duration: Time to wait for sweep completion
            save_dir: Directory to save data files
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Setting amplitude to {amp} dBm.")
        self.send_command(GPIBCommands.OSCILLATOR_1.value.format(amp))
        
        # Perform sweep
        self.send_command(GPIBCommands.SWEEP_MODE_SINGLE.value)
        self.send_command(GPIBCommands.SWEEP_TRIGGER.value)
        time.sleep(sleep_duration)

        # Acquire data
        if not (self.acquire_mag_data() and self.acquire_phase_data() and self.acquire_freq_data()):
            self.logger.error(f"Data acquisition failed at amplitude {amp} dBm.")
            self.message_queue.put(False)
            return False

        # Send data to GUI
        self.data_queue.put(self.freq_data)
        self.data_queue.put(self.mag_data)
        self.data_queue.put(amp)

        # Save to file
        if not self._save_amplitude_sweep_data(amp, save_dir):
            return False

        self._clear_data()
        return True

    def _save_amplitude_sweep_data(self, amp: float, save_dir: str) -> bool:
        """
        Save amplitude sweep data to CSV file.
        
        Args:
            amp: Amplitude value in dBm
            save_dir: Directory to save the file
            
        Returns:
            True if successful, False otherwise
        """
        file_name = os.path.join(save_dir, f"amplitude_sweep_{amp}dBm.csv")
        self.logger.info(f"Saving data to {file_name}")
        
        try:
            with open(file_name, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Frequency', 'Magnitude', 'Phase'])
                rows = zip(self.freq_data, self.mag_data, self.phase_data)
                writer.writerows(rows)
            return True
        except IOError as e:
            self.logger.error(f"Could not write to file {file_name}: {e}")
            self.message_queue.put(False)
            return False

    def _validate_data_consistency(self) -> bool:
        """
        Validate that all data arrays have the same length.
        
        Returns:
            True if data is consistent, False otherwise
        """
        return (len(self.mag_data) == len(self.freq_data) and 
                len(self.phase_data) == len(self.freq_data))

    def _send_data_to_queue(self) -> None:
        """Send measurement data to the data queue."""
        self.data_queue.put(self.mag_data)
        self.data_queue.put(self.phase_data)
        self.data_queue.put(self.freq_data)

    def _clear_data(self) -> None:
        """Clear all measurement data arrays."""
        self.mag_data = []
        self.phase_data = []
        self.freq_data = []

    # =========================================================================
    # PROCESS ENTRY POINT AND MAIN LOOP
    # =========================================================================
    # The run() method below is the entry point when this class is started
    # as a separate process. It sets up logging and continuously listens for
    # commands from the GUI, dispatching them to the command handlers above.

    def run(self) -> None:
        """
        Main process loop. Runs when the class is launched as a separate process.
        Sets up logging and processes commands from the command queue.
        """
        # Set up logging for this process
        self.qh = logging.handlers.QueueHandler(self.logging_queue)
        self.root = logging.getLogger()
        self.root.setLevel(logging.DEBUG)
        self.root.addHandler(self.qh)
        self.logger = logging.getLogger(__name__)

        # Main command processing loop
        while True:
            try:
                command = self.command_queue.get()
                self.handle_command(command)
            except Exception as e:
                self.logger.error(f"Error processing command: {e}")
                self.message_queue.put(False)

    # =========================================================================
    # LOW-LEVEL INSTRUMENT COMMUNICATION LAYER
    # =========================================================================
    # The methods below handle direct VISA/GPIB communication with the HP4195A
    # instrument. They are called by the command handlers above to perform
    # low-level operations like connecting, sending commands, and acquiring data.
    # This separation keeps instrument-specific details separate from business logic.

    def visa_connect(self) -> None:
        """
        Establish VISA connection to the HP4195A instrument.
        """
        self.logger.info('Starting VISA communications')
        try:
            self.rm = pyvisa.ResourceManager()
            self.instrument = self.rm.open_resource(self.visa_resource_name)
            self.instrument.timeout = DefaultValues.VISA_TIMEOUT

            identity_full = self.instrument.query(GPIBCommands.QUERY_IDENTITY.value)
            identity_clean = identity_full.splitlines()[0]
            
            self.logger.info(f"Connected to: {identity_clean}")
            if self.device_id in identity_clean:
                self.logger.info(f'Successfully found {self.device_id}')
                self.message_queue.put(True)
            else:
                self.logger.warning(f'Device ID mismatch. Expected {self.device_id}, got {identity_clean}')
                self.instrument.close()
                self.message_queue.put(False)
                
        except pyvisa.errors.VisaIOError as e:
            self.logger.error(f"VISA Error: {e}")
            self.message_queue.put(False)

    def visa_disconnect(self) -> None:
        """
        Disconnect from the HP4195A instrument.
        """
        self.logger.info('Disconnecting VISA connection')
        if self.instrument:
            self.instrument.close()
            self.instrument = None
        if self.rm:
            self.rm.close()
            self.rm = None
        self.message_queue.put(True)

    def acquire_mag_data(self) -> bool:
        """
        Acquire magnitude data from the instrument.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            raw_mag_data = self.send_query(GPIBCommands.QUERY_MAGNITUDE.value)
            mag_data = np.fromstring(raw_mag_data, dtype=float, sep=',')
            if len(mag_data) > 0:
                self.mag_data = mag_data.tolist()
                return True
            return False
        except (ValueError, AttributeError) as e:
            self.logger.error(f"Error acquiring magnitude data: {e}")
            return False

    def acquire_phase_data(self) -> bool:
        """
        Acquire phase data from the instrument.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            raw_phase_data = self.send_query(GPIBCommands.QUERY_PHASE.value)
            phase_data = np.fromstring(raw_phase_data, dtype=float, sep=',')
            if len(phase_data) > 0:
                self.phase_data = phase_data.tolist()
                return True
            return False
        except (ValueError, AttributeError) as e:
            self.logger.error(f"Error acquiring phase data: {e}")
            return False

    def acquire_freq_data(self) -> bool:
        """
        Acquire frequency data from the instrument.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            raw_freq_data = self.send_query(GPIBCommands.QUERY_FREQUENCY.value)
            freq_data = np.fromstring(raw_freq_data, dtype=float, sep=',')
            if len(freq_data) > 0:
                self.freq_data = freq_data.tolist()
                return True
            return False
        except (ValueError, AttributeError) as e:
            self.logger.error(f"Error acquiring frequency data: {e}")
            return False

    def acquire_all_data(self) -> bool:
        """
        Acquire magnitude, phase, and frequency data and validate consistency.
        
        Returns:
            True if all data acquired successfully and is consistent, False otherwise
        """
        if not (self.acquire_mag_data() and self.acquire_phase_data() and self.acquire_freq_data()):
            self.logger.error('Failed to acquire all data types.')
            return False
            
        if not self._validate_data_consistency():
            self.logger.warning('Data length check failed.')
            return False
            
        self.logger.info('Data acquisition and validation successful.')
        self._send_data_to_queue()
        return True

    def send_command(self, command: str) -> None:
        """
        Send a command to the instrument without expecting a response.
        
        Args:
            command: GPIB command string to send
        """
        self.logger.info(f'Sent "{command}"')
        if self.instrument:
            try:
                self.instrument.write(command)
            except pyvisa.errors.VisaIOError as e:
                self.logger.error(f"VISA Write Error: {e}")
        else:
            self.logger.warning("Cannot send command: not connected to instrument")

    def send_query(self, command: str) -> str:
        """
        Send a query command to the instrument and return the response.
        
        Args:
            command: GPIB query command string to send
            
        Returns:
            Response string from the instrument
        """
        self.logger.info(f'Querying "{command}"')
        if self.instrument:
            try:
                response = self.instrument.query(command)
                self.logger.info(f'Received {len(response)} characters of {type(response)}')
                return response.strip()
            except pyvisa.errors.VisaIOError as e:
                self.logger.error(f"VISA Query Error: {e}")
                return "Query failed"
        else:
            self.logger.warning("Cannot send query: not connected to instrument")
            return "Not connected"
    
    def single_sweep(self, sleep_duration: int) -> bool:
        """
        Perform a single sweep and acquire all data.
        
        Args:
            sleep_duration: Time to wait for sweep completion in seconds
            
        Returns:
            True if sweep and data acquisition successful, False otherwise
        """
        self.logger.info('Starting single sweep')

        self.send_command(GPIBCommands.SWEEP_MODE_SINGLE.value)
        self.send_command(GPIBCommands.SWEEP_TRIGGER.value)

        time.sleep(sleep_duration)

        self.logger.info('Sweep complete. Acquiring data.')
        return self.acquire_all_data()
