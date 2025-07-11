# tests/test_file_handler_comprehensive.py

import pytest
import csv
import tempfile
import os
from unittest.mock import Mock, MagicMock, patch, mock_open
from PyQt5 import QtWidgets

from src.logic.file_handler import FileHandler


class MockMainWindow(FileHandler):
    """Mock main window that properly implements the FileHandler interface."""
    
    def __init__(self):
        # Mock logger
        self.logger = Mock()
        
        # Mock graph component with data
        self.graph = Mock()
        self.graph.freq_data = [1000, 2000, 3000]
        self.graph.mag_data = [-10, -20, -15]
        self.graph.phase_data = [0, 45, 90]


class TestFileHandlerSaveDialog:
    """Test file save dialog functionality."""
    
    @pytest.fixture
    def mock_window(self):
        """Create a properly mocked main window."""
        return MockMainWindow()
    
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    def test_save_dialog_success(self, mock_get_save_filename, mock_window):
        """Test successful file save dialog."""
        # Setup
        test_filename = "/tmp/test_data.csv"
        mock_get_save_filename.return_value = (test_filename, "CSV Files (*.csv)")
        
        with patch.object(mock_window, 'save_file') as mock_save_file:
            # Execute
            mock_window.save_file_dialog()
            
            # Verify
            mock_get_save_filename.assert_called_once()
            mock_save_file.assert_called_once_with(test_filename)
    
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    def test_save_dialog_user_cancels(self, mock_get_save_filename, mock_window):
        """Test user cancelling the save dialog."""
        # Setup - empty filename indicates cancellation
        mock_get_save_filename.return_value = ("", "")
        
        with patch.object(mock_window, 'save_file') as mock_save_file:
            # Execute
            mock_window.save_file_dialog()
            
            # Verify save_file was not called
            mock_save_file.assert_not_called()
    
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    def test_save_dialog_adds_csv_extension(self, mock_get_save_filename, mock_window):
        """Test that .csv extension is added if missing."""
        # Setup
        test_filename = "/tmp/test_data"  # No extension
        expected_filename = "/tmp/test_data.csv"
        mock_get_save_filename.return_value = (test_filename, "CSV Files (*.csv)")
        
        with patch.object(mock_window, 'save_file') as mock_save_file:
            # Execute
            mock_window.save_file_dialog()
            
            # Verify extension was added
            mock_save_file.assert_called_once_with(expected_filename)
    
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    @patch('src.logic.file_handler.QtWidgets.QMessageBox.critical')
    def test_save_dialog_permission_error(self, mock_critical, mock_get_save_filename, mock_window):
        """Test handling of permission errors."""
        # Setup
        test_filename = "/tmp/test_data.csv"
        mock_get_save_filename.return_value = (test_filename, "CSV Files (*.csv)")
        
        with patch.object(mock_window, 'save_file', side_effect=PermissionError("Access denied")):
            # Execute
            mock_window.save_file_dialog()
            
            # Verify error was logged and dialog shown
            mock_window.logger.error.assert_called_once()
            mock_critical.assert_called_once()
    
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    def test_save_dialog_preserves_existing_csv_extension(self, mock_get_save_filename, mock_window):
        """Test that existing .csv extension is preserved."""
        # Setup
        test_filename = "/tmp/test_data.csv"  # Already has extension
        mock_get_save_filename.return_value = (test_filename, "CSV Files (*.csv)")
        
        with patch.object(mock_window, 'save_file') as mock_save_file:
            # Execute
            mock_window.save_file_dialog()
            
            # Verify extension was not duplicated
            mock_save_file.assert_called_once_with(test_filename)


class TestFileHandlerSaveFile:
    """Test actual file saving functionality."""
    
    @pytest.fixture
    def mock_window(self):
        """Create a properly mocked main window."""
        return MockMainWindow()
    
    def test_save_file_creates_valid_csv(self, mock_window):
        """Test that save_file creates a valid CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            # Execute
            mock_window.save_file(tmp_filename)
            
            # Verify file was created and has correct content
            assert os.path.exists(tmp_filename)
            
            with open(tmp_filename, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                # Check header
                assert rows[0] == ['Frequency', 'Magnitude', 'Phase']
                
                # Check data rows
                assert len(rows) == 4  # Header + 3 data rows
                assert rows[1] == ['1000', '-10', '0']
                assert rows[2] == ['2000', '-20', '45']
                assert rows[3] == ['3000', '-15', '90']
                
        finally:
            # Cleanup
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)
    
    def test_save_file_logs_operation(self, mock_window):
        """Test that save operation is logged."""
        test_filename = "/tmp/test.csv"
        
        with patch('builtins.open', mock_open()):
            # Execute
            mock_window.save_file(test_filename)
            
            # Verify logging
            mock_window.logger.info.assert_called_once_with(f'Saving data to: {test_filename}')
    
    def test_save_file_handles_empty_data(self, mock_window):
        """Test saving when data is empty."""
        # Setup empty data
        mock_window.graph.freq_data = []
        mock_window.graph.mag_data = []
        mock_window.graph.phase_data = []
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            # Execute
            mock_window.save_file(tmp_filename)
            
            # Verify file has only header
            with open(tmp_filename, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                assert len(rows) == 1  # Only header
                assert rows[0] == ['Frequency', 'Magnitude', 'Phase']
                
        finally:
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)
    
    def test_save_file_handles_mismatched_data_lengths(self, mock_window):
        """Test saving when data arrays have different lengths."""
        # Setup mismatched data
        mock_window.graph.freq_data = [1000, 2000, 3000, 4000]  # 4 elements
        mock_window.graph.mag_data = [-10, -20]  # 2 elements  
        mock_window.graph.phase_data = [0, 45, 90]  # 3 elements
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            # Execute
            mock_window.save_file(tmp_filename)
            
            # Verify file contains only matching data (zip stops at shortest)
            with open(tmp_filename, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                assert len(rows) == 3  # Header + 2 data rows (shortest length)
                assert rows[1] == ['1000', '-10', '0']
                assert rows[2] == ['2000', '-20', '45']
                
        finally:
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)


class TestFileHandlerIntegration:
    """Test integration between dialog and save operations."""
    
    @pytest.fixture
    def mock_window(self):
        """Create a properly mocked main window."""
        return MockMainWindow()
    
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    def test_full_save_workflow(self, mock_get_save_filename, mock_window):
        """Test complete save workflow from dialog to file."""
        # Setup
        test_filename = "/tmp/integration_test"
        mock_get_save_filename.return_value = (test_filename, "CSV Files (*.csv)")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            full_path = os.path.join(tmpdir, "integration_test.csv")
            mock_get_save_filename.return_value = (os.path.join(tmpdir, "integration_test"), "CSV Files (*.csv)")
            
            # Execute
            mock_window.save_file_dialog()
            
            # Verify file was created
            assert os.path.exists(full_path)
            
            # Verify logging occurred
            mock_window.logger.info.assert_called_once()
    
    def test_graph_data_access_pattern(self, mock_window):
        """Test that file handler accesses graph data correctly."""
        # Setup specific data
        test_freq = [100, 200, 300]
        test_mag = [-5, -10, -15]
        test_phase = [30, 60, 90]
        
        mock_window.graph.freq_data = test_freq
        mock_window.graph.mag_data = test_mag
        mock_window.graph.phase_data = test_phase
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('csv.writer') as mock_writer:
                mock_writer_instance = Mock()
                mock_writer.return_value = mock_writer_instance
                
                # Execute
                mock_window.save_file("/tmp/test.csv")
                
                # Verify data access pattern
                mock_writer_instance.writerow.assert_any_call(['Frequency', 'Magnitude', 'Phase'])
                mock_writer_instance.writerows.assert_called_once()
                
                # Check that the data was zipped correctly
                call_args = mock_writer_instance.writerows.call_args[0][0]
                data_rows = list(call_args)
                assert data_rows == [(100, -5, 30), (200, -10, 60), (300, -15, 90)]


class TestFileHandlerErrorScenarios:
    """Test various error scenarios and edge cases."""
    
    @pytest.fixture
    def mock_window(self):
        """Create a properly mocked main window."""
        return MockMainWindow()
    
    @patch('src.logic.file_handler.QtWidgets.QFileDialog.getSaveFileName')
    @patch('src.logic.file_handler.QtWidgets.QMessageBox.critical')
    def test_os_error_handling(self, mock_critical, mock_get_save_filename, mock_window):
        """Test handling of OS errors during save."""
        # Setup
        test_filename = "/invalid/path/test.csv"
        mock_get_save_filename.return_value = (test_filename, "CSV Files (*.csv)")
        
        with patch.object(mock_window, 'save_file', side_effect=OSError("Invalid path")):
            # Execute
            mock_window.save_file_dialog()
            
            # Verify error handling
            mock_window.logger.error.assert_called_once()
            assert "Could not write to file" in mock_window.logger.error.call_args[0][0]
            mock_critical.assert_called_once()
    
    def test_graph_attribute_access(self, mock_window):
        """Test that required graph attributes are accessed safely."""
        # Test that all required attributes exist and are accessible
        assert hasattr(mock_window.graph, 'freq_data')
        assert hasattr(mock_window.graph, 'mag_data')
        assert hasattr(mock_window.graph, 'phase_data')
        
        # Test data access
        freq_data = mock_window.graph.freq_data
        mag_data = mock_window.graph.mag_data
        phase_data = mock_window.graph.phase_data
        
        assert isinstance(freq_data, list)
        assert isinstance(mag_data, list)
        assert isinstance(phase_data, list)
    
    def test_logger_availability(self, mock_window):
        """Test that logger is available and functional."""
        assert hasattr(mock_window, 'logger')
        
        # Test logger methods exist
        assert hasattr(mock_window.logger, 'info')
        assert hasattr(mock_window.logger, 'error')
        
        # Test logger can be called
        mock_window.logger.info("test message")
        mock_window.logger.error("test error")
        
        mock_window.logger.info.assert_called_with("test message")
        mock_window.logger.error.assert_called_with("test error")
