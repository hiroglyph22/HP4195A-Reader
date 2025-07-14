# tests/test_main_window.py

import pytest
from unittest.mock import Mock, patch


class TestMainWindowBasics:
    """Basic tests for MainWindow without instantiation."""
    
    def test_main_window_imports(self):
        """Test that MainWindow can be imported."""
        # Mock all PyQt5 components to avoid GUI initialization
        with patch('PyQt5.QtWidgets.QMainWindow'), \
             patch('PyQt5.QtCore.QTimer'), \
             patch('PyQt5.QtGui.QIcon'), \
             patch('src.main_window.PlotCanvas'):
            
            from src.main_window import MainWindow
            assert MainWindow is not None
    
    def test_mixin_imports(self):
        """Test that all mixin classes can be imported."""
        from src.gui.ui_generator import UIGenerator
        from src.logic.file_handler import FileHandler
        from src.logic.instrument_controls import InstrumentControls
        from src.logic.plot_controls import PlotControls
        from src.logic.ui_logic import UiLogic
        
        # All mixins should be importable
        assert UIGenerator is not None
        assert FileHandler is not None
        assert InstrumentControls is not None
        assert PlotControls is not None
        assert UiLogic is not None
    
    def test_inheritance_chain(self):
        """Test MainWindow inheritance without creating instances."""
        with patch('PyQt5.QtWidgets.QMainWindow'), \
             patch('PyQt5.QtCore.QTimer'), \
             patch('PyQt5.QtGui.QIcon'), \
             patch('src.main_window.PlotCanvas'):
            
            from src.main_window import MainWindow
            from src.gui.ui_generator import UIGenerator
            from src.logic.file_handler import FileHandler
            from src.logic.instrument_controls import InstrumentControls
            from src.logic.plot_controls import PlotControls
            from src.logic.ui_logic import UiLogic
            
            # Check inheritance relationships
            assert issubclass(MainWindow, UIGenerator)
            assert issubclass(MainWindow, FileHandler)
            assert issubclass(MainWindow, InstrumentControls)
            assert issubclass(MainWindow, PlotControls)
            assert issubclass(MainWindow, UiLogic)
