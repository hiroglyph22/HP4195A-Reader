from PyQt5 import QtWidgets, QtCore
from .plot_canvas import PlotCanvas

class FinalSweepViewer(QtWidgets.QDialog):
    """
    A dedicated dialog to display the final plot with all amplitude
    sweeps overlaid on a single canvas.
    """
    def __init__(self, parent=None):
        super(FinalSweepViewer, self).__init__(parent)
        self.setWindowTitle("Final Overlaid Sweeps")
        self.setMinimumSize(800, 600)
        
        layout = QtWidgets.QVBoxLayout(self)
        self.plot_canvas = PlotCanvas(self, auto_plot=False)
        layout.addWidget(self.plot_canvas)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def update_plot(self, all_sweeps_data):
        """
        Renders all collected sweeps on the plot canvas.
        
        Args:
            all_sweeps_data (list): A list of tuples, where each tuple
                                    contains (freq_data, mag_data, amplitude).
        """
        self.plot_canvas.update_overlaid_plot(all_sweeps_data)