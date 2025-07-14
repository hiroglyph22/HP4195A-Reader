import sys
import os
import csv
import re
from PyQt5 import QtWidgets, QtCore
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import FuncFormatter

class PlotCanvas(FigureCanvas):
    """
    A modified, standalone version of the PlotCanvas for displaying data 
    from CSV files. It handles plotting multiple datasets on the same axes.
    """
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='black')
        self.mag_ax = self.fig.add_subplot(111)
        self.mag_ax.set_facecolor('black')
        
        # A second y-axis isn't needed for just magnitude plots, but we'll
        # create it and hide it to maintain style consistency.
        self.phase_ax = self.mag_ax.twinx()

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
        self.apply_styles()
        self.draw()

    def apply_styles(self):
        """Applies a consistent dark theme to the plot."""
        self.mag_ax.set_xlabel('Frequency (KHz)', color='white')
        self.mag_ax.set_ylabel('Magnitude (dBm)', color='yellow')
        
        # Hide the phase axis elements
        self.phase_ax.get_yaxis().set_visible(False)
        self.phase_ax.spines['right'].set_visible(False)

        self.mag_ax.tick_params(axis='x', colors='white')
        self.mag_ax.tick_params(axis='y', colors='yellow')

        for spine in self.mag_ax.spines.values():
            spine.set_edgecolor('white')
        self.mag_ax.spines['left'].set_edgecolor('yellow')

        self.mag_ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x/1e3:.2f}'))
        self.mag_ax.yaxis.set_major_formatter(FuncFormatter(lambda y, pos: f'{y:.0f}'))
        
        self.mag_ax.grid(color='gray', linestyle='-', linewidth=0.5)
        self.fig.tight_layout()

    def update_overlaid_plot(self, all_sweeps):
        """
        Clears the plot and redraws it with a new set of sweep data.
        
        Args:
            all_sweeps (list): A list of tuples, where each tuple is
                               (freq_data, mag_data, label_string).
        """
        self.mag_ax.clear()
        self.apply_styles()

        if not all_sweeps:
            self.draw()
            return

        min_mag, max_mag = float('inf'), float('-inf')
        min_freq, max_freq = float('inf'), float('-inf')

        # First, find the overall min/max across all selected sweeps
        for freq_data, mag_data, _ in all_sweeps:
            if len(mag_data) > 0:
                min_mag = min(min_mag, np.min(mag_data))
                max_mag = max(max_mag, np.max(mag_data))
            if len(freq_data) > 0:
                min_freq = min(min_freq, np.min(freq_data))
                max_freq = max(max_freq, np.max(freq_data))
        
        # Then, plot each sweep
        for freq_data, mag_data, label in all_sweeps:
            # Find peak frequency for this sweep
            if len(mag_data) > 0:
                peak_idx = np.argmax(mag_data)
                peak_freq = freq_data[peak_idx]
                peak_mag = mag_data[peak_idx]
                # Include peak frequency in the label
                enhanced_label = f"{label} (Peak: {peak_freq/1e3:.2f} kHz)"
            else:
                enhanced_label = label
            
            self.mag_ax.plot(freq_data, mag_data, linewidth=1.5, label=enhanced_label)
        
        # Finally, set the axis limits with a 5% padding
        if min_mag != float('inf') and max_mag != float('-inf'):
            mag_range = max_mag - min_mag
            mag_padding = mag_range * 0.05 if mag_range > 0 else 1
            self.mag_ax.set_ylim(min_mag - mag_padding, max_mag + mag_padding)

        if min_freq != float('inf') and max_freq != float('-inf'):
            freq_range = max_freq - min_freq
            freq_padding = freq_range * 0.05 if freq_range > 0 else 1
            self.mag_ax.set_xlim(min_freq - freq_padding, max_freq + freq_padding)

        self.mag_ax.legend()
        self.fig.tight_layout()
        self.draw()


class CsvPlotterWindow(QtWidgets.QMainWindow):
    """
    Main application window for loading and plotting CSV data.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Overlaid Plotter")
        self.setMinimumSize(1024, 768)

        # Store all loaded data here
        self.loaded_data = []

        # --- Main Layout ---
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)

        # --- Controls (Left Side) ---
        controls_widget = QtWidgets.QWidget()
        controls_layout = QtWidgets.QVBoxLayout(controls_widget)
        controls_widget.setMaximumWidth(300)

        self.load_button = QtWidgets.QPushButton("Load CSV Files")
        self.load_button.clicked.connect(self.load_csv_files)
        
        self.file_list_widget = QtWidgets.QListWidget()
        self.file_list_widget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.file_list_widget.itemSelectionChanged.connect(self.update_plot)

        controls_layout.addWidget(self.load_button)
        controls_layout.addWidget(QtWidgets.QLabel("Select files to display:"))
        controls_layout.addWidget(self.file_list_widget)

        # --- Plot (Right Side) ---
        self.plot_canvas = PlotCanvas(self)

        main_layout.addWidget(controls_widget)
        main_layout.addWidget(self.plot_canvas, 1) # Give plot more stretch factor

    def load_csv_files(self):
        """Opens a file dialog to select multiple CSVs and processes them."""
        options = QtWidgets.QFileDialog.Options()
        file_names, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Select CSV Files", "", "CSV Files (*.csv);;All Files (*)", options=options
        )

        if not file_names:
            return

        # Clear existing data and UI elements
        self.loaded_data.clear()
        self.file_list_widget.clear()

        for file_path in file_names:
            try:
                freq_data, mag_data = [], []
                with open(file_path, 'r', newline='') as f:
                    reader = csv.reader(f)
                    header = next(reader)  # Skip header
                    # Find column indices
                    try:
                        freq_idx = header.index('Frequency')
                        mag_idx = header.index('Magnitude')
                    except ValueError:
                        print(f"Warning: 'Frequency' or 'Magnitude' column not found in {os.path.basename(file_path)}. Skipping.")
                        continue

                    for row in reader:
                        freq_data.append(float(row[freq_idx]))
                        mag_data.append(float(row[mag_idx]))
                
                # Extract amplitude from filename for the legend label
                filename = os.path.basename(file_path)
                match = re.search(r'(-?\d+\.?\d*)', filename)
                label = f"{match.group(1)} dBm" if match else filename

                # Store the loaded data
                self.loaded_data.append({
                    "freq": np.array(freq_data),
                    "mag": np.array(mag_data),
                    "label": label,
                    "filename": filename
                })

            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

        # Populate the list widget
        for i, data in enumerate(self.loaded_data):
            item = QtWidgets.QListWidgetItem(data["filename"])
            item.setData(QtCore.Qt.UserRole, i) # Store index to self.loaded_data
            self.file_list_widget.addItem(item)
            item.setSelected(True) # Select all by default
        
        # The itemSelectionChanged signal will trigger the plot update
        # If only one item, it might not fire, so call it manually.
        if len(self.loaded_data) > 0:
             self.update_plot()


    def update_plot(self):
        """Filters data based on list selection and tells the canvas to replot."""
        selected_indices = {item.data(QtCore.Qt.UserRole) for item in self.file_list_widget.selectedItems()}
        
        plot_data = []
        for i, data in enumerate(self.loaded_data):
            if i in selected_indices:
                plot_data.append((data["freq"], data["mag"], data["label"]))
        
        # Sort plot_data by amplitude (extracted from label) for consistent legend ordering
        def extract_amplitude(label):
            """Extract the numerical amplitude value from a label like '-10.0 dBm'"""
            try:
                # Find the number before 'dBm' in the label
                import re
                match = re.search(r'(-?\d+\.?\d*)\s*dBm', label)
                return float(match.group(1)) if match else float('inf')
            except:
                return float('inf')
        
        # Sort by amplitude in descending order
        plot_data.sort(key=lambda x: extract_amplitude(x[2]), reverse=True)
        
        self.plot_canvas.update_overlaid_plot(plot_data)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_window = CsvPlotterWindow()
    main_window.show()
    sys.exit(app.exec_())
