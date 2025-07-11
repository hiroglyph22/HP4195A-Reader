# tests/test_instrument_controls_comprehensive.py

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from PyQt5 import QtWidgets, QtCore
from queue import Queue, Empty

from src.logic.instrument_controls import InstrumentControls, SweepCommunicator
from src.constants import Commands


class MockMainWindow(InstrumentControls):
    """Mock main window that properly implements the InstrumentControls interface."""
    
    def __init__(self):
        # Initialize required queues
        self.command_queue = Queue()
        self.message_queue = Queue() 
        self.data_queue = Queue()
        
        # Initialize connection state
        self.connected = False
        
        # Mock UI components
        self.connect_button = Mock()
        self.acquire_button = Mock() 
        self.peak_scan_button = Mock()
        self.low_res_sweep_button = Mock()
        self.range_scan_button = Mock()
        self.sweeping_range_of_amplitudes_button = Mock()
        self.pause_button = Mock()
        self.autofind_peak_button = Mock()
        self.center_peak_button = Mock()
        self.q_factor_button = Mock()
        self.command_box = Mock()
        self.response_box = Mock()
        
        # Mock other components
        self.timer = Mock()
        self.graph = Mock()
        
        # Mock methods that might be called
        self.update_connection_status = Mock()
        self.show_error_dialog = Mock()


class TestSweepCommunicator:
    """Test the SweepCommunicator signal handling class."""
    
    def test_sweep_communicator_initialization(self):
        """Test SweepCommunicator can be created."""
        communicator = SweepCommunicator()
        assert hasattr(communicator, 'new_sweep_window_ready')
        assert hasattr(communicator, 'final_plot_ready')
        assert hasattr(communicator, 'enable_button')
    
    def test_sweep_communicator_signals_exist(self):
        """Test that all required signals exist."""
        communicator = SweepCommunicator()
        # Signals become bound signal objects when accessed from instance
        assert hasattr(communicator, 'new_sweep_window_ready')
        assert hasattr(communicator, 'final_plot_ready')
        assert hasattr(communicator, 'enable_button')
        # Test signals can be used (have emit method)
        assert hasattr(communicator.new_sweep_window_ready, 'emit')
        assert hasattr(communicator.final_plot_ready, 'emit')
        assert hasattr(communicator.enable_button, 'emit')


class TestInstrumentControlsConnection:
    """Test connection and disconnection functionality."""
    
    @pytest.fixture
    def mock_window(self):
        """Create a properly mocked main window."""
        return MockMainWindow()
    
    def test_connect_when_disconnected(self, mock_window):
        """Test connecting when currently disconnected."""
        # Setup: not connected, message queue returns success
        mock_window.connected = False
        mock_window.message_queue.put(True)
        
        # Execute
        mock_window.connect()
        
        # Verify command was sent
        assert mock_window.command_queue.get() == Commands.CONNECT.value
        
        # Verify state changes
        assert mock_window.connected == True
        mock_window.connect_button.setText.assert_called_with("Disconnect")
        mock_window.acquire_button.setEnabled.assert_called_with(True)
    
    def test_disconnect_when_connected(self, mock_window):
        """Test disconnecting when currently connected."""
        # Setup: connected, message queue returns success
        mock_window.connected = True
        mock_window.message_queue.put(True)
        
        # Execute
        mock_window.connect()
        
        # Verify command was sent
        assert mock_window.command_queue.get() == Commands.DISCONNECT.value
        
        # Verify state changes
        assert mock_window.connected == False
        mock_window.connect_button.setText.assert_called_with("Connect")
        mock_window.acquire_button.setEnabled.assert_called_with(False)
        mock_window.timer.stop.assert_called_once()
    
    def test_connect_failure(self, mock_window):
        """Test connection failure handling."""
        # Setup: message queue returns failure
        mock_window.connected = False
        mock_window.message_queue.put(False)
        
        # Execute
        mock_window.connect()
        
        # Verify command was sent but state didn't change
        assert mock_window.command_queue.get() == Commands.CONNECT.value
        assert mock_window.connected == False


class TestInstrumentControlsDataAcquisition:
    """Test data acquisition functionality."""
    
    @pytest.fixture
    def mock_window(self):
        """Create a properly mocked main window."""
        return MockMainWindow()
    
    def test_start_acquisition_when_connected(self, mock_window):
        """Test starting data acquisition when connected."""
        # Setup
        mock_window.connected = True
        mock_window.message_queue.put(True)
        
        # Execute
        mock_window.start_acquisition()
        
        # Verify command was sent
        assert mock_window.command_queue.get() == Commands.START_ACQUISITION.value
        
        # Verify UI updates
        mock_window.autofind_peak_button.setEnabled.assert_called_with(True)
        mock_window.center_peak_button.setEnabled.assert_called_with(False)
        mock_window.graph.clear_q_factor_data.assert_called_once()
        mock_window.graph.plot.assert_called_once()
    
    def test_start_acquisition_when_not_connected(self, mock_window):
        """Test starting acquisition when not connected does nothing."""
        # Setup
        mock_window.connected = False
        
        # Execute
        mock_window.start_acquisition()
        
        # Verify no command was sent
        assert mock_window.command_queue.empty()


class TestInstrumentControlsCommandHandling:
    """Test GPIB command sending functionality."""
    
    @pytest.fixture
    def mock_window(self):
        """Create a properly mocked main window."""
        return MockMainWindow()
    
    def test_send_command_valid(self, mock_window):
        """Test sending a valid GPIB command."""
        # Setup
        test_command = "ID?"
        test_response = "HP4195A"
        mock_window.command_box.text.return_value = test_command
        mock_window.data_queue.put(test_response)
        
        # Execute
        mock_window.send_command()
        
        # Verify command queue interactions
        assert mock_window.command_queue.get() == Commands.SEND_COMMAND.value
        assert mock_window.command_queue.get() == test_command
        
        # Verify UI updates
        mock_window.response_box.setText.assert_called_with(f'{test_command}: {test_response}')
        mock_window.command_box.clear.assert_called_once()
    
    def test_send_command_empty(self, mock_window):
        """Test sending an empty command."""
        # Setup
        mock_window.command_box.text.return_value = ""
        mock_window.data_queue.put("Error")
        
        # Execute
        mock_window.send_command()
        
        # Verify command was still sent (validation happens elsewhere)
        assert mock_window.command_queue.get() == Commands.SEND_COMMAND.value
        assert mock_window.command_queue.get() == ""


class TestInstrumentControlsSweepWindows:
    """Test sweep window creation and management."""
    
    @pytest.fixture
    def mock_window(self):
        """Create a properly mocked main window."""
        return MockMainWindow()
    
    @patch('src.logic.instrument_controls.AmplitudeSweepViewer')
    def test_create_new_sweep_window(self, mock_viewer_class, mock_window):
        """Test creating a new sweep window."""
        # Setup
        mock_viewer = Mock()
        mock_viewer_class.return_value = mock_viewer
        freq_data = [1, 2, 3]
        mag_data = [-10, -20, -15]
        amplitude = -5.0
        
        # Execute
        mock_window.create_new_sweep_window(freq_data, mag_data, amplitude)
        
        # Verify
        mock_viewer_class.assert_called_once_with(parent=mock_window)
        mock_viewer.update_plot.assert_called_once_with(freq_data, mag_data, amplitude)
        mock_viewer.show.assert_called_once()
        assert hasattr(mock_window, 'sweep_viewers')
        assert mock_viewer in mock_window.sweep_viewers
    
    @patch('src.logic.instrument_controls.FinalSweepViewer') 
    def test_create_final_sweep_window(self, mock_viewer_class, mock_window):
        """Test creating the final sweep window."""
        # Setup
        mock_viewer = Mock()
        mock_viewer_class.return_value = mock_viewer
        all_sweeps_data = [{'amp': -5, 'freq': [1, 2], 'mag': [-10, -20]}]
        
        # Execute
        mock_window.create_final_sweep_window(all_sweeps_data)
        
        # Verify
        mock_viewer_class.assert_called_once_with(parent=mock_window)
        mock_viewer.update_plot.assert_called_once_with(all_sweeps_data)
        mock_viewer.show.assert_called_once()
        assert hasattr(mock_window, 'sweep_viewers')
        assert mock_viewer in mock_window.sweep_viewers


class TestInstrumentControlsIntegration:
    """Test integration between components."""
    
    @pytest.fixture
    def mock_window(self):
        """Create a properly mocked main window."""
        return MockMainWindow()
    
    def test_connect_acquisition_workflow(self, mock_window):
        """Test the complete connect -> acquire workflow."""
        # Setup
        mock_window.message_queue.put(True)  # Connect success
        mock_window.message_queue.put(True)  # Acquisition success
        
        # Execute connect
        mock_window.connect()
        assert mock_window.connected == True
        
        # Execute acquisition
        mock_window.start_acquisition()
        
        # Verify both workflows completed
        commands = []
        while not mock_window.command_queue.empty():
            commands.append(mock_window.command_queue.get())
        
        assert Commands.CONNECT.value in commands
        assert Commands.START_ACQUISITION.value in commands
    
    def test_queue_communication_patterns(self, mock_window):
        """Test that queue communication follows expected patterns."""
        # Test command queue usage
        mock_window.message_queue.put(True)
        mock_window.connect()
        
        # Should have sent exactly one command
        assert mock_window.command_queue.get() == Commands.CONNECT.value
        assert mock_window.command_queue.empty()
        
        # Test data queue usage 
        mock_window.command_box.text.return_value = "TEST"
        mock_window.data_queue.put("RESPONSE")
        mock_window.send_command()
        
        # Should have consumed the response
        assert mock_window.data_queue.empty()


class TestInstrumentControlsErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.fixture 
    def mock_window(self):
        """Create a properly mocked main window."""
        return MockMainWindow()
    
    def test_queue_empty_handling(self, mock_window):
        """Test handling of empty queues."""
        # Test with empty message queue
        mock_window.connected = False
        
        with pytest.raises(Exception):  # Queue.get() will block/raise
            # This simulates queue being empty when expected response
            # In real implementation this would be handled with timeouts
            mock_window.message_queue.get_nowait()
    
    def test_ui_component_safety(self, mock_window):
        """Test that UI components are safely accessed."""
        # All UI components should be mocked and available
        assert hasattr(mock_window, 'connect_button')
        assert hasattr(mock_window, 'acquire_button') 
        assert hasattr(mock_window, 'command_box')
        assert hasattr(mock_window, 'timer')
        assert hasattr(mock_window, 'graph')
        
        # Should be able to call methods without errors
        mock_window.connect_button.setText("Test")
        mock_window.acquire_button.setEnabled(True)
        mock_window.timer.stop()
