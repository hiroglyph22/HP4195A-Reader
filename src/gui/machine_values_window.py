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
        
        self.display_mappings = {
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
        self.key_mappings = {v: k for k, v in self.display_mappings.items()}

        self.editable_keys = [
            'center_frequency', 'span', 'start_frequency', 'stop_frequency',
            'resolution_bandwidth', 'oscillator_1_amplitude'
        ]
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("HP4195A Machine Configuration")
        self.setWindowIcon(QtGui.QIcon('assets/icon.png'))
        self.setModal(True)
        self.resize(600, 650) # Increased height for the new section
        
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

        # Quick Setup section
        quick_setup_group = QtWidgets.QGroupBox("Quick Setup")
        quick_setup_layout = QtWidgets.QFormLayout()
        quick_setup_layout.setSpacing(10)

        self.center_freq_input = QtWidgets.QLineEdit()
        self.center_freq_input.setPlaceholderText("e.g., 1000000 for 1 MHz")
        quick_setup_layout.addRow("Center Frequency (Hz):", self.center_freq_input)

        self.span_input = QtWidgets.QLineEdit()
        self.span_input.setPlaceholderText("e.g., 10000 for 10 kHz")
        quick_setup_layout.addRow("Span (Hz):", self.span_input)

        self.start_freq_input = QtWidgets.QLineEdit()
        self.start_freq_input.setPlaceholderText("Auto-calculated if empty")
        quick_setup_layout.addRow("Start Frequency (Hz):", self.start_freq_input)

        self.stop_freq_input = QtWidgets.QLineEdit()
        self.stop_freq_input.setPlaceholderText("Auto-calculated if empty")
        quick_setup_layout.addRow("Stop Frequency (Hz):", self.stop_freq_input)

        self.resolution_bw_input = QtWidgets.QLineEdit()
        self.resolution_bw_input.setPlaceholderText("e.g., 1000 for 1 kHz")
        quick_setup_layout.addRow("Resolution Bandwidth (Hz):", self.resolution_bw_input)

        self.osc1_amplitude_input = QtWidgets.QLineEdit()
        self.osc1_amplitude_input.setPlaceholderText("e.g., -10 for -10 dBm")
        quick_setup_layout.addRow("Oscillator 1 Amplitude (dBm):", self.osc1_amplitude_input)
        
        populate_button = QtWidgets.QPushButton("Populate Table from Quick Setup")
        populate_button.setToolTip("Use the values above to fill the settings table below.")
        populate_button.clicked.connect(self.populate_from_quick_setup)
        quick_setup_layout.addRow(populate_button)

        quick_setup_group.setLayout(quick_setup_layout)
        main_layout.addWidget(quick_setup_group)
        
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
        
        self.apply_button = QtWidgets.QPushButton("Apply Settings")
        self.apply_button.setToolTip("Apply the settings in the table to the instrument")
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)
        
        button_layout.addStretch(1)

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

    def populate_from_quick_setup(self):
        """Populate the machine settings table from the quick setup inputs."""
        updates = {}
        center_freq_str = self.center_freq_input.text()
        span_str = self.span_input.text()
        start_freq_str = self.start_freq_input.text()
        stop_freq_str = self.stop_freq_input.text()
        resolution_bw_str = self.resolution_bw_input.text()
        osc1_amplitude_str = self.osc1_amplitude_input.text()

        center_freq, span = None, None

        # Validate and gather values
        if center_freq_str:
            try:
                center_freq = float(center_freq_str)
                updates['center_frequency'] = center_freq
            except ValueError:
                self.show_error("Invalid Center Frequency. Must be a number.")
                return

        if span_str:
            try:
                span = float(span_str)
                updates['span'] = span
            except ValueError:
                self.show_error("Invalid Span. Must be a number.")
                return
        
        # Auto-calculate start/stop if they are empty and center/span are provided
        if center_freq is not None and span is not None:
            if not start_freq_str:
                updates['start_frequency'] = center_freq - (span / 2)
            if not stop_freq_str:
                updates['stop_frequency'] = center_freq + (span / 2)

        # Overwrite with explicit values if provided
        if start_freq_str:
            try:
                updates['start_frequency'] = float(start_freq_str)
            except ValueError:
                self.show_error("Invalid Start Frequency. Must be a number.")
                return

        if stop_freq_str:
            try:
                updates['stop_frequency'] = float(stop_freq_str)
            except ValueError:
                self.show_error("Invalid Stop Frequency. Must be a number.")
                return

        # Handle resolution bandwidth
        if resolution_bw_str:
            try:
                updates['resolution_bandwidth'] = float(resolution_bw_str)
            except ValueError:
                self.show_error("Invalid Resolution Bandwidth. Must be a number.")
                return

        # Handle oscillator 1 amplitude
        if osc1_amplitude_str:
            try:
                updates['oscillator_1_amplitude'] = float(osc1_amplitude_str)
            except ValueError:
                self.show_error("Invalid Oscillator 1 Amplitude. Must be a number.")
                return

        # Batch update the internal state and refresh the display
        self.machine_values.update(updates)
        self.update_values_display()
        
        self.show_info("Table populated. Review and click 'Apply Settings' to send to instrument.")
            
    def update_values_display(self):
        """Update the values table with current machine values."""
        self.values_table.setRowCount(len(self.machine_values))
        
        row = 0
        for key, value in self.machine_values.items():
            # Parameter name
            param_item = QtWidgets.QTableWidgetItem(self.display_mappings.get(key, key))
            param_item.setFlags(param_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.values_table.setItem(row, 0, param_item)
            
            # Parameter value
            value_str = str(value) if value is not None else "Unknown"
            value_item = QtWidgets.QTableWidgetItem(value_str)
            
            if key in self.editable_keys:
                value_item.setFlags(value_item.flags() | QtCore.Qt.ItemIsEditable)
            else:
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
            
    def apply_settings(self):
        """Read settings from the table and apply them to the instrument."""
        if not self.command_queue:
            self.show_error("Cannot apply settings: No command queue available.")
            return

        parent_connected = getattr(self.parent(), 'connected', False) if self.parent() else False
        if not parent_connected:
            self.show_error("Cannot apply settings: Not connected to instrument.")
            return

        new_settings = {}
        for row in range(self.values_table.rowCount()):
            param_item = self.values_table.item(row, 0)
            value_item = self.values_table.item(row, 1)
            
            if param_item and value_item:
                display_name = param_item.text()
                value_str = value_item.text()
                
                key = self.key_mappings.get(display_name)
                
                if key and key in self.editable_keys:
                    try:
                        new_settings[key] = float(value_str)
                    except ValueError:
                        self.show_error(f"Invalid value for {display_name}: '{value_str}'. Must be a number.")
                        return
        
        if new_settings:
            # Send command string first, then settings dictionary
            self.command_queue.put('apply_machine_settings')
            self.command_queue.put(new_settings)
            self.show_info("Settings have been sent to the instrument. Use 'Refresh Values' to confirm.")
        else:
            self.show_info("No changes to apply.")

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
                try:
                    values_dict = self.data_queue.get(timeout=5)
                    
                    # Validate that we received a proper dictionary
                    if isinstance(values_dict, dict):
                        self.machine_values.update(values_dict)
                        self.machine_values['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.update_values_display()
                        self.show_info("Machine values refreshed successfully.")
                    else:
                        self.show_error(f"Invalid data received from instrument: expected dictionary, got {type(values_dict)}")
                        
                except Exception as e:
                    self.show_error(f"Error processing data from instrument: {str(e)}")
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
                        display_name = self.display_mappings.get(key, key.replace('_', ' ').title())
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
                            key = self.key_mappings.get(display_name)

                            if not key:
                                # Fallback for slight variations in naming
                                for d_name, i_key in self.display_mappings.items():
                                    if display_name.lower().strip() == d_name.lower().strip():
                                        key = i_key
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
