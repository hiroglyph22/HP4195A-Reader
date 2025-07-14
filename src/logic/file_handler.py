import csv
import json
import os
from PyQt5 import QtWidgets

class FileHandler:
    def save_file_dialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 
            "Save File", 
            "", 
            "CSV Files (*.csv);;All Files (*)", 
            options=options
        )
        if file_name:
            if not file_name.endswith('.csv'):
                file_name += '.csv'
            try:
                self.save_file(file_name)
            except (PermissionError, OSError) as e:
                self.logger.error(f"Could not write to file {file_name}: {str(e)}")
                QtWidgets.QMessageBox.critical(
                    self, 
                    "Save Error", 
                    f"Could not save file: {str(e)}"
                )

    def save_file(self, file_name):
        self.logger.info(f'Saving data to: {file_name}')
        rows = zip(self.graph.freq_data, self.graph.mag_data, self.graph.phase_data)
        with open(file_name, "w", newline='') as output:
            writer = csv.writer(output)
            writer.writerow(['Frequency', 'Magnitude', 'Phase'])
            writer.writerows(rows)
    
    def load_config_file_dialog(self):
        """Load machine configuration from CSV or JSON file."""
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Load Configuration File",
            "",
            "All Config Files (*.csv *.json);;CSV Files (*.csv);;JSON Files (*.json);;All Files (*)",
            options=options
        )
        
        if file_name:
            try:
                config = self.load_config_file(file_name)
                if config:
                    return config
                else:
                    QtWidgets.QMessageBox.critical(
                        self,
                        "Load Error",
                        f"Could not load configuration from: {file_name}"
                    )
            except (PermissionError, OSError) as e:
                self.logger.error(f"Could not read file {file_name}: {str(e)}")
                QtWidgets.QMessageBox.critical(
                    self,
                    "Load Error",
                    f"Could not load file: {str(e)}"
                )
        return None
    
    def load_config_file(self, file_name):
        """Load configuration from CSV or JSON file."""
        self.logger.info(f'Loading configuration from: {file_name}')
        
        file_ext = os.path.splitext(file_name)[1].lower()
        
        try:
            if file_ext == '.csv':
                return self.load_csv_config(file_name)
            elif file_ext == '.json':
                return self.load_json_config(file_name)
            else:
                # Try to auto-detect file type
                with open(file_name, 'r') as f:
                    first_char = f.read(1)
                    if first_char == '{':
                        return self.load_json_config(file_name)
                    else:
                        return self.load_csv_config(file_name)
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            return None
    
    def load_csv_config(self, file_name):
        """Load configuration from CSV file."""
        config = {}
        with open(file_name, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
            
            for row in rows:
                if len(row) >= 2 and row[0] and row[0] != 'Parameter' and row[0] != '':
                    key = row[0].lower().replace(' ', '_').replace('(', '').replace(')', '')
                    value = row[1]
                    
                    # Try to convert to appropriate type
                    try:
                        if '.' in value:
                            config[key] = float(value)
                        else:
                            config[key] = int(value)
                    except ValueError:
                        config[key] = value
        
        return config
    
    def load_json_config(self, file_name):
        """Load configuration from JSON file."""
        with open(file_name, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
            
            # Handle different JSON structures
            if 'hp4195a_configuration' in data:
                return data['hp4195a_configuration']
            else:
                return data