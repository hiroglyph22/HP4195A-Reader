import csv
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