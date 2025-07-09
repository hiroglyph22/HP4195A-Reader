from PyQt5 import QtWidgets
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import FuncFormatter
from queue import Empty

class PlotCanvas(FigureCanvas):
    '''
    This class is for the figure that displays the data. It reads data
    from the data queue and updates the graph depending on the settings.
    '''
    def __init__(self, parent=None, data_queue=None, width=5, height=4, dpi=100):
        self.data_queue = data_queue
        self.persist = False
        self.magnitude = True
        self.phase = True

        self.peak_freq = None
        self.peak_mag = None

        self.q_factor = None
        self.fit_freq = None
        self.fit_data = None

        self.freq_data = range(1, 100)
        self.mag_data = [0 for i in range(1, 100)]
        self.phase_data = [0 for i in range(1, 100)]

        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='black')
        self.mag_ax = self.fig.add_subplot(111)
        self.mag_ax.set_facecolor('black')
        self.phase_ax = self.mag_ax.twinx()

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()

    def mark_peak(self, freq, mag):
        '''Saves the coordinates of the peak to be marked on the plot.'''
        self.peak_freq = freq
        self.peak_mag = mag

    def set_q_factor_data(self, fit_freq, fit_data, q_factor):
        '''Saves the fitted curve data and Q-Factor to be plotted.'''
        self.fit_freq = fit_freq
        self.fit_data = fit_data
        self.q_factor = q_factor

    def clear_q_factor_data(self):
        '''Clears the Q-Factor data before a new acquisition.'''
        self.q_factor = None
        self.fit_freq = None
        self.fit_data = None

    def plot(self):
        if not self.persist:
            self.mag_ax.clear()
            self.phase_ax.clear()

        try:
            # Try to get data without blocking
            self.mag_data = self.data_queue.get_nowait()
            self.phase_data = self.data_queue.get_nowait()
            self.freq_data = self.data_queue.get_nowait()
        except Empty:
            # If the queue is empty, just redraw the existing data
            pass

        # --- Style Configuration ---
        self.mag_ax.set_xlabel('Frequency (Hz)', color='white')
        self.mag_ax.set_ylabel('Magnitude (dBm)', color='yellow')
        self.phase_ax.set_ylabel('Phase (deg)', color='cyan')
        self.phase_ax.yaxis.set_label_position('right')

        if len(self.mag_data) > 1 and len(self.phase_data) > 1:
            self.phase_ax.set_ylim(np.min(self.phase_data)-20, np.max(self.phase_data)+20)
            self.mag_ax.set_ylim(np.min(self.mag_data)-20, np.max(self.mag_data)+20)
        
        if len(self.freq_data) > 1:
            self.phase_ax.set_xlim(np.min(self.freq_data), np.max(self.freq_data))
            self.mag_ax.set_xlim(np.min(self.freq_data), np.max(self.freq_data))

        self.mag_ax.tick_params(axis='x', colors='white')
        self.mag_ax.tick_params(axis='y', colors='yellow')
        self.phase_ax.tick_params(axis='y', colors='cyan')

        for spine in self.mag_ax.spines.values():
            spine.set_edgecolor('white')
        self.phase_ax.spines['right'].set_edgecolor('cyan')
        self.mag_ax.spines['left'].set_edgecolor('yellow')

        self.mag_ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x/1e3:.0f} KHz'))
        self.mag_ax.yaxis.set_major_formatter(FuncFormatter(lambda y, pos: f'{y:.0f} dBm'))
        self.phase_ax.yaxis.set_major_formatter(FuncFormatter(lambda y, pos: f'{y:.0f} °'))

        # --- Plotting ---
        if self.magnitude:
            self.mag_ax.plot(self.freq_data, self.mag_data, color='yellow', linewidth=1.5, label='Magnitude')

        if self.phase:
            self.phase_ax.plot(self.freq_data, self.phase_data, color='cyan', linewidth=1.5, label='Phase')
        
        if self.peak_freq is not None and self.peak_mag is not None:
            self.mag_ax.annotate(f'Peak\n{self.peak_mag:.2f} dBm',
                xy=(self.peak_freq, self.peak_mag),
                xytext=(self.peak_freq, self.peak_mag + 15), color='red',
                fontsize=10, ha='center',
                arrowprops=dict(facecolor='red', shrink=0.05, width=2, headwidth=8))

        if self.q_factor is not None:
            self.mag_ax.plot(self.fit_freq, self.fit_data, 'r--', linewidth=2, label=f'Lorentzian Fit')
            self.mag_ax.text(0.02, 0.95, f'Q-Factor: {self.q_factor:.2f}',
                             transform=self.mag_ax.transAxes, fontsize=14,
                             verticalalignment='top',
                             bbox=dict(boxstyle='round', facecolor='black', alpha=0.5), color='white')

        self.mag_ax.grid(color='gray', linestyle='-', linewidth=0.5)

        if self.magnitude or self.q_factor is not None:
             self.mag_ax.legend(loc='lower left')
        if self.phase:
             self.phase_ax.legend(loc='lower right')

        self.fig.tight_layout()
        self.draw()