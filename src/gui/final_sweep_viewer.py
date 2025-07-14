from PyQt5 import QtWidgets, QtCore
from .plot_canvas import PlotCanvas

class FinalSweepViewer(QtWidgets.QDialog):
    """
    A dedicated dialog to display the final plot with all amplitude
    sweeps overlaid on a single canvas, with functionality to select
    which sweeps to display.
    """
    def __init__(self, parent=None):
        super(FinalSweepViewer, self).__init__(parent)
        self.setWindowTitle("Final Overlaid Sweeps")
        self.setMinimumSize(800, 600)
        
        # Store all sweep data
        self.all_sweeps_data = []

        # Main layout
        main_layout = QtWidgets.QHBoxLayout(self)
        
        # Plotting area
        plot_layout = QtWidgets.QVBoxLayout()
        self.plot_canvas = PlotCanvas(self, auto_plot=False)
        plot_layout.addWidget(self.plot_canvas)

        # Dialog buttons
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        plot_layout.addWidget(button_box)

        # Selection area
        selection_layout = QtWidgets.QVBoxLayout()
        selection_layout.addWidget(QtWidgets.QLabel("Select Amplitudes (dBm):"))
        
        self.amplitude_list = QtWidgets.QListWidget()
        # Allow multiple selections
        self.amplitude_list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.amplitude_list.itemSelectionChanged.connect(self.replot_selected_sweeps)
        
        selection_layout.addWidget(self.amplitude_list)

        main_layout.addLayout(plot_layout, 3) # Plot gets more space
        main_layout.addLayout(selection_layout, 1)

    def update_plot(self, all_sweeps_data):
        """
        Renders all collected sweeps on the plot canvas and populates the selection list.
        
        Args:
            all_sweeps_data (list): A list of tuples, where each tuple
                                    contains (freq_data, mag_data, amplitude).
        """
        self.all_sweeps_data = all_sweeps_data
        self.amplitude_list.clear()

        # Populate the list widget with amplitudes
        for _, _, amp in self.all_sweeps_data:
            item = QtWidgets.QListWidgetItem(f"{amp:.2f}")
            item.setData(QtCore.Qt.UserRole, amp)
            self.amplitude_list.addItem(item)
            item.setSelected(True) # Select all by default

        # Initial plot (will be called via itemSelectionChanged when items are selected)
        # self.replot_selected_sweeps()

    def replot_selected_sweeps(self):
        """
        Filters the sweep data based on the selected amplitudes in the list widget
        and updates the plot canvas.
        """
        selected_items = self.amplitude_list.selectedItems()
        selected_amplitudes = {item.data(QtCore.Qt.UserRole) for item in selected_items}
        
        # Filter the data to include only selected amplitudes
        selected_sweeps = [
            sweep for sweep in self.all_sweeps_data 
            if sweep[2] in selected_amplitudes
        ]
        
        self.plot_canvas.update_overlaid_plot(selected_sweeps)