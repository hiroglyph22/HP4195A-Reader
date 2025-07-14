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

    def show_machine_setup(self):
        """Show the machine setup and values window."""
        try:
            # Import here to avoid circular imports
            from ..gui.machine_values_window import MachineValuesWindow, InitialSetupDialog
        except ImportError:
            from gui.machine_values_window import MachineValuesWindow, InitialSetupDialog
            
        # Show a choice dialog
        choice = QtWidgets.QMessageBox.question(
            self, 
            "Machine Setup",
            "What would you like to do?\n\nClick 'Yes' to view current machine values\nClick 'No' to configure initial setup",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
            QtWidgets.QMessageBox.Yes
        )
        
        if choice == QtWidgets.QMessageBox.Yes:
            # Show machine values window
            machine_window = MachineValuesWindow(
                parent=self,
                command_queue=self.command_queue,
                message_queue=self.message_queue, 
                data_queue=self.data_queue
            )
            machine_window.exec_()
            
        elif choice == QtWidgets.QMessageBox.No:
            # Show initial setup dialog
            setup_dialog = InitialSetupDialog(parent=self)
            if setup_dialog.exec_() == QtWidgets.QDialog.Accepted:
                setup_values = setup_dialog.get_setup_values()
                if setup_values and self.connected:
                    # Apply the setup to the machine
                    self.command_queue.put('initial_setup')
                    self.command_queue.put(setup_values)
                    
                    if self.message_queue.get(timeout=10):  # Wait up to 10 seconds
                        QtWidgets.QMessageBox.information(
                            self, 
                            "Setup Complete", 
                            "Initial machine setup has been applied successfully."
                        )
                    else:
                        self.show_error_dialog(
                            "Setup Failed", 
                            "Failed to apply initial setup to the machine."
                        )
                elif setup_values and not self.connected:
                    self.show_error_dialog(
                        "Not Connected", 
                        "Please connect to the instrument first before applying setup."
                    )
                    
        # If Cancel was clicked, do nothing
                    
    def load_config_dialog(self):
        """Load machine configuration from CSV or JSON file."""
        config = self.load_config_file_dialog()
        
        if config:
            # Show the loaded configuration in machine values window
            try:
                # Import here to avoid circular imports
                try:
                    from ..gui.machine_values_window import MachineValuesWindow
                except ImportError:
                    from gui.machine_values_window import MachineValuesWindow
                
                machine_window = MachineValuesWindow(
                    parent=self,
                    command_queue=self.command_queue,
                    message_queue=self.message_queue,
                    data_queue=self.data_queue
                )
                
                # Update machine window with loaded config
                for key, value in config.items():
                    machine_window.set_machine_value(key, value)
                
                machine_window.exec_()
                
            except Exception as e:
                self.show_error_dialog(
                    "Display Error",
                    f"Failed to show machine values window: {str(e)}"
                )