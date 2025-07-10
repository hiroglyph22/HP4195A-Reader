from PyQt5 import QtWidgets, QtCore
from gui.plot_canvas import PlotCanvas

class AmplitudeSweepViewer(QtWidgets.QDialog):
    # Signal to update the plot with new data
    sweep_data_ready = QtCore.pyqtSignal(object, object)

    def __init__(self, parent=None, data_queue=None):
        super(AmplitudeSweepViewer, self).__init__(parent)
        self.setWindowTitle("Amplitude Sweep Viewer")
        self.setMinimumSize(800, 600)
        
        self.all_sweeps_data = []

        # Main layout
        layout = QtWidgets.QVBoxLayout(self)

        # Create plot canvas without auto-plotting
        self.plot_canvas = PlotCanvas(self, data_queue=data_queue, auto_plot=False)
        layout.addWidget(self.plot_canvas)

        # Button box
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        
        # Connect the signal to the slot
        self.sweep_data_ready.connect(self.update_sweep)

    @QtCore.pyqtSlot(object, object)
    def update_sweep(self, freq_data, mag_data):
        """Displays a single, most recent sweep."""
        self.plot_canvas.update_sweep_plot(freq_data, mag_data)
        self.all_sweeps_data.append((freq_data, mag_data))

    def show_final_plot(self):
        """Overlays all collected sweeps on the plot."""
        self.setWindowTitle("Final Overlaid Sweeps")
        self.plot_canvas.update_overlaid_plot(self.all_sweeps_data)
        self.exec_()