from PyQt5 import QtWidgets

class InstrumentControls:
    def connect(self):
        if self.connected:
            self.command_queue.put('disconnect')
            if self.message_queue.get():
                self.connected = False
                self.connect_button.setText("Connect")
                self.acquire_button.setEnabled(False)
                self.peak_scan_button.setEnabled(False) 
                self.low_res_sweep_button.setEnabled(False)
                self.range_scan_button.setEnabled(False)
                self.sweeping_range_of_amplitudes_button.setEnabled(False)
        else:
            self.command_queue.put('connect')
            if self.message_queue.get():
                self.connected = True
                self.connect_button.setText("Disconnect")
                self.acquire_button.setEnabled(True)
                self.peak_scan_button.setEnabled(True) 
                self.low_res_sweep_button.setEnabled(True)
                self.range_scan_button.setEnabled(True)
                self.sweeping_range_of_amplitudes_button.setEnabled(True)
                self.timer.start()

    def start_acquisition(self):
        if self.connected:
            self.command_queue.put('start_acquisition')
            if self.message_queue.get():
                self.autofind_peak_button.setEnabled(True)
                self.center_peak_button.setEnabled(False)
                self.q_factor_button.setEnabled(False)
                self.graph.clear_q_factor_data()
                self.graph.peak_freq = None
                self.graph.peak_mag = None
                self.graph.plot()

    def send_command(self):
        command = self.command_box.text()
        self.command_queue.put('send_command')
        self.command_queue.put(command)
        response = self.data_queue.get()
        self.response_box.setText(f'{command}: {response}')
        self.command_box.clear()

    def center_on_peak(self):
        if self.graph.peak_freq is not None:
            self.command_queue.put('set_center_frequency')
            self.command_queue.put(self.graph.peak_freq)
            self.start_acquisition()

    def start_peak_scan(self):
        try:
            center_freq = float(self.peak_freq_input.text())
            span_freq = float(self.span_input.text())
            self.command_queue.put('set_center_and_span')
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
            self.command_queue.put('set_start_stop')
            self.command_queue.put(start_freq)
            self.command_queue.put(stop_freq)
            if self.message_queue.get():
                self.start_acquisition()
        except ValueError:
            self.show_error_dialog("Invalid Input", "Please enter valid numbers for start and stop frequencies.")

    def start_low_res_sweep(self):
        self.command_queue.put('low_res_sweep')
        if self.message_queue.get():
            self.start_acquisition()

    def start_sweeping_range_of_amplitudes(self):
        try:
            start_p = float(self.start_amplitude_input.text())
            stop_p = float(self.stop_amplitude_input.text())
            step_p = float(self.step_amplitude_input.text())

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
                        
            self.sweeping_range_of_amplitudes_button.setEnabled(False)

            self.command_queue.put('sweeping_range_of_amplitudes')
            self.command_queue.put({
                "start": start_p,
                "stop": stop_p,
                "step": step_p,
                "dir": save_dir
            })
            
            if self.message_queue.get():
                self.logger.info("Sweeping Range of Amplitudes completed successfully.")
                QtWidgets.QMessageBox.information(self, "Sweeps Complete", "Sweeping Range of Amplitudes finished and all files have been saved.")
            else:
                self.logger.error("Sweeping Range of Amplitudes failed or were interrupted in the backend.")
            
            self.sweeping_range_of_amplitudes_button.setEnabled(True)

        except ValueError:
            self.show_error_dialog("Invalid Input", "Please enter valid numbers for the Sweeping Range of Amplitudes parameters.")