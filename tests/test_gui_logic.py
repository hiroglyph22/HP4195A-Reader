import pytest
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock
import logging

# Import the main window
from src.main_window import MainWindow

@pytest.fixture
def app(qtbot, queues, mocker):
    """
    Creates the main application window for testing and ensures
    it is properly closed after the test.
    """
    # --- Setup ---
    # Mock all external dependencies and background processes
    mocker.patch('src.hp4195a.hp4195a')
    mocker.patch('PyQt5.QtCore.QTimer')
    
    # --- THIS IS THE FIX ---
    # Mock the QueueHandler and configure its instance to have a valid level
    mock_q_handler = mocker.patch('logging.handlers.QueueHandler')
    mock_q_handler.return_value.level = logging.NOTSET # Set level to 0
    # -----------------------

    # Create the application instance
    main_app = MainWindow(queues["command"], queues["message"], queues["data"], queues["logging"])
    qtbot.addWidget(main_app)
    
    # --- Yield to the test ---
    yield main_app
    
    # --- Teardown ---
    main_app.close()

def test_initial_button_state(app):
    """Tests that control buttons are disabled on startup."""
    assert not app.acquire_button.isEnabled()
    assert not app.power_sweep_button.isEnabled()
    assert not app.peak_scan_button.isEnabled()

def test_connect_enables_buttons(app, queues, qtbot, mocker):
    """Tests if buttons become enabled after clicking 'connect'."""
    # Arrange:
    # --- THIS IS THE FIX ---
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