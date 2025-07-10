import pytest
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock
import logging

# Import the main window
from src.main_window import MainWindow

def test_initial_button_state(app):
    """Tests that control buttons are disabled on startup."""
    assert not app.acquire_button.isEnabled()
    assert not app.power_sweep_button.isEnabled()
    assert not app.peak_scan_button.isEnabled()

def test_connect_enables_buttons(app, queues, qtbot, mocker):
    """Tests if buttons become enabled after clicking 'connect'."""
    # Arrange:
    # Intercept the call to message_queue.get() and make it return True instantly.
    mocker.patch.object(queues["message"], 'get', return_value=True)
    
    # Act: Simulate a user clicking the connect button.
    qtbot.mouseClick(app.connect_button, Qt.LeftButton)
    
    # Assert: Check that the buttons are now enabled.
    assert app.acquire_button.isEnabled()
    assert app.power_sweep_button.isEnabled()
    assert app.connect_button.text() == "Disconnect"

# def test_power_sweep_sends_command(app, queues, qtbot, mocker):
#     """
#     Tests if clicking 'Start Power Sweep' sends the correct command.
#     """
#     # Arrange: First, connect the application to enable the button.
#     # We use the same mock to prevent the connect call from blocking.
#     mocker.patch.object(queues["message"], 'get', return_value=True)
#     qtbot.mouseClick(app.connect_button, Qt.LeftButton)
    
#     # Set the input values for the power sweep.
#     app.start_power_input.setText("-10")
#     app.stop_power_input.setText("0")
#     app.step_power_input.setText("5")
    
#     # Mock the file dialog to prevent it from actually opening.
#     mocker.patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory', return_value="/fake/directory")
    
#     # Act: Simulate a user clicking the power sweep button.
#     qtbot.mouseClick(app.power_sweep_button, Qt.LeftButton)
    
#     # Assert: Check that the correct commands were sent to the backend.
#     assert queues["command"].get() == 'start_power_sweep'
    
#     expected_params = {
#         "start": -10.0,
#         "stop": 0.0,
#         "step": 5.0,
#         "dir": "/fake/directory"
#     }
#     assert queues["command"].get() == expected_params