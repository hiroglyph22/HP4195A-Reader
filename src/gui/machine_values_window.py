"""
Machine Values Window for HP4195A Reader.

This window displays all important machine settings and allows exporting them.
It provides an interface for initial machine setup and configuration viewing.
"""

import json
import csv
import os
from typing import Dict, Any, Optional
from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime

class MachineValuesWindow(QtWidgets.QDialog):
    """
    A dialog window that displays and manages HP4195A machine configuration values.
    
    Features:
    - Display current machine settings in a formatted table
    - Refresh values from the instrument
    - Export settings to CSV or JSON
    - Initial setup configuration
    """
    
    def __init__(self, parent=None, command_queue=None, message_queue=None, data_queue=None):
        super(MachineValuesWindow, self).__init__(parent)
        self.command_queue = command_queue
        self.message_queue = message_queue
        self.data_queue = data_queue
        
        # Machine values storage
        self.machine_values: Dict[str, Any] = {
            'device_id': 'Unknown',
            'connection_status': 'Disconnected',
            'center_frequency': 'Unknown',
            'span': 'Unknown', 
            'start_frequency': 'Unknown',
            'stop_frequency': 'Unknown',
            'resolution_bandwidth': 'Unknown',
            'oscillator_1_amplitude': 'Unknown',
            'sweep_mode': 'Unknown',
            'last_updated': 'Never'
        }
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("HP4195A Machine Configuration")
        self.setWindowIcon(QtGui.QIcon('assets/icon.png'))
        self.setModal(True)
        self.resize(600, 500)
        
        # Main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(15)
        
        # Title section
        title_label = QtWidgets.QLabel("HP4195A Machine Configuration")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Status section
        status_group = QtWidgets.QGroupBox("Connection Status")
        status_layout = QtWidgets.QHBoxLayout()
        
        self.connection_label = QtWidgets.QLabel("Status: Unknown")
        self.connection_label.setStyleSheet("padding: 5px;")
        status_layout.addWidget(self.connection_label)
        
        status_layout.addStretch()
        
        self.refresh_button = QtWidgets.QPushButton("Refresh Values")
        self.refresh_button.setToolTip("Query the instrument for current settings")
        self.refresh_button.clicked.connect(self.refresh_values)
        status_layout.addWidget(self.refresh_button)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # Values table
        values_group = QtWidgets.QGroupBox("Machine Settings")
        values_layout = QtWidgets.QVBoxLayout()
        
        self.values_table = QtWidgets.QTableWidget()
        self.values_table.setColumnCount(2)
        self.values_table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.values_table.horizontalHeader().setStretchLastSection(True)
        self.values_table.setAlternatingRowColors(True)
        self.values_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        
        values_layout.addWidget(self.values_table)
        values_group.setLayout(values_layout)
        main_layout.addWidget(values_group)
        
        # Action buttons
        button_group = QtWidgets.QGroupBox("Actions")
        button_layout = QtWidgets.QHBoxLayout()
        
        self.export_csv_button = QtWidgets.QPushButton("Export to CSV")
        self.export_csv_button.setToolTip("Save machine settings to CSV file")
        self.export_csv_button.clicked.connect(self.export_to_csv)
        button_layout.addWidget(self.export_csv_button)
        
        self.export_json_button = QtWidgets.QPushButton("Export to JSON")
        self.export_json_button.setToolTip("Save machine settings to JSON file")
        self.export_json_button.clicked.connect(self.export_to_json)
        button_layout.addWidget(self.export_json_button)
        
        self.import_csv_button = QtWidgets.QPushButton("Import from CSV")
        self.import_csv_button.setToolTip("Load machine settings from CSV file")
        self.import_csv_button.clicked.connect(self.import_from_csv)
        button_layout.addWidget(self.import_csv_button)
        
        self.import_json_button = QtWidgets.QPushButton("Import from JSON")
        self.import_json_button.setToolTip("Load machine settings from JSON file")
        self.import_json_button.clicked.connect(self.import_from_json)
        button_layout.addWidget(self.import_json_button)
        
        button_layout.addStretch()
        
        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        button_group.setLayout(button_layout)
        main_layout.addWidget(button_group)
        
        self.setLayout(main_layout)
        
        # Initial population of table
        self.update_values_display()
        
    def update_values_display(self):
        """Update the values table with current machine values."""
        # Define display-friendly names and formatting
        display_mappings = {
            'device_id': 'Device ID',
            'connection_status': 'Connection Status',
            'center_frequency': 'Center Frequency (Hz)',
            'span': 'Span (Hz)', 
            'start_frequency': 'Start Frequency (Hz)',
            'stop_frequency': 'Stop Frequency (Hz)',
            'resolution_bandwidth': 'Resolution Bandwidth (Hz)',
            'oscillator_1_amplitude': 'Oscillator 1 Amplitude (dBm)',
            'sweep_mode': 'Sweep Mode',
            'last_updated': 'Last Updated'
        }
        
        self.values_table.setRowCount(len(self.machine_values))
        
        row = 0
        for key, value in self.machine_values.items():
            # Parameter name
            param_item = QtWidgets.QTableWidgetItem(display_mappings.get(key, key))
            param_item.setFlags(param_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.values_table.setItem(row, 0, param_item)
            
            # Parameter value
            value_str = str(value) if value is not None else "Unknown"
            value_item = QtWidgets.QTableWidgetItem(value_str)
            value_item.setFlags(value_item.flags() & ~QtCore.Qt.ItemIsEditable)
            
            # Color coding for connection status
            if key == 'connection_status':
                if value == 'Connected':
                    value_item.setBackground(QtGui.QColor(200, 255, 200))  # Light green
                elif value == 'Disconnected':
                    value_item.setBackground(QtGui.QColor(255, 200, 200))  # Light red
                    
            self.values_table.setItem(row, 1, value_item)
            row += 1
            
        # Update connection status label
        status = self.machine_values.get('connection_status', 'Unknown')
        self.connection_label.setText(f"Status: {status}")
        if status == 'Connected':
            self.connection_label.setStyleSheet("color: green; padding: 5px; font-weight: bold;")
        elif status == 'Disconnected':
            self.connection_label.setStyleSheet("color: red; padding: 5px; font-weight: bold;")
        else:
            self.connection_label.setStyleSheet("color: orange; padding: 5px; font-weight: bold;")
            
    def refresh_values(self):
        """Query the instrument for current values."""
        if not self.command_queue or not self.message_queue or not self.data_queue:
            self.show_error("Cannot refresh values: No communication queues available")
            return
            
        try:
            # Check if connected first
            parent_connected = getattr(self.parent(), 'connected', False) if self.parent() else False
            
            if not parent_connected:
                self.machine_values['connection_status'] = 'Disconnected'
                self.machine_values['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.update_values_display()
                self.show_error("Cannot refresh values: Not connected to instrument")
                return
                
            self.machine_values['connection_status'] = 'Connected'
            
            # Query all machine parameters
            queries = [
                ('device_id', 'ID?'),
                ('center_frequency', 'CENTER?'),
                ('span', 'SPAN?'),
                ('start_frequency', 'START?'),
                ('stop_frequency', 'STOP?'),
                ('resolution_bandwidth', 'RBW?'),
                ('oscillator_1_amplitude', 'OSC1?')
            ]
            
            # Send query command for machine values
            self.command_queue.put('get_machine_values')
            
            # Wait for response
            if self.message_queue.get(timeout=5):  # Wait up to 5 seconds
                # Get the values dictionary from data queue
                values_dict = self.data_queue.get(timeout=5)
                self.machine_values.update(values_dict)
                self.machine_values['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.update_values_display()
            else:
                self.show_error("Failed to retrieve machine values from instrument")
                
        except Exception as e:
            self.show_error(f"Error refreshing values: {str(e)}")
            
    def export_to_csv(self):
        """Export machine values to CSV file."""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Machine Values to CSV",
            f"hp4195a_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Parameter', 'Value', 'Exported'])
                    writer.writerow(['', '', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                    writer.writerow([])  # Empty row
                    
                    # Write machine values
                    for key, value in self.machine_values.items():
                        display_name = key.replace('_', ' ').title()
                        writer.writerow([display_name, str(value)])
                        
                self.show_info(f"Machine values exported successfully to:\n{file_path}")
                
            except Exception as e:
                self.show_error(f"Error exporting to CSV: {str(e)}")
                
    def export_to_json(self):
        """Export machine values to JSON file."""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Machine Values to JSON", 
            f"hp4195a_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                export_data = {
                    'hp4195a_configuration': self.machine_values,
                    'exported_at': datetime.now().isoformat(),
                    'exported_by': 'HP4195A Reader Application'
                }
                
                with open(file_path, 'w', encoding='utf-8') as jsonfile:
                    json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
                    
                self.show_info(f"Machine values exported successfully to:\n{file_path}")
                
            except Exception as e:
                self.show_error(f"Error exporting to JSON: {str(e)}")
                
    def import_from_csv(self):
        """Import machine values from CSV file."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Import Machine Values from CSV",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                imported_values = {}
                with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    rows = list(reader)
                    
                    # Skip header and metadata rows, look for actual parameter data
                    for row in rows:
                        if len(row) >= 2 and row[0] and row[0] != 'Parameter' and row[0] != '':
                            # Convert display name back to key format
                            display_name = row[0]
                            value = row[1]
                            
                            # Map display names back to internal keys
                            key_mapping = {
                                'Device ID': 'device_id',
                                'Connection Status': 'connection_status',
                                'Center Frequency (Hz)': 'center_frequency',
                                'Span (Hz)': 'span',
                                'Start Frequency (Hz)': 'start_frequency',
                                'Stop Frequency (Hz)': 'stop_frequency',
                                'Resolution Bandwidth (Hz)': 'resolution_bandwidth',
                                'Oscillator 1 Amplitude (Dbm)': 'oscillator_1_amplitude',
                                'Sweep Mode': 'sweep_mode',
                                'Last Updated': 'last_updated'
                            }
                            
                            # Find the matching key
                            key = None
                            for display_key, internal_key in key_mapping.items():
                                if display_name == display_key or display_name.lower().replace(' ', '_') == internal_key:
                                    key = internal_key
                                    break
                            
                            if key:
                                # Try to convert numeric values
                                try:
                                    if key in ['center_frequency', 'span', 'start_frequency', 'stop_frequency', 'resolution_bandwidth']:
                                        imported_values[key] = float(value)
                                    elif key == 'oscillator_1_amplitude':
                                        imported_values[key] = float(value)
                                    else:
                                        imported_values[key] = value
                                except ValueError:
                                    imported_values[key] = value
                
                if imported_values:
                    # Update machine values with imported data
                    self.machine_values.update(imported_values)
                    self.machine_values['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.update_values_display()
                    
                    self.show_info(f"Machine values imported successfully from:\n{file_path}")
                else:
                    self.show_error("No valid machine values found in the CSV file.")
                    
            except Exception as e:
                self.show_error(f"Error importing from CSV: {str(e)}")
                
    def import_from_json(self):
        """Import machine values from JSON file."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Import Machine Values from JSON",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as jsonfile:
                    data = json.load(jsonfile)
                    
                # Handle different JSON structures
                imported_values = {}
                if 'hp4195a_configuration' in data:
                    imported_values = data['hp4195a_configuration']
                elif isinstance(data, dict):
                    # Assume the entire JSON is the configuration
                    imported_values = data
                else:
                    self.show_error("Invalid JSON format. Expected configuration object.")
                    return
                
                if imported_values:
                    # Validate and update machine values
                    valid_keys = set(self.machine_values.keys())
                    filtered_values = {k: v for k, v in imported_values.items() if k in valid_keys}
                    
                    if filtered_values:
                        self.machine_values.update(filtered_values)
                        self.machine_values['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.update_values_display()
                        
                        self.show_info(f"Machine values imported successfully from:\n{file_path}\n\nImported {len(filtered_values)} parameters.")
                    else:
                        self.show_error("No valid machine parameters found in the JSON file.")
                else:
                    self.show_error("No configuration data found in the JSON file.")
                    
            except Exception as e:
                self.show_error(f"Error importing from JSON: {str(e)}")
                
    def show_error(self, message: str):
        """Show error message dialog."""
        QtWidgets.QMessageBox.critical(self, "Error", message)
        
    def show_info(self, message: str):
        """Show information message dialog."""
        QtWidgets.QMessageBox.information(self, "Information", message)
        
    def set_machine_value(self, key: str, value: Any):
        """Set a machine value programmatically."""
        self.machine_values[key] = value
        self.update_values_display()
        
    def get_machine_values(self) -> Dict[str, Any]:
        """Get current machine values dictionary."""
        return self.machine_values.copy()


class InitialSetupDialog(QtWidgets.QDialog):
    """
    Dialog for initial machine setup configuration.
    Allows setting basic parameters before connecting.
    """
    
    def __init__(self, parent=None):
        super(InitialSetupDialog, self).__init__(parent)
        self.setup_values = {}
        self.init_ui()
        
    def init_ui(self):
        """Initialize the setup dialog UI."""
        self.setWindowTitle("HP4195A Initial Setup")
        self.setWindowIcon(QtGui.QIcon('assets/icon.png'))
        self.setModal(True)
        self.resize(400, 350)
        
        layout = QtWidgets.QVBoxLayout()
        
        # Title
        title_label = QtWidgets.QLabel("Initial Machine Setup")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Setup form
        form_layout = QtWidgets.QFormLayout()
        
        self.center_freq_input = QtWidgets.QLineEdit()
        self.center_freq_input.setPlaceholderText("e.g., 1000000 (1 MHz)")
        form_layout.addRow("Center Frequency (Hz):", self.center_freq_input)
        
        self.span_input = QtWidgets.QLineEdit()
        self.span_input.setPlaceholderText("e.g., 100000 (100 kHz)")
        self.span_input.setText("10000")  # Default span
        form_layout.addRow("Span (Hz):", self.span_input)
        
        self.start_freq_input = QtWidgets.QLineEdit()
        self.start_freq_input.setPlaceholderText("e.g., 500000 (500 kHz)")
        form_layout.addRow("Start Frequency (Hz):", self.start_freq_input)
        
        self.stop_freq_input = QtWidgets.QLineEdit()
        self.stop_freq_input.setPlaceholderText("e.g., 1500000 (1.5 MHz)")
        form_layout.addRow("Stop Frequency (Hz):", self.stop_freq_input)
        
        self.rbw_input = QtWidgets.QComboBox()
        self.rbw_input.addItems(["10", "30", "100", "300", "1000", "3000"])
        self.rbw_input.setCurrentText("100")
        form_layout.addRow("Resolution Bandwidth (Hz):", self.rbw_input)
        
        self.osc1_input = QtWidgets.QLineEdit()
        self.osc1_input.setPlaceholderText("e.g., -10 (dBm)")
        self.osc1_input.setText("0")  # Default amplitude
        form_layout.addRow("Oscillator 1 Amplitude (dBm):", self.osc1_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        self.apply_button = QtWidgets.QPushButton("Apply Settings")
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)
        
        button_layout.addStretch()
        
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def apply_settings(self):
        """Apply the configured settings."""
        try:
            # Validate inputs
            values = {}
            
            if self.center_freq_input.text():
                values['center_frequency'] = float(self.center_freq_input.text())
                
            if self.span_input.text():
                values['span'] = float(self.span_input.text())
                
            if self.start_freq_input.text():
                values['start_frequency'] = float(self.start_freq_input.text())
                
            if self.stop_freq_input.text():
                values['stop_frequency'] = float(self.stop_freq_input.text())
                
            values['resolution_bandwidth'] = float(self.rbw_input.currentText())
            
            if self.osc1_input.text():
                values['oscillator_1_amplitude'] = float(self.osc1_input.text())
                
            self.setup_values = values
            self.accept()
            
        except ValueError as e:
            QtWidgets.QMessageBox.critical(self, "Invalid Input", 
                "Please enter valid numeric values for all fields.")
            
    def get_setup_values(self):
        """Get the configured setup values."""
        return self.setup_values
