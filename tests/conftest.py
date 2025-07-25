# tests/conftest.py

import pytest
from multiprocessing import Queue, Process
import logging

# Import the main window and backend process to be used in fixtures
from src.main_window import MainWindow
from src.hp4195a_interface import HP4195AInterface

@pytest.fixture
def queues():
    """Provides a dictionary of mock queues for testing."""
    queue_dict = {
        "command": Queue(),
        "message": Queue(),
        "data": Queue(),
        "logging": Queue()
    }
    
    yield queue_dict
    
    # Cleanup: Close all queues to prevent resource warnings
    for queue in queue_dict.values():
        queue.close()
        queue.join_thread()

@pytest.fixture
def app(qtbot, queues, mocker):
    """
    A central fixture for UNIT TESTING the GUI in isolation.
    It mocks all background processes (hardware, timers, logging) and
    ensures the window is closed after each test.
    """
    # Mock all external dependencies and background processes
    mocker.patch('src.hp4195a_interface.HP4195AInterface')
    mocker.patch('PyQt5.QtCore.QTimer')
    
    # Mock the QueueHandler and configure its instance to have a valid level
    mock_q_handler = mocker.patch('logging.handlers.QueueHandler')
    mock_q_handler.return_value.level = logging.NOTSET # Set level to 0

    # Create the application instance
    main_app = MainWindow(queues["command"], queues["message"], queues["data"], queues["logging"])
    qtbot.addWidget(main_app)
    
    # Yield the app to the test
    yield main_app
    
    # Teardown: This code runs after the test is complete
    main_app.close()

@pytest.fixture
def managed_backend():
    """
    A fixture for INTEGRATION TESTING that starts and properly terminates
    the real backend process.
    """
    # Setup: Create the queues and the backend process
    command_queue = Queue()
    message_queue = Queue()
    data_queue = Queue()
    logging_queue = Queue()
    
    backend_process = HP4195AInterface(command_queue, message_queue, data_queue, logging_queue)
    backend_process.start()

    # Yield the queues to the test
    queue_dict = {
        "command": command_queue,
        "message": message_queue,
        "data": data_queue,
        "logging": logging_queue
    }
    
    yield queue_dict

    # Teardown: This code runs after the test finishes
    print("\nTerminating backend process...")
    backend_process.terminate()
    backend_process.join() # Wait for the process to fully close
    
    # Cleanup: Close all queues to prevent resource warnings
    for queue in queue_dict.values():
        queue.close()
        queue.join_thread()
