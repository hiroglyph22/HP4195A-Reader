# tests/test_backend.py

import pytest
import numpy as np
from unittest.mock import MagicMock

# Import the class to be tested
from src.hp4195a import hp4195a

@pytest.fixture
def mock_pyvisa(mocker):
    """Mocks the entire pyvisa library."""
    mock_rm = MagicMock()
    mock_instrument = MagicMock()
    
    mock_instrument.query.return_value = "HP4195A"
    mock_rm.open_resource.return_value = mock_instrument
    
    mocker.patch('pyvisa.ResourceManager', return_value=mock_rm)
    return mock_instrument

def test_set_output_power(queues, mock_pyvisa):
    """
    Tests if the 'set_output_power' command sends the correct GPIB string.
    """
    # Arrange
    backend = hp4195a(queues["command"], queues["message"], queues["data"], queues["logging"])
    backend.instrument = mock_pyvisa
    
    # Act
    test_power = -10.5
    queues["command"].put('set_output_power')
    queues["command"].put(test_power)
    
    command = queues["command"].get()
    # You will need to refactor your backend to have a testable handle_command method
    # backend.handle_command(command) 

    # Assert
    # mock_pyvisa.write.assert_called_once_with(f"OSCPWR = {test_power} DB")
    # assert queues["message"].get() is True
    pass # Placeholder until backend is refactored for testing

def test_data_acquisition(queues, mock_pyvisa):
    """
    Tests if the 'start_acquisition' command correctly queries the instrument
    and puts the data on the queues.
    """
    # Arrange
    backend = hp4195a(queues["command"], queues["message"], queues["data"], queues["logging"])
    backend.instrument = mock_pyvisa
    
    fake_mag_data = "1.0,2.0,3.0"
    fake_phase_data = "90.0,85.0,80.0"
    fake_freq_data = "1000,2000,3000"
    mock_pyvisa.query.side_effect = [fake_mag_data, fake_phase_data, fake_freq_data]

    # Act
    queues["command"].put('start_acquisition')
    # command = queues["command"].get()
    # backend.handle_command(command)

    # Assert
    # assert queues["message"].get() is True
    pass # Placeholder