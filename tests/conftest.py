import pytest
from multiprocessing import Queue

@pytest.fixture
def queues():
    """
    Creates a dictionary of mock queues for testing.
    """
    return {
        "command": Queue(),
        "message": Queue(),
        "data": Queue(),
        "logging": Queue()
    }

import pytest
from multiprocessing import Queue, Process
from src.hp4195a import hp4195a

@pytest.fixture
def managed_backend():
    """
    A fixture that starts and properly terminates the backend process.
    """
    command_queue = Queue()
    message_queue = Queue()
    data_queue = Queue()
    logging_queue = Queue()

    # Setup: Create and start the backend process
    backend_process = hp4195a(command_queue, message_queue, data_queue, logging_queue)
    backend_process.start()

    # Yield the queues to the test
    yield {
        "command": command_queue,
        "message": message_queue,
        "data": data_queue,
        "logging": logging_queue
    }

    # Teardown: This code runs after the test finishes
    print("\nTerminating backend process...")
    backend_process.terminate()
    backend_process.join() # Wait for the process to fully close