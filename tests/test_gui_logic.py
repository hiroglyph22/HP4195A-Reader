import pytest
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock
import logging

# Import the main window
from src.main_window import MainWindow

def test_initial_button_state(app):
    """Tests that control buttons are disabled on startup."""
    assert not app.acquire_button.isEnabled()
    assert not app.sweeping_range_of_amplitudes_button.isEnabled()
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
    assert app.sweeping_range_of_amplitudes_button.isEnabled()
    assert app.connect_button.text() == "Disconnect"
