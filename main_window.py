import csv
import logging
import logging.handlers
import numpy as np
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon
from scipy.optimize import curve_fit

# Local imports for refactored components
from ui_generator import UIGenerator
from plot_canvas import PlotCanvas
from help_window import Help_Window

class MainWindow(QtWidgets.QMainWindow, UIGenerator):
    '''
    This class is for the main GUI window. It handles events and
    application logic, putting messages in a command queue for the
    backend process. UI generation is handled by the UIGenerator mixin.
    '''
    def __init__(self, command_queue, message_queue, data_queue, logging_queue):
        super(MainWindow, self).__init__()

        self.command_queue = command_queue
        self.message_queue = message_queue
        self.data_queue = data_queue
        self.logging_queue = logging_queue

        self.title = 'HP4195A'
        self.width = 1920
        self.height = 1120 # <-- MODIFIED: Increased height
        
        self.qh = logging.handlers.QueueHandler(self.logging_queue)
        self.root = logging.getLogger()
        self.root.setLevel(logging.DEBUG)
        self.root.addHandler(self.qh)
        self.logger = logging.getLogger(__name__)

        self.connected = False
        self.initUI()
    
    # ... (rest of main_window.py is unchanged) ...
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setFixedSize(self.width, self.height)
        self.setWindowIcon(QIcon('icon.png'))

        self.graph = PlotCanvas(self, data_queue=self.data_queue, width=17, height=8.5)
        self.graph.move(0,20)

        # Call all the UI generation methods from the UIGenerator mixin
        self.generate_menu_bar()
        self.generate_connection_button()
        self.generate_acquire_button()
        self.generate_save_button()
        self.generate_autofind_peak_button()
        self.generate_pause_button()
        self.generate_center_on_peak_button()
        self.generate_q_factor_button()
        self.generate_persistance_checkbox()
        self.generate_mag_enable_checkbox()
        self.generate_phase_enable_checkbox()
        self.generate_peak_scan_section()
        self.generate_low_res_sweep_button() 
        self.generate_range_scan_section()
        self.generate_command_box()
        self.generate_command_button()
        self.generate_response_box()
        self.generate_power_control_section()

        # Set initial button states
        self.acquire_button.setEnabled(False)
        self.autofind_peak_button.setEnabled(False)
        self.center_peak_button.setEnabled(False)
        self.q_factor_button.setEnabled(False)
        self.peak_scan_button.setEnabled(False)
        self.low_res_sweep_button.setEnabled(False)
        self.range_scan_button.setEnabled(False)
        self.command_button.setEnabled(False)
        self.power_sweep_button.setEnabled(False)
        
        self.show()

        self.timer = QtCore.QTimer()
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.start_acquisition)

    # --- APPLICATION LOGIC AND EVENT HANDLERS --- #

    def change_persist_state(self):
        self.graph.persist = self.p_cb.isChecked()
        self.mag_cb.setEnabled(not self.graph.persist)
        self.phase_cb.setEnabled(not self.graph.persist)
        state = "Enabled" if self.graph.persist else "Disabled"
        self.logger.info(f'Persistence: {state}')

    def change_mag_state(self):
        self.graph.magnitude = self.mag_cb.isChecked()
        self.graph.plot()
        state = "Enabled" if self.graph.magnitude else "Disabled"
        self.logger.info(f'Magnitude: {state}')

    def change_phase_state(self):
        self.graph.phase = self.phase_cb.isChecked()
        self.graph.plot()
        state = "Enabled" if self.graph.phase else "Disabled"
        self.logger.info(f'Phase: {state}')

    def toggle_connect_button(self):
        self.command_button.setEnabled(len(self.command_box.text()) > 0 and self.connected)

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
                self.power_sweep_button.setEnabled(False)
        else:
            self.command_queue.put('connect')
            if self.message_queue.get():
                self.connected = True
                self.connect_button.setText("Disconnect")
                self.acquire_button.setEnabled(True)
                self.peak_scan_button.setEnabled(True) 
                self.low_res_sweep_button.setEnabled(True)
                self.range_scan_button.setEnabled(True)
                self.power_sweep_button.setEnabled(True)
                self.timer.start()

    def start_acquisition(self):
        self.command_queue.put('start_acquisition')
        if self.message_queue.get():
            self.autofind_peak_button.setEnabled(True)
            self.center_peak_button.setEnabled(False)
            self.q_factor_button.setEnabled(False)
            self.graph.clear_q_factor_data()
            self.graph.peak_freq = None
            self.graph.peak_mag = None
            self.graph.plot()

    def autofind_peak(self):
        if not hasattr(self.graph, 'mag_data') or len(self.graph.mag_data) == 0:
            return
        try:
            mag_data_np = np.array(self.graph.mag_data)
            peak_index = np.argmax(mag_data_np)
            peak_mag = mag_data_np[peak_index]
            peak_freq = self.graph.freq_data[peak_index]
            self.graph.mark_peak(peak_freq, peak_mag)
            self.center_peak_button.setEnabled(True)
            self.q_factor_button.setEnabled(True) 
            self.graph.plot()
        except (ValueError, IndexError) as e:
            self.logger.error(f'Could not find peak. Error: {e}')

    def send_command(self):
        command = self.command_box.text()
        self.command_queue.put('send_command')
        self.command_queue.put(command)
        response = self.data_queue.get()
        self.response_box.setText(f'{command}: {response}')
        self.command_box.clear()

    def save_file_dialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            if not file_name.endswith('.csv'):
                file_name += '.csv'
            self.save_file(file_name)

    def save_file(self, file_name):
        self.logger.info(f'Saving data to: {file_name}')
        rows = zip(self.graph.freq_data, self.graph.mag_data, self.graph.phase_data)
        with open(file_name, "w", newline='') as output:
            writer = csv.writer(output)
            writer.writerow(['Frequency', 'Magnitude', 'Phase'])
            writer.writerows(rows)

    def help_dialog(self):
        # The Help_Window is modal, so it blocks other input
        help_window = Help_Window()
        help_window.exec_()

    def closeEvent(self, event):
        if self.connected:
            self.connect()
        self.logging_queue.put(None)
        event.accept()

    def toggle_pause(self, paused):
        if paused:
            self.timer.stop()
            self.pause_button.setText('Resume')
        else:
            self.timer.start()
            self.pause_button.setText('Pause')

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

    def calculate_q_factor(self):
        if self.graph.peak_freq is None:
            return

        def _lorentzian(x, amp, cen, fwhm):
            return amp * (fwhm/2)**2 / ((x - cen)**2 + (fwhm/2)**2)

        x_data = np.array(self.graph.freq_data)
        y_data_dbm = np.array(self.graph.mag_data)
        y_data_linear = 10**(y_data_dbm / 10)
        
        peak_freq = self.graph.peak_freq
        peak_mag_linear = 10**(self.graph.peak_mag / 10)
        initial_fwhm = (np.max(x_data) - np.min(x_data)) / 10
        p0 = [peak_mag_linear, peak_freq, initial_fwhm]
        
        try:
            popt, _ = curve_fit(_lorentzian, x_data, y_data_linear, p0=p0, maxfev=5000)
            fit_amp, fit_center_freq, fit_fwhm = popt
            q_factor = abs(fit_center_freq / fit_fwhm)
            
            fit_freq_range = np.linspace(x_data.min(), x_data.max(), 400)
            fit_data_linear = _lorentzian(fit_freq_range, *popt)
            fit_data_dbm = 10 * np.log10(fit_data_linear)
            
            self.graph.set_q_factor_data(fit_freq_range, fit_data_dbm, q_factor)
            self.graph.plot()

        except (RuntimeError, ValueError) as e:
            self.show_error_dialog("Fit Failed", "Could not calculate Q-Factor. The data may not resemble a resonance peak.")
            
    def start_power_sweep(self):
        try:
            start_p = float(self.start_power_input.text())
            stop_p = float(self.stop_power_input.text())
            step_p = float(self.step_power_input.text())

            if step_p <= 0:
                self.show_error_dialog("Invalid Step", "Power step must be a positive number.")
                return
            if start_p > stop_p:
                self.show_error_dialog("Invalid Range", "Start power cannot be greater than stop power.")
                return
            
            save_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory to Save Power Sweep Data")
            if not save_dir:
                self.logger.info("Power sweep cancelled by user.")
                return
            
            self.logger.info(f"Starting power sweep from {start_p} to {stop_p} dBm, saving to {save_dir}")
            
            self.power_sweep_button.setEnabled(False)

            self.command_queue.put('start_power_sweep')
            self.command_queue.put({
                "start": start_p,
                "stop": stop_p,
                "step": step_p,
                "dir": save_dir
            })
            
            if self.message_queue.get():
                self.logger.info("Power sweep completed successfully.")
                QtWidgets.QMessageBox.information(self, "Sweep Complete", "Power sweep finished and all files have been saved.")
            else:
                self.logger.error("Power sweep failed or was interrupted in the backend.")
            
            self.power_sweep_button.setEnabled(True)

        except ValueError:
            self.show_error_dialog("Invalid Input", "Please enter valid numbers for power sweep parameters.")


    def show_error_dialog(self, title, text):
        error_dialog = QtWidgets.QMessageBox()
        error_dialog.setIcon(QtWidgets.QMessageBox.Warning)
        error_dialog.setText(title)
        error_dialog.setInformativeText(text)
        error_dialog.setWindowTitle("Error")
        error_dialog.exec_()