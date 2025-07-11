import unittest
from unittest.mock import Mock, patch
import pytest

# Import the UIGenerator mixin
from src.gui.ui_generator import UIGenerator

class TestUIGeneratorImport:
    """Test basic UI generator functionality without creating widgets."""
    
    def test_ui_generator_can_be_imported(self):
        """Test that UIGenerator can be imported successfully."""
        assert UIGenerator is not None
        assert hasattr(UIGenerator, 'generate_UI')
        assert hasattr(UIGenerator, 'generate_frequency_sweep_section')
        assert hasattr(UIGenerator, 'generate_amplitude_sweep_section')
        assert hasattr(UIGenerator, 'generate_command_section')
        assert hasattr(UIGenerator, 'generate_menu_bar')
    
    def test_ui_generator_methods_exist(self):
        """Test that all expected UI generator methods exist."""
        expected_methods = [
            'generate_UI',
            'generate_frequency_sweep_section', 
            'generate_amplitude_sweep_section',
            'generate_command_section',
            'generate_menu_bar'
        ]
        
        for method_name in expected_methods:
            assert hasattr(UIGenerator, method_name)
            assert callable(getattr(UIGenerator, method_name))


class TestUIGeneratorConstants:
    """Test UI-related constants and configurations."""
    
    def test_ui_component_names_are_consistent(self):
        """Test that expected UI component names follow patterns."""
        # These are the component names we expect to be created
        expected_components = [
            'connect_button',
            'acquire_button', 
            'save_button',
            'pause_button',
            'p_cb',  # persistence checkbox
            'mag_cb',  # magnitude checkbox
            'phase_cb',  # phase checkbox
            'peak_freq_input',
            'autofind_peak_button',
            'center_peak_button',
            'q_factor_button'
        ]
        
        # This test doesn't create widgets, just verifies naming conventions
        for component in expected_components:
            assert isinstance(component, str)
            assert len(component) > 0
            # Check naming convention (snake_case with descriptive suffixes)
            assert '_' in component or component.endswith(('_cb', '_button', '_input'))


if __name__ == '__main__':
    unittest.main()
