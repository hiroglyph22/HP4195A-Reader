from PyQt5 import QtWidgets, QtCore
from .plot_canvas import PlotCanvas

class AmplitudeSweepViewer(QtWidgets.QDialog):
    """
    A simple dialog to display a single sweep from the amplitude sweep process.
    A new instance of this class is created for each sweep.
    """
    def __init__(self, parent=None):
        super(AmplitudeSweepViewer, self).__init__(parent)
        self.setMinimumSize(800, 600)
        
        layout = QtWidgets.QVBoxLayout(self)
        self.plot_canvas = PlotCanvas(self, auto_plot=False)
        layout.addWidget(self.plot_canvas)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def update_plot(self, freq_data, mag_data, amp):
        """
        Displays a single sweep and sets the window title to match the
        amplitude.
        """
        self.setWindowTitle(f"Sweep at {amp:.2f} dBm")
        self.plot_canvas.update_sweep_plot(freq_data, mag_data)