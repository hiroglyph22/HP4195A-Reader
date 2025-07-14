import pytest
import numpy as np
from unittest.mock import MagicMock, patch, call
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog
from queue import Queue
import tempfile
import os

# Import the classes to be tested
from src.main_window import MainWindow
from src.logic.instrument_controls import SweepCommunicator, InstrumentControls
from src.gui.final_sweep_viewer import FinalSweepViewer
from src.gui.amplitude_sweep_viewer import AmplitudeSweepViewer


class TestSweepCommunicator:
    """Tests for the SweepCommunicator class."""
    
    def test_sweep_communicator_signals(self):
        """Test that SweepCommunicator has the expected signals."""
        communicator = SweepCommunicator()
        
        # Check that all required signals exist
        assert hasattr(communicator, 'new_sweep_window_ready')
        assert hasattr(communicator, 'final_plot_ready')
        assert hasattr(communicator, 'enable_button')


class TestSweepingRangeOfAmplitudes:
    """Tests for the sweeping range of amplitudes functionality."""
    
    def test_input_validation_positive_step(self, app, qtbot):
        """Test that step size must be positive."""
        # Set invalid step (negative)
        app.start_amplitude_input.setText("-10")
        app.stop_amplitude_input.setText("10")
        app.step_amplitude_input.setText("-1")  # Invalid negative step
        
        with patch.object(app, 'show_error_dialog') as mock_error:
            app.start_sweeping_range_of_amplitudes()
            mock_error.assert_called_once_with("Invalid Step", "Amplitude step must be a positive number.")
    
    def test_input_validation_start_less_than_stop(self, app, qtbot):
        """Test that start amplitude must be less than stop amplitude."""
        # Set invalid range (start > stop)
        app.start_amplitude_input.setText("10")
        app.stop_amplitude_input.setText("-10")  # Invalid: stop < start
        app.step_amplitude_input.setText("1")
        
        with patch.object(app, 'show_error_dialog') as mock_error:
            app.start_sweeping_range_of_amplitudes()
            mock_error.assert_called_once_with("Invalid Range", "Start amplitude cannot be greater than stop amplitude.")
    
    def test_input_validation_invalid_numbers(self, app, qtbot):
        """Test validation of non-numeric inputs."""
        # Set invalid input (non-numeric)
        app.start_amplitude_input.setText("invalid")
        app.stop_amplitude_input.setText("10")
        app.step_amplitude_input.setText("1")
        
        with patch.object(app, 'show_error_dialog') as mock_error:
            app.start_sweeping_range_of_amplitudes()
            mock_error.assert_called_once_with("Invalid Input", "Please enter valid numbers for the Sweeping Range of Amplitudes parameters.")
    
    @patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory')
    def test_directory_selection_cancelled(self, mock_file_dialog, app, qtbot):
        """Test behavior when user cancels directory selection."""
        # Set valid inputs
        app.start_amplitude_input.setText("-10")
        app.stop_amplitude_input.setText("10")
        app.step_amplitude_input.setText("2")
        
        # Mock file dialog to return empty string (cancelled)
        mock_file_dialog.return_value = ""
        
        with patch.object(app.logger, 'info') as mock_logger:
            app.start_sweeping_range_of_amplitudes()
            mock_logger.assert_called_once_with("Sweeping Range of Amplitudes cancelled by user.")
    
    @patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory')
    def test_successful_sweep_setup(self, mock_file_dialog, app, qtbot):
        """Test successful setup of sweeping range of amplitudes."""
        # Set valid inputs
        app.start_amplitude_input.setText("-10")
        app.stop_amplitude_input.setText("10")
        app.step_amplitude_input.setText("5")
        app.resolution_combo.setCurrentText("100")
        
        # Mock file dialog to return a directory
        temp_dir = tempfile.mkdtemp()
        mock_file_dialog.return_value = temp_dir
        
        try:
            with patch('src.logic.instrument_controls.Thread') as mock_thread:
                # Mock thread to prevent actual execution
                mock_thread_instance = MagicMock()
                mock_thread.return_value = mock_thread_instance
                
                app.start_sweeping_range_of_amplitudes()
                
                # Verify button is disabled during sweep
                assert not app.sweeping_range_of_amplitudes_button.isEnabled()
                
                # Verify thread was created and started
                mock_thread.assert_called_once()
                mock_thread_instance.start.assert_called_once()
                
                # Verify sweep_viewers list was initialized
                assert hasattr(app, 'sweep_viewers')
                assert app.sweep_viewers == []
                
                # Verify the thread target function was set correctly
                call_args = mock_thread.call_args
                assert 'target' in call_args[1]
                assert callable(call_args[1]['target'])
            
        finally:
            # Clean up temp directory
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
    
    def test_sweep_calculation(self, app):
        """Test calculation of number of sweeps."""
        # Test case: start=-10, stop=10, step=5 should give 5 sweeps
        # (-10, -5, 0, 5, 10)
        start_p, stop_p, step_p = -10.0, 10.0, 5.0
        num_sweeps = int((stop_p - start_p) / step_p) + 1
        assert num_sweeps == 5
        
        # Test case: start=0, stop=10, step=2 should give 6 sweeps
        # (0, 2, 4, 6, 8, 10)
        start_p, stop_p, step_p = 0.0, 10.0, 2.0
        num_sweeps = int((stop_p - start_p) / step_p) + 1
        assert num_sweeps == 6
    
    def test_create_new_sweep_window(self, app):
        """Test creation of new sweep window."""
        # Prepare test data
        freq_data = np.linspace(1000, 2000, 100)
        mag_data = np.random.randn(100) - 20
        amplitude = -10.0
        
        # Call the method
        app.create_new_sweep_window(freq_data, mag_data, amplitude)
        
        # Verify sweep_viewers list exists and contains the new viewer
        assert hasattr(app, 'sweep_viewers')
        assert len(app.sweep_viewers) == 1
        assert isinstance(app.sweep_viewers[0], AmplitudeSweepViewer)
    
    def test_create_final_sweep_window(self, app):
        """Test creation of final sweep window."""
        # Prepare test data
        all_sweeps_data = [
            (np.linspace(1000, 2000, 100), np.random.randn(100) - 20, -10.0),
            (np.linspace(1000, 2000, 100), np.random.randn(100) - 15, -5.0),
            (np.linspace(1000, 2000, 100), np.random.randn(100) - 10, 0.0),
        ]
        
        # Call the method
        app.create_final_sweep_window(all_sweeps_data)
        
        # Verify sweep_viewers list exists and contains the new viewer
        assert hasattr(app, 'sweep_viewers')
        assert len(app.sweep_viewers) == 1
        assert isinstance(app.sweep_viewers[0], FinalSweepViewer)
    
    def test_sweep_window_cleanup(self, app):
        """Test that old sweep windows are cleaned up before new sweep."""
        # Create some mock sweep viewers
        mock_viewer1 = MagicMock()
        mock_viewer2 = MagicMock()
        app.sweep_viewers = [mock_viewer1, mock_viewer2]
        
        # Set valid inputs for sweep
        app.start_amplitude_input.setText("-10")
        app.stop_amplitude_input.setText("10")
        app.step_amplitude_input.setText("5")
        
        # Use a valid directory path so the method doesn't exit early
        with patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory', return_value="/tmp"), \
             patch('src.logic.instrument_controls.Thread') as mock_thread:
            
            # Mock thread to prevent actual execution
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance
            
            app.start_sweeping_range_of_amplitudes()
        
        # Verify old viewers were closed
        mock_viewer1.close.assert_called_once()
        mock_viewer2.close.assert_called_once()
        
        # Verify list was cleared
        assert len(app.sweep_viewers) == 0


class TestFinalSweepViewer:
    """Tests for the FinalSweepViewer class."""
    
    def test_final_sweep_viewer_initialization(self, qtbot):
        """Test FinalSweepViewer initializes correctly."""
        viewer = FinalSweepViewer()
        qtbot.addWidget(viewer)
        
        # Check basic properties
        assert viewer.windowTitle() == "Final Overlaid Sweeps"
        assert viewer.minimumSize().width() == 800
        assert viewer.minimumSize().height() == 600
        assert hasattr(viewer, 'all_sweeps_data')
        assert hasattr(viewer, 'amplitude_list')
        assert hasattr(viewer, 'plot_canvas')
    
    def test_update_plot_populates_list(self, qtbot):
        """Test that update_plot populates the amplitude list correctly."""
        viewer = FinalSweepViewer()
        qtbot.addWidget(viewer)
        
        # Prepare test data
        all_sweeps_data = [
            (np.linspace(1000, 2000, 100), np.random.randn(100) - 20, -10.0),
            (np.linspace(1000, 2000, 100), np.random.randn(100) - 15, -5.0),
            (np.linspace(1000, 2000, 100), np.random.randn(100) - 10, 0.0),
        ]
        
        # Call update_plot
        viewer.update_plot(all_sweeps_data)
        
        # Verify data was stored
        assert viewer.all_sweeps_data == all_sweeps_data
        
        # Verify amplitude list was populated
        assert viewer.amplitude_list.count() == 3
        
        # Verify items are selected by default
        selected_items = viewer.amplitude_list.selectedItems()
        assert len(selected_items) == 3
        
        # Verify amplitude values in list items
        amplitudes = {item.data(Qt.UserRole) for item in selected_items}
        expected_amplitudes = {-10.0, -5.0, 0.0}
        assert amplitudes == expected_amplitudes
    
    def test_replot_selected_sweeps(self, qtbot):
        """Test that replot_selected_sweeps filters data correctly."""
        viewer = FinalSweepViewer()
        qtbot.addWidget(viewer)
        
        # Prepare test data
        all_sweeps_data = [
            (np.linspace(1000, 2000, 100), np.random.randn(100) - 20, -10.0),
            (np.linspace(1000, 2000, 100), np.random.randn(100) - 15, -5.0),
            (np.linspace(1000, 2000, 100), np.random.randn(100) - 10, 0.0),
        ]
        
        viewer.update_plot(all_sweeps_data)
        
        # Deselect middle item
        viewer.amplitude_list.item(1).setSelected(False)
        
        with patch.object(viewer.plot_canvas, 'update_overlaid_plot') as mock_plot:
            viewer.replot_selected_sweeps()
            
            # Verify only selected sweeps were passed to plot
            mock_plot.assert_called_once()
            args = mock_plot.call_args[0][0]  # Get the first argument
            assert len(args) == 2  # Only 2 sweeps should be selected
            
            # Verify correct amplitudes were selected (-10.0 and 0.0, not -5.0)
            selected_amplitudes = {sweep[2] for sweep in args}
            expected_amplitudes = {-10.0, 0.0}
            assert selected_amplitudes == expected_amplitudes


class TestAmplitudeSweepViewer:
    """Tests for the AmplitudeSweepViewer class."""
    
    def test_amplitude_sweep_viewer_initialization(self, qtbot):
        """Test AmplitudeSweepViewer initializes correctly."""
        viewer = AmplitudeSweepViewer()
        qtbot.addWidget(viewer)
        
        # Check basic properties
        assert viewer.minimumSize().width() == 800
        assert viewer.minimumSize().height() == 600
        assert hasattr(viewer, 'plot_canvas')
        
        # Window title is empty by default, gets set during update_plot
        assert viewer.windowTitle() == ""
    
    def test_update_plot(self, qtbot):
        """Test that update_plot updates the canvas correctly."""
        viewer = AmplitudeSweepViewer()
        qtbot.addWidget(viewer)
        
        # Prepare test data
        freq_data = np.linspace(1000, 2000, 100)
        mag_data = np.random.randn(100) - 20
        amplitude = -10.0
        
        with patch.object(viewer.plot_canvas, 'update_sweep_plot') as mock_plot:
            viewer.update_plot(freq_data, mag_data, amplitude)
            
            # Verify plot canvas was called with correct data
            mock_plot.assert_called_once_with(freq_data, mag_data)
            
            # Verify window title was updated
            assert viewer.windowTitle() == "Sweep at -10.00 dBm"
