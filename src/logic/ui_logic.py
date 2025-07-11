from PyQt5 import QtWidgets
try:
    # Try relative imports first (for when running as a module/package)
    from ..gui.help_window import Help_Window
except ImportError:
    # Fall back to absolute imports (for when running directly)
    from gui.help_window import Help_Window

class UiLogic:
    def toggle_connect_button(self):
        self.command_button.setEnabled(len(self.command_box.text()) > 0 and self.connected)
    
    def help_dialog(self):
        help_window = Help_Window()
        help_window.exec_()

    def toggle_pause(self, started):
        if started:
            self.timer.start()
            self.pause_button.setText('Pause Auto-Update')
        else:
            self.timer.stop()
            self.pause_button.setText('Start Auto-Update')
            
    def show_error_dialog(self, title, text):
        error_dialog = QtWidgets.QMessageBox()
        error_dialog.setIcon(QtWidgets.QMessageBox.Warning)
        error_dialog.setText(title)
        error_dialog.setInformativeText(text)
        error_dialog.setWindowTitle("Error")
        error_dialog.exec_()