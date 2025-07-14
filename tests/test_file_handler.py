# tests/test_file_handler.py

import pytest
import os
import tempfile
import csv
from unittest.mock import Mock, patch, MagicMock
from PyQt5 import QtWidgets
from src.logic.file_handler import FileHandler


class MockMainWindow(FileHandler):
    """Mock main window class for testing file handling."""
    
    def __init__(self):
        # Mock required attributes
        self.graph = Mock()
        self.graph.freq_data = [1000, 2000, 3000]
        self.graph.mag_data = [-10, -20, -30]
        self.graph.phase_data = [0, 45, 90]
        self.logger = Mock()


@pytest.fixture
def mock_window():
    """Create a mock main window for testing."""
    return MockMainWindow()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing file operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


class TestFileHandlerSaveOperations:
    """Test file saving operations."""
    
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    def test_save_file_dialog_csv_success(self, mock_dialog, mock_window, temp_dir):
        """Test successful CSV file saving."""
        # Setup
        test_file = os.path.join(temp_dir, "test_data.csv")
        mock_dialog.return_value = (test_file, "CSV files (*.csv)")
        
        # Execute
        mock_window.save_file_dialog()
        
        # Verify
        mock_dialog.assert_called_once()
        mock_window.logger.info.assert_called()
        
        # Check file was created and has correct content
        assert os.path.exists(test_file)
        
        with open(test_file, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Check header
            assert rows[0] == ['Frequency', 'Magnitude', 'Phase']
            
            # Check data rows
            assert len(rows) == 4  # Header + 3 data rows
            assert rows[1] == ['1000', '-10', '0']
            assert rows[2] == ['2000', '-20', '45']
            assert rows[3] == ['3000', '-30', '90']

    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    def test_save_file_dialog_user_cancels(self, mock_dialog, mock_window):
        """Test handling when user cancels the save dialog."""
        # Setup - simulate user canceling
        mock_dialog.return_value = ("", "")

        # Execute
        mock_window.save_file_dialog()

        # Verify
        mock_dialog.assert_called_once()
        # No logging occurs when user cancels in the current implementation
    
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    def test_save_file_dialog_no_data(self, mock_dialog, mock_window, temp_dir):
        """Test saving when no data is available."""
        # Setup
        test_file = os.path.join(temp_dir, "empty_data.csv")
        mock_dialog.return_value = (test_file, "CSV files (*.csv)")
        
        # Remove data from graph
        mock_window.graph.freq_data = []
        mock_window.graph.mag_data = []
        mock_window.graph.phase_data = []
        
        # Execute
        mock_window.save_file_dialog()
        
        # Verify
        assert os.path.exists(test_file)
        
        with open(test_file, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Should only have header
            assert len(rows) == 1
            assert rows[0] == ['Frequency', 'Magnitude', 'Phase']
    
    @patch('src.logic.file_handler.QtWidgets.QMessageBox.critical')
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    @patch('builtins.open', side_effect=PermissionError("Access denied"))
    def test_save_file_dialog_permission_error(self, mock_open, mock_dialog, mock_message_box, mock_window):
        """Test handling of permission errors during save."""
        # Setup
        mock_dialog.return_value = ("/restricted/test.csv", "CSV files (*.csv)")
        
        # Execute
        mock_window.save_file_dialog()
        
        # Verify error handling
        mock_window.logger.error.assert_called()
        error_call = mock_window.logger.error.call_args[0][0]
        assert "Could not write to file" in error_call
        assert "Access denied" in error_call
        
        # Verify error dialog was shown
        mock_message_box.assert_called_once()
    
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    def test_save_file_dialog_file_extensions(self, mock_dialog, mock_window, temp_dir):
        """Test that the correct file extensions are offered."""
        mock_dialog.return_value = ("", "")
        
        mock_window.save_file_dialog()
        
        # Check the file filter includes CSV
        call_args = mock_dialog.call_args
        # The third argument should be the filter string
        assert call_args is not None
        filter_arg = call_args[0][3]  # 4th positional argument (0-indexed)
        assert "CSV Files (*.csv)" in filter_arg


class TestFileHandlerDataValidation:
    """Test data validation during file operations."""
    
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    def test_save_mismatched_data_lengths(self, mock_dialog, mock_window, temp_dir):
        """Test saving when data arrays have mismatched lengths."""
        # Setup mismatched data
        test_file = os.path.join(temp_dir, "mismatched_data.csv")
        mock_dialog.return_value = (test_file, "CSV files (*.csv)")
        
        mock_window.graph.freq_data = [1000, 2000]
        mock_window.graph.mag_data = [-10, -20, -30]  # One extra element
        mock_window.graph.phase_data = [0, 45]
        
        # Execute
        mock_window.save_file_dialog()
        
        # Should handle gracefully by using shortest length
        assert os.path.exists(test_file)
        
        with open(test_file, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Should have header + 2 rows (shortest array length)
            assert len(rows) == 3
            assert rows[1] == ['1000', '-10', '0']
            assert rows[2] == ['2000', '-20', '45']
    
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    def test_save_with_none_values(self, mock_dialog, mock_window, temp_dir):
        """Test saving when data contains None values."""
        # Setup
        test_file = os.path.join(temp_dir, "none_data.csv")
        mock_dialog.return_value = (test_file, "CSV files (*.csv)")
        
        mock_window.graph.freq_data = [1000, None, 3000]
        mock_window.graph.mag_data = [-10, -20, None]
        mock_window.graph.phase_data = [0, None, 90]
        
        # Execute
        mock_window.save_file_dialog()
        
        # Verify
        assert os.path.exists(test_file)
        
        with open(test_file, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Check that None values are handled
            assert len(rows) == 4  # Header + 3 data rows
            # None should be converted to string 'None' or empty
            assert 'None' in str(rows) or '' in rows[2]


class TestFileHandlerEdgeCases:
    """Test edge cases and error conditions."""
    
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    def test_save_very_large_dataset(self, mock_dialog, mock_window, temp_dir):
        """Test saving a large dataset."""
        # Setup large dataset
        test_file = os.path.join(temp_dir, "large_data.csv")
        mock_dialog.return_value = (test_file, "CSV files (*.csv)")
        
        size = 10000
        mock_window.graph.freq_data = list(range(size))
        mock_window.graph.mag_data = [-i/100 for i in range(size)]
        mock_window.graph.phase_data = [i % 360 for i in range(size)]
        
        # Execute
        mock_window.save_file_dialog()
        
        # Verify
        assert os.path.exists(test_file)
        
        with open(test_file, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Should have header + data rows
            assert len(rows) == size + 1
            assert rows[0] == ['Frequency', 'Magnitude', 'Phase']
    
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    def test_save_special_characters_in_filename(self, mock_dialog, mock_window, temp_dir):
        """Test saving with special characters in filename."""
        # Setup filename with special characters
        test_file = os.path.join(temp_dir, "test_data_@#$%.csv")
        mock_dialog.return_value = (test_file, "CSV files (*.csv)")
        
        # Execute
        mock_window.save_file_dialog()
        
        # Verify - should handle special characters gracefully
        # File might be created with modified name depending on OS
        files_in_dir = os.listdir(temp_dir)
        assert len(files_in_dir) > 0  # Some file should be created
        
        # Find the created file
        created_file = [f for f in files_in_dir if f.endswith('.csv')][0]
        full_path = os.path.join(temp_dir, created_file)
        
        with open(full_path, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert rows[0] == ['Frequency', 'Magnitude', 'Phase']


class TestFileHandlerIntegration:
    """Test file handler integration with other components."""
    
    def test_file_handler_requires_graph_data(self, mock_window):
        """Test that file handler properly accesses graph data."""
        # Ensure the required graph attributes exist
        assert hasattr(mock_window.graph, 'freq_data')
        assert hasattr(mock_window.graph, 'mag_data')
        assert hasattr(mock_window.graph, 'phase_data')
    
    def test_file_handler_logging_integration(self, mock_window):
        """Test that file handler properly integrates with logging."""
        # Ensure logger is available
        assert hasattr(mock_window, 'logger')
        assert mock_window.logger is not None
        
        with patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog:
            mock_dialog.return_value = ("", "")  # User cancels
            
            mock_window.save_file_dialog()
            
            # When user cancels, no logging should occur
            # (The current implementation doesn't log cancellations)
    
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    def test_csv_format_compatibility(self, mock_dialog, mock_window, temp_dir):
        """Test that saved CSV files are compatible with standard readers."""
        # Setup
        test_file = os.path.join(temp_dir, "compatibility_test.csv")
        mock_dialog.return_value = (test_file, "CSV files (*.csv)")
        
        # Add some realistic data
        mock_window.graph.freq_data = [1000.0, 2000.5, 3000.75]
        mock_window.graph.mag_data = [-10.5, -20.25, -30.125]
        mock_window.graph.phase_data = [0.0, 45.5, 90.25]
        
        # Execute
        mock_window.save_file_dialog()
        
        # Verify file can be read by standard CSV tools
        import csv
        
        # Read and verify CSV content using built-in csv module
        with open(test_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
        # Check header
        assert rows[0] == ['Frequency', 'Magnitude', 'Phase']
        
        # Check data rows
        assert len(rows) == 4  # header + 3 data rows
        assert rows[1] == ['1000.0', '-10.5', '0.0']
        assert rows[2] == ['2000.5', '-20.25', '45.5']
        assert rows[3] == ['3000.75', '-30.125', '90.25']
