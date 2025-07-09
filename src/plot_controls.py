import numpy as np
from scipy.optimize import curve_fit

class PlotControls:
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