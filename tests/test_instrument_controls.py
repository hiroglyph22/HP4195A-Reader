# tests/test_instrument_controls.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt5 import QtWidgets, QtCore
from src.logic.instrument_controls import InstrumentControls
from src.constants import Commands, DefaultValues


class MockMainWindow(InstrumentControls):
    """Mock MainWindow class that inherits from InstrumentControls for testing."""
    
    def __init__(self):
        # Initialize required attributes for testing
        self.logger = Mock()
        self.connected = False
        self.paused = False
        
        # Mock HP4195A interface
        self.hp4195a = Mock()
        self.hp4195a.command_queue = Mock()
        self.hp4195a.data_queue = Mock()
        self.hp4195a.add_command = Mock()
        
        # Mock UI components
        self.connect_button = Mock()
        self.acquire_button = Mock()
        self.save_button = Mock()
        self.pause_button = Mock()
        self.peak_freq_input = Mock()
        self.sweep_range_input = Mock()
        
        # Mock graph
        self.graph = Mock()
        self.graph.clear_plot = Mock()
        self.graph.update_plot = Mock()
        
        # Mock timer
        self.timer = Mock()
        
        # Mock message box for testing
        self.message_box = Mock()


@pytest.fixture
def mock_window():
    """Create a mock main window for testing."""
    return MockMainWindow()


class TestInstrumentControlsConnection:
    """Test instrument connection functionality."""
    
    def test_connect_success(self, mock_window):
        """Test successful connection to instrument."""
        # Setup successful connection
        mock_window.hp4195a.connected = False
        
        # Call connect method
        mock_window.connect()
        
        # Verify connection command was sent
        mock_window.hp4195a.add_command.assert_called_with(
            Commands.CONNECT.value, 
            ()
        )
        
        # Verify logger was called
        mock_window.logger.info.assert_called_with('Attempting to connect to HP4195A...')
    
    def test_connect_when_already_connected(self, mock_window):
        """Test connect when already connected."""
        # Setup already connected state
        mock_window.connected = True
        
        # Call connect method
        mock_window.connect()
        
        # Should not send connect command
        mock_window.hp4195a.add_command.assert_not_called()
        
        # Should log that already connected
        mock_window.logger.info.assert_called_with('Already connected to HP4195A')
    
    def test_disconnect(self, mock_window):
        """Test disconnection from instrument."""
        # Setup connected state
        mock_window.connected = True
        mock_window.paused = False
        
        # Call disconnect method
        mock_window.disconnect()
        
        # Verify disconnect command was sent
        mock_window.hp4195a.add_command.assert_called_with(
            Commands.DISCONNECT.value,
            ()
        )
        
        # Verify logger was called
        mock_window.logger.info.assert_called_with('Disconnecting from HP4195A...')
    
    def test_disconnect_when_not_connected(self, mock_window):
        """Test disconnect when not connected."""
        # Setup not connected state
        mock_window.connected = False
        
        # Call disconnect method
        mock_window.disconnect()
        
        # Should not send disconnect command
        mock_window.hp4195a.add_command.assert_not_called()
        
        # Should log not connected
        mock_window.logger.info.assert_called_with('Not connected to HP4195A')


class TestInstrumentControlsDataAcquisition:
    """Test data acquisition functionality."""
    
    def test_acquire_data_when_connected(self, mock_window):
        """Test data acquisition when connected."""
        # Setup connected state
        mock_window.connected = True
        
        # Call acquire method
        mock_window.acquire()
        
        # Verify acquisition command was sent
        mock_window.hp4195a.add_command.assert_called_with(
            Commands.START_ACQUISITION.value,
            ()
        )
        
        # Verify logger was called
        mock_window.logger.info.assert_called_with('Starting data acquisition...')
    
    def test_acquire_data_when_not_connected(self, mock_window):
        """Test data acquisition when not connected."""
        # Setup not connected state
        mock_window.connected = False
        
        with patch('src.logic.instrument_controls.QtWidgets.QMessageBox.warning') as mock_warning:
            # Call acquire method
            mock_window.acquire()
            
            # Should show warning message
            mock_warning.assert_called_once()
            
            # Should not send acquisition command
            mock_window.hp4195a.add_command.assert_not_called()
    
    def test_pause_resume_functionality(self, mock_window):
        """Test pause and resume functionality."""
        # Test pause
        mock_window.paused = False
        mock_window.pause_resume()
        
        # Should call timer stop and update button
        mock_window.timer.stop.assert_called_once()
        mock_window.pause_button.setText.assert_called_with('Resume Auto-Update')
        
        # Test resume
        mock_window.paused = True
        mock_window.pause_resume()
        
        # Should call timer start and update button
        mock_window.timer.start.assert_called()
        mock_window.pause_button.setText.assert_called_with('Pause Auto-Update')


class TestInstrumentControlsFrequencyControl:
    """Test frequency control methods."""
    
    def test_set_center_and_span_valid_input(self, mock_window):
        """Test setting center frequency and span with valid input."""
        # Setup UI input values
        mock_window.peak_freq_input.text.return_value = "1000000"  # 1 MHz
        mock_window.sweep_range_input.text.return_value = "50000"  # 50 kHz
        mock_window.connected = True
        
        # Call method
        mock_window.set_center_and_span()
        
        # Verify command was sent with correct parameters
        mock_window.hp4195a.add_command.assert_called_with(
            Commands.SET_CENTER_AND_SPAN.value,
            (1000000, 50000)
        )
        
        # Verify logging
        mock_window.logger.info.assert_called()
    
    def test_set_center_and_span_invalid_input(self, mock_window):
        """Test setting center frequency and span with invalid input."""
        # Setup invalid UI input
        mock_window.peak_freq_input.text.return_value = "invalid"
        mock_window.sweep_range_input.text.return_value = "50000"
        
        with patch('src.logic.instrument_controls.QtWidgets.QMessageBox.warning') as mock_warning:
            # Call method
            mock_window.set_center_and_span()
            
            # Should show warning message
            mock_warning.assert_called_once()
            
            # Should not send command
            mock_window.hp4195a.add_command.assert_not_called()
    
    def test_set_center_and_span_not_connected(self, mock_window):
        """Test setting center and span when not connected."""
        # Setup not connected state
        mock_window.connected = False
        mock_window.peak_freq_input.text.return_value = "1000000"
        mock_window.sweep_range_input.text.return_value = "50000"
        
        with patch('src.logic.instrument_controls.QtWidgets.QMessageBox.warning') as mock_warning:
            # Call method
            mock_window.set_center_and_span()
            
            # Should show warning message
            mock_warning.assert_called_once()
            
            # Should not send command
            mock_window.hp4195a.add_command.assert_not_called()
    
    def test_center_on_peak_with_frequency(self, mock_window):
        """Test centering on peak with frequency input."""
        # Setup UI input
        mock_window.peak_freq_input.text.return_value = "1500000"  # 1.5 MHz
        mock_window.connected = True
        
        # Call method
        mock_window.center_on_peak()
        
        # Verify command was sent
        mock_window.hp4195a.add_command.assert_called_with(
            Commands.SET_CENTER_FREQUENCY.value,
            (1500000,)
        )
    
    def test_center_on_peak_invalid_frequency(self, mock_window):
        """Test centering on peak with invalid frequency."""
        # Setup invalid input
        mock_window.peak_freq_input.text.return_value = ""
        
        with patch('src.logic.instrument_controls.QtWidgets.QMessageBox.warning') as mock_warning:
            # Call method
            mock_window.center_on_peak()
            
            # Should show warning
            mock_warning.assert_called_once()
            
            # Should not send command
            mock_window.hp4195a.add_command.assert_not_called()


class TestInstrumentControlsSweepOperations:
    """Test sweep operation methods."""
    
    def test_autofind_peak_when_connected(self, mock_window):
        """Test auto-finding peak when connected."""
        # Setup connected state
        mock_window.connected = True
        
        # Call method
        mock_window.autofind_peak()
        
        # Verify low resolution sweep command was sent
        mock_window.hp4195a.add_command.assert_called_with(
            Commands.LOW_RES_SWEEP.value,
            ()
        )
        
        # Verify logging
        mock_window.logger.info.assert_called_with('Starting auto peak detection...')
    
    def test_autofind_peak_when_not_connected(self, mock_window):
        """Test auto-finding peak when not connected."""
        # Setup not connected state
        mock_window.connected = False
        
        with patch('src.logic.instrument_controls.QtWidgets.QMessageBox.warning') as mock_warning:
            # Call method
            mock_window.autofind_peak()
            
            # Should show warning
            mock_warning.assert_called_once()
            
            # Should not send command
            mock_window.hp4195a.add_command.assert_not_called()


class TestInstrumentControlsAmplitudeSweep:
    """Test amplitude sweep functionality."""
    
    def test_sweeping_range_of_amplitudes_valid_input(self, mock_window):
        """Test amplitude sweep with valid parameters."""
        # Setup connected state
        mock_window.connected = True
        
        # Mock dialog inputs
        with patch('src.logic.instrument_controls.QtWidgets.QInputDialog.getDouble') as mock_double, \
             patch('src.logic.instrument_controls.QtWidgets.QFileDialog.getExistingDirectory') as mock_dir:
            
            # Setup input dialog returns
            mock_double.side_effect = [
                (-20.0, True),  # start amplitude
                (-10.0, True),  # stop amplitude
                (1.0, True)     # step size
            ]
            mock_dir.return_value = "/test/directory"
            
            # Call method
            mock_window.sweeping_range_of_amplitudes()
            
            # Verify command was sent
            mock_window.hp4195a.add_command.assert_called_with(
                Commands.SWEEPING_RANGE_OF_AMPLITUDES.value,
                (-20.0, -10.0, 1.0, "/test/directory")
            )
    
    def test_sweeping_range_of_amplitudes_cancelled(self, mock_window):
        """Test amplitude sweep when user cancels input."""
        mock_window.connected = True
        
        with patch('src.logic.instrument_controls.QtWidgets.QInputDialog.getDouble') as mock_double:
            # User cancels first dialog
            mock_double.return_value = (0.0, False)
            
            # Call method
            mock_window.sweeping_range_of_amplitudes()
            
            # Should not send command
            mock_window.hp4195a.add_command.assert_not_called()
    
    def test_sweeping_range_of_amplitudes_not_connected(self, mock_window):
        """Test amplitude sweep when not connected."""
        mock_window.connected = False
        
        with patch('src.logic.instrument_controls.QtWidgets.QMessageBox.warning') as mock_warning:
            # Call method
            mock_window.sweeping_range_of_amplitudes()
            
            # Should show warning
            mock_warning.assert_called_once()
            
            # Should not proceed with dialogs
            mock_window.hp4195a.add_command.assert_not_called()


class TestInstrumentControlsCommandHandling:
    """Test command input and processing."""
    
    def test_send_command_valid(self, mock_window):
        """Test sending valid GPIB command."""
        # Setup connected state and command input
        mock_window.connected = True
        mock_command_input = Mock()
        mock_command_input.text.return_value = "TEST COMMAND"
        mock_window.command_input = mock_command_input
        
        # Call method
        mock_window.send_command()
        
        # Verify command was sent
        mock_window.hp4195a.add_command.assert_called_with(
            Commands.SEND_COMMAND.value,
            ("TEST COMMAND",)
        )
        
        # Verify input was cleared
        mock_command_input.clear.assert_called_once()
    
    def test_send_command_empty(self, mock_window):
        """Test sending empty command."""
        mock_window.connected = True
        mock_command_input = Mock()
        mock_command_input.text.return_value = ""
        mock_window.command_input = mock_command_input
        
        with patch('src.logic.instrument_controls.QtWidgets.QMessageBox.warning') as mock_warning:
            # Call method
            mock_window.send_command()
            
            # Should show warning
            mock_warning.assert_called_once()
            
            # Should not send command
            mock_window.hp4195a.add_command.assert_not_called()
    
    def test_send_command_not_connected(self, mock_window):
        """Test sending command when not connected."""
        mock_window.connected = False
        mock_command_input = Mock()
        mock_command_input.text.return_value = "TEST"
        mock_window.command_input = mock_command_input
        
        with patch('src.logic.instrument_controls.QtWidgets.QMessageBox.warning') as mock_warning:
            # Call method
            mock_window.send_command()
            
            # Should show warning
            mock_warning.assert_called_once()
            
            # Should not send command
            mock_window.hp4195a.add_command.assert_not_called()


class TestInstrumentControlsButtonStates:
    """Test button state management."""
    
    def test_update_connection_status_connected(self, mock_window):
        """Test updating UI when connected."""
        # Call method with connected status
        mock_window.update_connection_status(True)
        
        # Verify button states
        mock_window.connect_button.setText.assert_called_with('Disconnect')
        mock_window.acquire_button.setEnabled.assert_called_with(True)
        mock_window.save_button.setEnabled.assert_called_with(True)
        
        # Verify internal state
        assert mock_window.connected == True
    
    def test_update_connection_status_disconnected(self, mock_window):
        """Test updating UI when disconnected."""
        # Call method with disconnected status
        mock_window.update_connection_status(False)
        
        # Verify button states
        mock_window.connect_button.setText.assert_called_with('Connect')
        mock_window.acquire_button.setEnabled.assert_called_with(False)
        mock_window.save_button.setEnabled.assert_called_with(False)
        
        # Verify internal state
        assert mock_window.connected == False


class TestInstrumentControlsInputValidation:
    """Test input validation methods."""
    
    def test_validate_frequency_input_valid(self, mock_window):
        """Test frequency input validation with valid values."""
        assert mock_window.validate_frequency_input("1000000") == 1000000.0
        assert mock_window.validate_frequency_input("1.5e6") == 1500000.0
        assert mock_window.validate_frequency_input("0") == 0.0
    
    def test_validate_frequency_input_invalid(self, mock_window):
        """Test frequency input validation with invalid values."""
        assert mock_window.validate_frequency_input("") is None
        assert mock_window.validate_frequency_input("invalid") is None
        assert mock_window.validate_frequency_input("abc123") is None
        assert mock_window.validate_frequency_input("-1000") is None  # Negative frequency
    
    def test_validate_amplitude_input_valid(self, mock_window):
        """Test amplitude input validation with valid values."""
        assert mock_window.validate_amplitude_input("-10.0") == -10.0
        assert mock_window.validate_amplitude_input("0") == 0.0
        assert mock_window.validate_amplitude_input("-20.5") == -20.5
    
    def test_validate_amplitude_input_invalid(self, mock_window):
        """Test amplitude input validation with invalid values."""
        assert mock_window.validate_amplitude_input("") is None
        assert mock_window.validate_amplitude_input("invalid") is None
        assert mock_window.validate_amplitude_input("abc") is None


class TestInstrumentControlsErrorHandling:
    """Test error handling in instrument controls."""
    
    def test_command_exception_handling(self, mock_window):
        """Test handling of command execution exceptions."""
        # Setup mock to raise exception
        mock_window.hp4195a.add_command.side_effect = Exception("Command error")
        mock_window.connected = True
        
        # Should not crash when command fails
        mock_window.acquire()
        
        # Should log the error
        mock_window.logger.error.assert_called()
    
    def test_ui_update_exception_handling(self, mock_window):
        """Test handling of UI update exceptions."""
        # Setup mock to raise exception
        mock_window.connect_button.setText.side_effect = Exception("UI error")
        
        # Should not crash when UI update fails
        mock_window.update_connection_status(True)
        
        # Should still update internal state
        assert mock_window.connected == True


if __name__ == '__main__':
    pytest.main([__file__])
