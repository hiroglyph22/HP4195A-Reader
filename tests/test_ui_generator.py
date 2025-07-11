import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt5 import QtWidgets, QtCore
import pytest

# Import the UIGenerator mixin
from src.gui.ui_generator import UIGenerator

class MockMainWindow(UIGenerator):
    """Mock MainWindow class that inherits from UIGenerator for testing."""
    
    def __init__(self):
        # Initialize required attributes for testing
        self.logger = Mock()
        
        # Mock PyQt5 methods that would normally be inherited from QMainWindow
        self.menuBar = Mock()
        self.setCentralWidget = Mock()
        self.setWindowTitle = Mock()
        self.setGeometry = Mock()
        
        # Mock graph object for file handler tests
        self.graph = Mock()
        self.graph.freq_data = []
        self.graph.mag_data = []
        self.graph.phase_data = []
        
    def set_tooltips_and_connections(self):
        """Mock method for setting tooltips and connections."""
        pass
        
    def set_initial_button_states(self):
        """Mock method for setting initial button states."""
        pass


@pytest.fixture
def mock_window():
    """Create a mock main window for testing."""
    return MockMainWindow()


class TestUIGeneratorMain:
    """Test main UI generation functionality."""

    @patch('src.gui.ui_generator.QtWidgets.QWidget')
    @patch('src.gui.ui_generator.QtWidgets.QVBoxLayout')
    @patch('src.gui.ui_generator.QtWidgets.QGroupBox')
    @patch('src.gui.ui_generator.QtWidgets.QPushButton')
    def test_generate_UI_creates_main_components(self, mock_button, mock_group, mock_layout, mock_widget, mock_window):
        """Test that generate_UI creates all main UI components."""
        # Setup mocks
        mock_widget_instance = Mock()
        mock_widget.return_value = mock_widget_instance
        mock_layout_instance = Mock()
        mock_layout.return_value = mock_layout_instance
        mock_group_instance = Mock()
        mock_group.return_value = mock_group_instance
        mock_button_instance = Mock()
        mock_button.return_value = mock_button_instance
        
        # Execute
        result = mock_window.generate_UI()
        
        # Verify the function returns a widget
        assert result == mock_widget_instance
        
        # Verify main layout components were created
        assert mock_layout.called
        assert mock_group.called
        assert mock_button.called

    @patch('src.gui.ui_generator.QtWidgets.QPushButton')
    def test_main_action_buttons_created(self, mock_button_class, mock_window):
        """Test that main action buttons are created with correct labels."""
        mock_button = Mock()
        mock_button_class.return_value = mock_button
        
        with patch('src.gui.ui_generator.QtWidgets.QGroupBox'), \
             patch('src.gui.ui_generator.QtWidgets.QGridLayout'), \
             patch('src.gui.ui_generator.QtWidgets.QVBoxLayout'), \
             patch('src.gui.ui_generator.QtWidgets.QWidget'):
            mock_window.generate_UI()
        
        # Check that buttons were created with correct text
        button_calls = mock_button_class.call_args_list
        button_texts = [call[0][0] for call in button_calls if call[0]]
        
        assert 'Connect' in button_texts
        assert 'Acquire Data' in button_texts
        assert 'Save Data' in button_texts
        assert 'Start Auto-Update' in button_texts

    @patch('src.gui.ui_generator.QtWidgets.QCheckBox')
    def test_plotting_checkboxes_created(self, mock_checkbox_class, mock_window):
        """Test that plotting control checkboxes are created."""
        mock_checkbox = Mock()
        mock_checkbox_class.return_value = mock_checkbox
        
        with patch('src.gui.ui_generator.QtWidgets.QGroupBox'), \
             patch('src.gui.ui_generator.QtWidgets.QHBoxLayout'), \
             patch('src.gui.ui_generator.QtWidgets.QVBoxLayout'), \
             patch('src.gui.ui_generator.QtWidgets.QWidget'):
            mock_window.generate_UI()
        
        # Check that checkboxes were created
        checkbox_calls = mock_checkbox_class.call_args_list
        checkbox_texts = [call[0][0] for call in checkbox_calls if call[0]]
        
        assert 'Persist' in checkbox_texts
        assert 'Magnitude' in checkbox_texts
        assert 'Phase' in checkbox_texts


class TestUIGeneratorSections:
    """Test individual UI section generation methods."""

    def test_generate_frequency_sweep_section(self, mock_window):
        """Test frequency sweep section generation."""
        with patch('src.gui.ui_generator.QtWidgets.QGroupBox') as mock_group, \
             patch('src.gui.ui_generator.QtWidgets.QGridLayout') as mock_layout, \
             patch('src.gui.ui_generator.QtWidgets.QLabel') as mock_label, \
             patch('src.gui.ui_generator.QtWidgets.QLineEdit') as mock_input:
            
            mock_group_instance = Mock()
            mock_group.return_value = mock_group_instance
            mock_layout_instance = Mock()
            mock_layout.return_value = mock_layout_instance
            
            result = mock_window.generate_frequency_sweep_section()
            
            # Verify that the method returns a group box
            assert result == mock_group_instance
            
            # Verify group box was created with correct title
            mock_group.assert_called_with("Frequency Sweep")
            
            # Verify layout was set
            mock_group_instance.setLayout.assert_called_with(mock_layout_instance)

    def test_generate_amplitude_sweep_section(self, mock_window):
        """Test amplitude sweep section generation."""
        with patch('src.gui.ui_generator.QtWidgets.QGroupBox') as mock_group, \
             patch('src.gui.ui_generator.QtWidgets.QGridLayout') as mock_layout:
            
            mock_group_instance = Mock()
            mock_group.return_value = mock_group_instance
            
            result = mock_window.generate_amplitude_sweep_section()
            
            # Verify that the method returns a group box
            assert result == mock_group_instance
            
            # Verify group box was created with correct title
            mock_group.assert_called_with("Amplitude Sweep")

    def test_generate_command_section(self, mock_window):
        """Test command section generation."""
        with patch('src.gui.ui_generator.QtWidgets.QGroupBox') as mock_group, \
             patch('src.gui.ui_generator.QtWidgets.QVBoxLayout') as mock_layout:
            
            mock_group_instance = Mock()
            mock_group.return_value = mock_group_instance
            
            result = mock_window.generate_command_section()
            
            # Verify that the method returns a group box
            assert result == mock_group_instance
            
            # Verify group box was created with correct title
            mock_group.assert_called_with("GPIB Command")


class TestUIGeneratorMenus:
    """Test menu generation functionality."""

    def test_generate_menu_bar(self, mock_window):
        """Test menu bar generation."""
        # Setup mocks for menu system
        mock_main_menu = Mock()
        mock_file_menu = Mock()
        mock_about_menu = Mock()
        
        mock_window.menuBar.return_value = mock_main_menu
        mock_main_menu.addMenu.side_effect = [mock_file_menu, mock_about_menu]
        
        with patch('src.gui.ui_generator.QtWidgets.QAction') as mock_action:
            mock_action_instance = Mock()
            mock_action.return_value = mock_action_instance
            
            mock_window.generate_menu_bar()
            
            # Verify menu bar was accessed
            mock_window.menuBar.assert_called_once()
            
            # Verify menus were added
            assert mock_main_menu.addMenu.call_count == 2
            call_args = mock_main_menu.addMenu.call_args_list
            assert call_args[0][0][0] == '&File'
            assert call_args[1][0][0] == '&About'


class TestUIGeneratorIntegration:
    """Test UI component integration and consistency."""

    def test_ui_components_are_accessible(self, mock_window):
        """Test that generated UI components are accessible as attributes."""
        with patch('src.gui.ui_generator.QtWidgets.QPushButton') as mock_button, \
             patch('src.gui.ui_generator.QtWidgets.QCheckBox') as mock_checkbox, \
             patch('src.gui.ui_generator.QtWidgets.QLineEdit') as mock_input, \
             patch('src.gui.ui_generator.QtWidgets.QGroupBox'), \
             patch('src.gui.ui_generator.QtWidgets.QGridLayout'), \
             patch('src.gui.ui_generator.QtWidgets.QHBoxLayout'), \
             patch('src.gui.ui_generator.QtWidgets.QVBoxLayout'), \
             patch('src.gui.ui_generator.QtWidgets.QWidget'):
            
            mock_button.return_value = Mock()
            mock_checkbox.return_value = Mock()
            mock_input.return_value = Mock()
            
            mock_window.generate_UI()
            
            # Check that main components are accessible
            assert hasattr(mock_window, 'connect_button')
            assert hasattr(mock_window, 'acquire_button')
            assert hasattr(mock_window, 'save_button')
            assert hasattr(mock_window, 'pause_button')
            assert hasattr(mock_window, 'p_cb')
            assert hasattr(mock_window, 'mag_cb')
            assert hasattr(mock_window, 'phase_cb')

    def test_ui_layout_structure(self, mock_window):
        """Test that UI follows correct layout structure."""
        with patch('src.gui.ui_generator.QtWidgets.QVBoxLayout') as mock_vlayout, \
             patch('src.gui.ui_generator.QtWidgets.QWidget') as mock_widget, \
             patch('src.gui.ui_generator.QtWidgets.QGroupBox'), \
             patch('src.gui.ui_generator.QtWidgets.QGridLayout'), \
             patch('src.gui.ui_generator.QtWidgets.QHBoxLayout'):
            
            mock_layout_instance = Mock()
            mock_vlayout.return_value = mock_layout_instance
            mock_widget_instance = Mock()
            mock_widget.return_value = mock_widget_instance
            
            result = mock_window.generate_UI()
            
            # Verify main layout was created and configured
            mock_vlayout.assert_called()
            mock_layout_instance.setSpacing.assert_called_with(10)
            mock_layout_instance.setAlignment.assert_called_with(QtCore.Qt.AlignTop)
            
            # Verify widget was created and layout applied
            mock_widget.assert_called()
            mock_widget_instance.setLayout.assert_called_with(mock_layout_instance)
            mock_widget_instance.setMinimumWidth.assert_called_with(420)
            
            assert result == mock_widget_instance


if __name__ == '__main__':
    unittest.main()
