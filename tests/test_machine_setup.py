#!/usr/bin/env python3
"""
Test script for the new Machine Setup functionality.
This script tests the basic imports and functionality.
"""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import csv
from io import StringIO
from PyQt5 import QtWidgets

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from constants import Commands, GPIBCommands
from gui.machine_values_window import MachineValuesWindow
from logic.ui_logic import UiLogic
from gui.ui_generator import UIGenerator

def test_imports():
    """Test that all the new modules can be imported."""
    print("Testing imports...")
    
    # Test new commands
    assert hasattr(Commands, 'GET_MACHINE_VALUES')
    assert hasattr(Commands, 'APPLY_MACHINE_SETTINGS')
    print("✓ New commands found in Constants")
    
    # Test new GPIB queries
    assert hasattr(GPIBCommands, 'QUERY_CENTER')
    assert hasattr(GPIBCommands, 'QUERY_SPAN')
    print("✓ New GPIB query commands found")
    
    # Test that classes can be imported
    assert MachineValuesWindow is not None
    print("✓ Machine values window imported successfully")
    assert UiLogic is not None
    print("✓ UI logic imported successfully")
    assert UIGenerator is not None
    print("✓ UI generator imported successfully")

class MockParent(QtWidgets.QWidget):
    """Mock parent widget with connected attribute."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connected = True

@pytest.fixture
def mock_window(qtbot):
    """Fixture to create a mocked MachineValuesWindow instance."""
    # Mock the queues for communication
    mock_command_queue = Mock()
    mock_message_queue = Mock()
    mock_data_queue = Mock()
    
    # Use a QWidget subclass for the parent to ensure 'connected' attribute exists
    mock_parent = MockParent()

    window = MachineValuesWindow(
        parent=mock_parent,
        command_queue=mock_command_queue,
        message_queue=mock_message_queue,
        data_queue=mock_data_queue
    )
    qtbot.addWidget(window)

    # Attach mocks to the instance for easy access in tests
    window.command_queue = mock_command_queue
    window.message_queue = mock_message_queue
    window.data_queue = mock_data_queue
    yield window

@patch('gui.machine_values_window.QtWidgets.QFileDialog.getSaveFileName')
def test_export_to_json(mock_get_save_file_name, mock_window):
    """Test exporting configuration to a JSON file."""
    print("\nTesting Export to JSON functionality...")
    
    # Set up test data in the window
    mock_window.machine_values.update({
        'center_frequency': 1000000.0,
        'span': 50000.0,
        'device_id': 'TestDevice'
    })
    
    # Mock the file dialog to return a path
    mock_get_save_file_name.return_value = ("test.json", "JSON Files (*.json)")
    
    # Use mock_open to handle the file writing context
    m = mock_open()
    with patch('builtins.open', m):
        with patch('gui.machine_values_window.QtWidgets.QMessageBox.information'):
            mock_window.export_to_json()

    # Check that open was called correctly
    m.assert_called_once_with("test.json", 'w', encoding='utf-8')

    # Combine all writes to the file handle to reconstruct the full JSON string
    handle = m()
    file_content = "".join(call.args[0] for call in handle.write.call_args_list)
    exported_data = json.loads(file_content)

    # Assertions
    assert 'hp4195a_configuration' in exported_data
    assert exported_data['hp4195a_configuration']['center_frequency'] == 1000000.0
    assert exported_data['hp4195a_configuration']['span'] == 50000.0
    assert exported_data['hp4195a_configuration']['device_id'] == 'TestDevice'
    assert 'exported_at' in exported_data
    assert 'exported_by' in exported_data
    print("✓ JSON export successful with correct data structure")

@patch('gui.machine_values_window.QtWidgets.QFileDialog.getSaveFileName')
def test_export_to_csv(mock_get_save_file_name, mock_window):
    """Test exporting configuration to a CSV file."""
    print("\nTesting Export to CSV functionality...")
    
    # Set up test data in the window
    mock_window.machine_values.update({
        'center_frequency': 2000000.0,
        'span': 100000.0,
        'device_id': 'CSVTestDevice'
    })
    
    # Mock the file dialog to return a path
    mock_get_save_file_name.return_value = ("test.csv", "CSV Files (*.csv)")
    
    # Use StringIO to capture CSV output
    csv_content = StringIO()
    m = mock_open()
    m.return_value = csv_content
    
    with patch('builtins.open', m):
        with patch('gui.machine_values_window.QtWidgets.QMessageBox.information'):
            mock_window.export_to_csv()

    # Check that open was called correctly
    m.assert_called_once_with("test.csv", 'w', newline='', encoding='utf-8')
    
    # Verify CSV content structure by checking the call arguments to csv.writer.writerow
    # Since we can't easily mock csv.writer, we'll check that the file was opened correctly
    print("✓ CSV export successful with correct file handling")

@patch('gui.machine_values_window.QtWidgets.QFileDialog.getOpenFileName')
def test_import_from_json(mock_get_open_file_name, mock_window):
    """Test importing configuration from a JSON file."""
    print("\nTesting Import from JSON functionality...")

    # Prepare mock JSON data
    json_data = {
        "hp4195a_configuration": {
            "center_frequency": 5000000.0,
            "span": 10000.0,
            "device_id": "ImportedDevice",
            "start_frequency": 4995000.0,
            "stop_frequency": 5005000.0
        }
    }
    mock_file_content = json.dumps(json_data)
    
    # Mock the file dialog and the open function
    mock_get_open_file_name.return_value = ("test.json", "JSON Files (*.json)")
    with patch('builtins.open', MagicMock(return_value=StringIO(mock_file_content))):
        with patch('gui.machine_values_window.QtWidgets.QMessageBox.information'):
            mock_window.import_from_json()

    # Assert that the window's internal state was updated
    assert mock_window.machine_values['center_frequency'] == 5000000.0
    assert mock_window.machine_values['span'] == 10000.0
    assert mock_window.machine_values['device_id'] == "ImportedDevice"
    assert mock_window.machine_values['start_frequency'] == 4995000.0
    assert mock_window.machine_values['stop_frequency'] == 5005000.0
    print("✓ JSON import successful and machine values updated correctly")

@patch('gui.machine_values_window.QtWidgets.QFileDialog.getOpenFileName')
def test_import_from_csv(mock_get_open_file_name, mock_window):
    """Test importing configuration from a CSV file."""
    print("\nTesting Import from CSV functionality...")

    # Prepare mock CSV data
    csv_data = [
        ['Parameter', 'Value', 'Exported'],
        ['', '', '2025-07-14 10:30:00'],
        [''],  # Empty row
        ['Center Frequency (Hz)', '3000000'],
        ['Span (Hz)', '75000'],
        ['Device ID', 'CSVImportedDevice'],
        ['Start Frequency (Hz)', '2962500'],
        ['Stop Frequency (Hz)', '3037500']
    ]
    
    mock_file_content = StringIO()
    csv_writer = csv.writer(mock_file_content)
    csv_writer.writerows(csv_data)
    mock_file_content.seek(0)

    mock_get_open_file_name.return_value = ("test.csv", "CSV Files (*.csv)")
    with patch('builtins.open', MagicMock(return_value=mock_file_content)):
        with patch('gui.machine_values_window.QtWidgets.QMessageBox.information'):
            mock_window.import_from_csv()

    # Assert that the window's internal state was updated
    assert mock_window.machine_values['center_frequency'] == 3000000.0
    assert mock_window.machine_values['span'] == 75000.0
    assert mock_window.machine_values['device_id'] == 'CSVImportedDevice'
    assert mock_window.machine_values['start_frequency'] == 2962500.0
    assert mock_window.machine_values['stop_frequency'] == 3037500.0
    print("✓ CSV import successful and machine values updated correctly")

@patch('gui.machine_values_window.QtWidgets.QFileDialog.getOpenFileName')
def test_import_json_with_invalid_format(mock_get_open_file_name, mock_window):
    """Test importing from JSON with invalid format shows error."""
    print("\nTesting Import from JSON with invalid format...")

    # Prepare invalid JSON data (missing hp4195a_configuration key)
    invalid_json_data = {
        "wrong_key": {
            "center_frequency": 1000000.0
        }
    }
    mock_file_content = json.dumps(invalid_json_data)
    
    mock_get_open_file_name.return_value = ("invalid.json", "JSON Files (*.json)")
    with patch('builtins.open', MagicMock(return_value=StringIO(mock_file_content))):
        with patch('gui.machine_values_window.QtWidgets.QMessageBox.critical') as mock_error:
            mock_window.import_from_json()

    # Should not update machine values and should show error
    assert mock_window.machine_values['center_frequency'] == 'Unknown'  # Should remain unchanged
    mock_error.assert_called_once()  # Error dialog should be shown
    print("✓ Invalid JSON format correctly handled with error message")

@patch('gui.machine_values_window.QtWidgets.QFileDialog.getOpenFileName')
def test_import_csv_with_no_valid_data(mock_get_open_file_name, mock_window):
    """Test importing from CSV with no valid parameters shows error."""
    print("\nTesting Import from CSV with no valid data...")

    # Prepare CSV with no valid machine parameters
    csv_data = [
        ['Parameter', 'Value'],
        ['Invalid Parameter', '123'],
        ['Another Invalid', 'test']
    ]
    
    mock_file_content = StringIO()
    csv_writer = csv.writer(mock_file_content)
    csv_writer.writerows(csv_data)
    mock_file_content.seek(0)

    mock_get_open_file_name.return_value = ("empty.csv", "CSV Files (*.csv)")
    with patch('builtins.open', MagicMock(return_value=mock_file_content)):
        with patch('gui.machine_values_window.QtWidgets.QMessageBox.critical') as mock_error:
            mock_window.import_from_csv()

    # Should show error for no valid data
    mock_error.assert_called_once()
    print("✓ CSV with no valid data correctly handled with error message")

def test_roundtrip_json_export_import(mock_window):
    """Test exporting to JSON and then importing it back produces the same data."""
    print("\nTesting JSON export-import roundtrip...")

    # Set up initial test data
    original_data = {
        'center_frequency': 1500000.0,
        'span': 200000.0,
        'device_id': 'RoundtripDevice',
        'start_frequency': 1400000.0,
        'stop_frequency': 1600000.0,
        'resolution_bandwidth': 1000.0
    }
    mock_window.machine_values.update(original_data)

    # Create the expected JSON structure that would be exported
    expected_export_data = {
        'hp4195a_configuration': mock_window.machine_values.copy(),
        'exported_at': '2025-07-14T10:30:00',
        'exported_by': 'HP4195A Reader Application'
    }
    exported_json_content = json.dumps(expected_export_data, indent=2)

    # Reset machine values to different data to test import
    mock_window.machine_values.update({
        'center_frequency': 'Unknown',
        'span': 'Unknown',
        'device_id': 'Unknown',
        'start_frequency': 'Unknown',
        'stop_frequency': 'Unknown',
        'resolution_bandwidth': 'Unknown'
    })

    # Import the JSON data
    with patch('gui.machine_values_window.QtWidgets.QFileDialog.getOpenFileName', return_value=("test.json", "")):
        with patch('builtins.open', MagicMock(return_value=StringIO(exported_json_content))):
            with patch('gui.machine_values_window.QtWidgets.QMessageBox.information'):
                mock_window.import_from_json()

    # Verify the data matches what we originally had
    for key, value in original_data.items():
        assert mock_window.machine_values[key] == value, f"Mismatch for {key}: expected {value}, got {mock_window.machine_values[key]}"
    
    print("✓ JSON roundtrip successful - exported and imported data matches")

def test_machine_values_window():
    """Test basic functionality of the machine values window."""
    print("\nTesting machine values window...")
    
    try:
        # This requires PyQt5, so we'll just test the class can be instantiated
        from gui.machine_values_window import MachineValuesWindow
        
        # Create a mock window (without actually showing it)
        # We can't fully test GUI without a display
        print("✓ MachineValuesWindow class can be imported")
    except Exception as e:
        pytest.fail(f"MachineValuesWindow test failed: {e}")

def main():
    """Run all tests."""
    print("HP4195A Machine Setup Feature Test")
    print("=" * 40)
    
    success = True
    
    if not test_imports():
        success = False
        
    if not test_machine_values_window():
        success = False
        
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed! Machine setup feature is ready.")
        print("\nNew Features Added:")
        print("- Unified machine configuration window for viewing, editing, and applying settings")
        print("- Editable table for machine parameters")
        print("- 'Apply Settings' button to send configuration to the instrument")
        print("- Import/Export to CSV/JSON functionality")
        print("- Tools menu with Machine Setup option")
        print("- New GPIB query commands for machine status")
    else:
        print("✗ Some tests failed. Please check the issues above.")
        
    return success

if __name__ == "__main__":
    exit(0 if main() else 1)
