from PyQt5 import QtWidgets, QtCore
try:
    # Try relative imports first (for when running as a module/package)
    from ..gui.amplitude_sweep_viewer import AmplitudeSweepViewer
    from ..gui.final_sweep_viewer import FinalSweepViewer
    from ..constants import Commands
except ImportError:
    # Fall back to absolute imports (for when running directly)
    from gui.amplitude_sweep_viewer import AmplitudeSweepViewer
    from gui.final_sweep_viewer import FinalSweepViewer
    from constants import Commands
from threading import Thread
from queue import Empty

class SweepCommunicator(QtCore.QObject):
    """
    Manages thread-safe communication between the sweep worker thread
    and the main GUI thread using signals.
    """
    # Signal for creating a new window for a single sweep
    new_sweep_window_ready = QtCore.pyqtSignal(object, object, float) # freq, mag, amp
    # Signal for creating the final, overlaid plot window
    final_plot_ready = QtCore.pyqtSignal(list)
    # Signal to re-enable the sweep button when finished
    enable_button = QtCore.pyqtSignal(bool)

class InstrumentControls:
    # This method is a slot that runs on the GUI thread
    @QtCore.pyqtSlot(object, object, float)
    def create_new_sweep_window(self, freq_data, mag_data, amp):
        """Creates and shows a new, persistent window for a single sweep."""
        if not hasattr(self, 'sweep_viewers'):
            self.sweep_viewers = []
        
        viewer = AmplitudeSweepViewer(parent=self)
        viewer.update_plot(freq_data, mag_data, amp)
        viewer.show()
        # Keep a reference to the window so it's not garbage collected
        self.sweep_viewers.append(viewer)

    # This method is a slot that runs on the GUI thread
    @QtCore.pyqtSlot(list)
    def create_final_sweep_window(self, all_sweeps_data):
        """Creates and shows the final window with all sweeps overlaid."""
        if not hasattr(self, 'sweep_viewers'):
            self.sweep_viewers = []

        final_viewer = FinalSweepViewer(parent=self)
        final_viewer.update_plot(all_sweeps_data)
        final_viewer.show()
        # Keep a reference to the window
        self.sweep_viewers.append(final_viewer)

    def connect(self):
        if self.connected:
            self.command_queue.put(Commands.DISCONNECT.value)
            if self.message_queue.get():
                self.connected = False
                self.connect_button.setText("Connect")
                self.acquire_button.setEnabled(False)
                self.peak_scan_button.setEnabled(False) 
                self.low_res_sweep_button.setEnabled(False)
                self.range_scan_button.setEnabled(False)
                self.sweeping_range_of_amplitudes_button.setEnabled(False)
                self.pause_button.setEnabled(False)
                self.timer.stop()
                self.pause_button.setText('Start Auto-Update')
                self.pause_button.setChecked(False)
        else:
            self.command_queue.put(Commands.CONNECT.value)
            if self.message_queue.get():
                self.connected = True
                self.connect_button.setText("Disconnect")
                self.acquire_button.setEnabled(True)
                self.peak_scan_button.setEnabled(True) 
                self.low_res_sweep_button.setEnabled(True)
                self.range_scan_button.setEnabled(True)
                self.sweeping_range_of_amplitudes_button.setEnabled(True)
                self.pause_button.setEnabled(True)

    def start_acquisition(self):
        if self.connected:
            self.command_queue.put(Commands.START_ACQUISITION.value)
            if self.message_queue.get():
                self.autofind_peak_button.setEnabled(True)
                self.center_peak_button.setEnabled(False)
                self.q_factor_button.setEnabled(False)
                self.graph.clear_q_factor_data()
                self.graph.peak_freq = None
                self.graph.peak_mag = None
                self.graph.plot(force_refresh=True)

    def send_command(self):
        command = self.command_box.text()
        self.command_queue.put(Commands.SEND_COMMAND.value)
        self.command_queue.put(command)
        response = self.data_queue.get()
        self.response_box.setText(f'{command}: {response}')
        self.command_box.clear()

    def apply_machine_settings(self, settings):
        """Send a command to apply a dictionary of settings to the instrument."""
        if self.connected:
            self.command_queue.put(Commands.APPLY_MACHINE_SETTINGS.value)
            self.command_queue.put(settings)
            if self.message_queue.get(timeout=10):
                self.show_info_dialog("Settings Applied", "Machine settings have been successfully applied.")
            else:
                self.show_error_dialog("Application Failed", "Failed to apply settings to the instrument.")
        else:
            self.show_error_dialog("Not Connected", "Cannot apply settings, not connected to the instrument.")

    def center_on_peak(self):
        if self.graph.peak_freq is not None:
            self.command_queue.put(Commands.SET_CENTER_FREQUENCY.value)
            self.command_queue.put(self.graph.peak_freq)
            self.start_acquisition()

    def start_peak_scan(self):
        try:
            center_freq = float(self.peak_freq_input.text())
            span_freq = float(self.span_input.text())
            self.command_queue.put(Commands.SET_CENTER_AND_SPAN.value)
            self.command_queue.put(center_freq)
            self.command_queue.put(span_freq)
            if self.message_queue.get():
                self.start_acquisition()
        except ValueError:
            self.show_error_dialog("Invalid Input", "Please enter a valid number for frequency and span.")

    def start_range_scan(self):
        try:
            start_freq = float(self.start_freq_input.text())
            stop_freq = float(self.stop_freq_input.text())
            if start_freq >= stop_freq:
                self.show_error_dialog("Invalid Range", "Start frequency must be less than stop frequency.")
                return
            self.command_queue.put(Commands.SET_START_STOP.value)
            self.command_queue.put(start_freq)
            self.command_queue.put(stop_freq)
            if self.message_queue.get():
                self.start_acquisition()
        except ValueError:
            self.show_error_dialog("Invalid Input", "Please enter valid numbers for start and stop frequencies.")

    def start_low_res_sweep(self):
        self.command_queue.put(Commands.LOW_RES_SWEEP.value)
        if self.message_queue.get():
            self.start_acquisition()

    def start_sweeping_range_of_amplitudes(self):
        try:
            start_p = float(self.start_amplitude_input.text())
            stop_p = float(self.stop_amplitude_input.text())
            step_p = float(self.step_amplitude_input.text())
            resolution = int(self.resolution_combo.currentText())

            if step_p <= 0:
                self.show_error_dialog("Invalid Step", "Amplitude step must be a positive number.")
                return
            if start_p > stop_p:
                self.show_error_dialog("Invalid Range", "Start amplitude cannot be greater than stop amplitude.")
                return
            
            save_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory to Save Sweeping Range of Amplitudes Data")
            if not save_dir:
                self.logger.info("Sweeping Range of Amplitudes cancelled by user.")
                return
            
            # Clear any old sweep windows before starting a new run
            if hasattr(self, 'sweep_viewers'):
                for viewer in self.sweep_viewers:
                    viewer.close()
                self.sweep_viewers.clear()
            else:
                self.sweep_viewers = []
                        
            self.sweeping_range_of_amplitudes_button.setEnabled(False)
            
            communicator = SweepCommunicator()

            # Connect signals to the new slots, which will run on the GUI thread
            communicator.new_sweep_window_ready.connect(self.create_new_sweep_window)
            communicator.final_plot_ready.connect(self.create_final_sweep_window)
            communicator.enable_button.connect(self.sweeping_range_of_amplitudes_button.setEnabled)

            def sweep_thread_func():
                self.command_queue.put(Commands.SWEEPING_RANGE_OF_AMPLITUDES.value)
                self.command_queue.put({
                    "start": start_p,
                    "stop": stop_p,
                    "step": step_p,
                    "dir": save_dir,
                    "resolution": resolution
                })
                
                all_sweeps_data = []
                num_sweeps = int((stop_p - start_p) / step_p) + 1
                for i in range(num_sweeps):
                    try:
                        # Get all three data points from the backend
                        freq_data = self.data_queue.get(timeout=300)
                        mag_data = self.data_queue.get(timeout=10)
                        amp = self.data_queue.get(timeout=10)

                        all_sweeps_data.append((freq_data, mag_data, amp))
                        # Emit signal to create a new window for this sweep
                        communicator.new_sweep_window_ready.emit(freq_data, mag_data, amp)

                    except Empty:
                        self.logger.error("Timeout waiting for sweep data from backend.")
                        break

                if self.message_queue.get():
                    self.logger.info("Sweeping Range of Amplitudes completed successfully.")
                    # Emit signal to create the final plot if data was collected
                    if all_sweeps_data:
                        communicator.final_plot_ready.emit(all_sweeps_data)
                else:
                    self.logger.error("Sweeping Range of Amplitudes failed or were interrupted in the backend.")
                
                communicator.enable_button.emit(True)

            thread = Thread(target=sweep_thread_func)
            thread.daemon = True
            thread.start()

        except ValueError:
            self.show_error_dialog("Invalid Input", "Please enter valid numbers for the Sweeping Range of Amplitudes parameters.")