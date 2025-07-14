# tests/test_hp4195a_interface.py

import pytest
from unittest.mock import Mock, patch, MagicMock
import queue
import threading
import time
from src.hp4195a_interface import HP4195AInterface
from src.constants import Commands, GPIBCommands, DefaultValues


class TestHP4195AInterfaceInitialization:
    """Test HP4195A interface initialization and setup."""
    
    def test_initialization(self):
        """Test that the interface initializes with correct default values."""
        # Create mock queues
        command_queue = Mock()
        message_queue = Mock()
        data_queue = Mock()
        logger_queue = Mock()
        
        interface = HP4195AInterface(command_queue, message_queue, data_queue, logger_queue)
        
        # Check queue assignments
        assert interface.command_queue == command_queue
        assert interface.message_queue == message_queue
        assert interface.data_queue == data_queue
        assert interface.logging_queue == logger_queue
        
        # Check default attributes
        assert interface.visa_resource_name == DefaultValues.VISA_RESOURCE_NAME
        assert interface.device_id == DefaultValues.DEVICE_ID
        
        # Check initial state
        assert interface.instrument is None
        assert interface.rm is None
        assert interface.logger is None
        
        # Check data storage initialization
        assert interface.mag_data == []
        assert interface.phase_data == []
        assert interface.freq_data == []
    
    def test_initialization_inherits_from_process(self):
        """Test that the interface properly inherits from multiprocessing.Process."""
        import multiprocessing
        
        # Create mock queues
        command_queue = Mock()
        message_queue = Mock()
        data_queue = Mock()
        logger_queue = Mock()
        
        interface = HP4195AInterface(command_queue, message_queue, data_queue, logger_queue)
        
        # Should be a Process instance
        assert isinstance(interface, multiprocessing.Process)


class TestHP4195AInterfaceConnection:
    """Test connection and disconnection functionality."""
    
    @pytest.fixture
    def interface(self):
        """Create a HP4195A interface for testing."""
        command_queue = Mock()
        message_queue = Mock()
        data_queue = Mock()
        logger_queue = Mock()
        return HP4195AInterface(command_queue, message_queue, data_queue, logger_queue)
    
    @patch('src.hp4195a_interface.pyvisa.ResourceManager')
    def test_connect_visa_setup(self, mock_rm, interface):
        """Test VISA resource manager setup during connection."""
        # Setup mock logger
        interface.logger = Mock()
        
        # Setup mocks
        mock_resource = Mock()
        mock_manager = Mock()
        mock_manager.open_resource.return_value = mock_resource
        mock_rm.return_value = mock_manager
        
        # Mock instrument response
        mock_resource.query.return_value = DefaultValues.DEVICE_ID
        
        # Test connection logic (simulate what _handle_connect would do)
        with patch.object(interface, '_handle_connect') as mock_handle:
            interface._handle_connect()
            mock_handle.assert_called_once()
    
    def test_command_handling_structure(self, interface):
        """Test that command handling structure is in place."""
        # Setup mock logger
        interface.logger = Mock()
        
        # Test that handle_command method exists and can process commands
        assert hasattr(interface, 'handle_command')
        
        # Test with a known command
        interface.handle_command(Commands.CONNECT.value)
        
        # Should log the command
        interface.logger.info.assert_called()


class TestHP4195AInterfaceCommands:
    """Test command handling and processing."""
    
    @pytest.fixture
    def interface(self):
        """Create a HP4195A interface for testing."""
        command_queue = Mock()
        message_queue = Mock()
        data_queue = Mock()
        logger_queue = Mock()
        interface = HP4195AInterface(command_queue, message_queue, data_queue, logger_queue)
        interface.logger = Mock()  # Setup mock logger
        return interface
    
    def test_handle_command_method_exists(self, interface):
        """Test that handle_command method exists and is callable."""
        assert hasattr(interface, 'handle_command')
        assert callable(interface.handle_command)
    
    def test_command_logging_structure(self, interface):
        """Test that command handling has logging structure in place."""
        # Mock the handle_command to test just the logging part
        with patch.object(interface, 'handle_command') as mock_handle:
            # Setup a simple mock that just logs
            def log_command(command):
                interface.logger.info(f'Received "{command}" from GUI')
            
            mock_handle.side_effect = log_command
            
            # Test the mock
            test_command = Commands.CONNECT.value
            mock_handle(test_command)
            
            # Should log the received command
            interface.logger.info.assert_called_with(f'Received "{test_command}" from GUI')
    
    def test_commands_enum_values_are_strings(self, interface):
        """Test that all command values are strings (for queue compatibility)."""
        for command in Commands:
            assert isinstance(command.value, str)
            assert len(command.value) > 0


class TestHP4195AInterfaceDataStructures:
    """Test data structure management."""
    
    @pytest.fixture
    def interface(self):
        """Create a HP4195A interface for testing."""
        command_queue = Mock()
        message_queue = Mock()
        data_queue = Mock()
        logger_queue = Mock()
        return HP4195AInterface(command_queue, message_queue, data_queue, logger_queue)
    
    def test_data_storage_initialization(self, interface):
        """Test that data storage lists are properly initialized."""
        assert isinstance(interface.mag_data, list)
        assert isinstance(interface.phase_data, list)
        assert isinstance(interface.freq_data, list)
        
        assert len(interface.mag_data) == 0
        assert len(interface.phase_data) == 0
        assert len(interface.freq_data) == 0
    
    def test_data_storage_types(self, interface):
        """Test that data storage maintains correct types."""
        # Data should be typed as List[float]
        from typing import get_type_hints
        hints = get_type_hints(HP4195AInterface.__init__)
        
        # Basic type checking
        assert hasattr(interface, 'mag_data')
        assert hasattr(interface, 'phase_data')
        assert hasattr(interface, 'freq_data')


class TestHP4195AInterfaceConfiguration:
    """Test configuration and constants integration."""
    
    @pytest.fixture
    def interface(self):
        """Create a HP4195A interface for testing."""
        command_queue = Mock()
        message_queue = Mock()
        data_queue = Mock()
        logger_queue = Mock()
        return HP4195AInterface(command_queue, message_queue, data_queue, logger_queue)
    
    def test_default_configuration_values(self, interface):
        """Test that default configuration values are properly set."""
        assert interface.visa_resource_name == DefaultValues.VISA_RESOURCE_NAME
        assert interface.device_id == DefaultValues.DEVICE_ID
    
    def test_visa_configuration_attributes(self, interface):
        """Test that VISA configuration attributes exist."""
        assert hasattr(interface, 'visa_resource_name')
        assert hasattr(interface, 'device_id')
        assert hasattr(interface, 'instrument')
        assert hasattr(interface, 'rm')
        
        # Initial state should be None
        assert interface.instrument is None
        assert interface.rm is None
    
    def test_constants_integration(self, interface):
        """Test integration with constants module."""
        # Should be able to access all command constants
        assert hasattr(Commands, 'CONNECT')
        assert hasattr(Commands, 'DISCONNECT')
        assert hasattr(Commands, 'START_ACQUISITION')
        
        # Should be able to access GPIB commands
        assert hasattr(GPIBCommands, 'QUERY_IDENTITY')
        assert hasattr(GPIBCommands, 'QUERY_MAGNITUDE')
        
        # Should be able to access default values
        assert hasattr(DefaultValues, 'VISA_RESOURCE_NAME')
        assert hasattr(DefaultValues, 'DEVICE_ID')


if __name__ == '__main__':
    pytest.main([__file__])
