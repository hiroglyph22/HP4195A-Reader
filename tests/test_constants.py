# tests/test_constants.py

import pytest
from src.constants import Commands, GPIBCommands, SweepTimings, DefaultValues


class TestCommands:
    """Test the Commands enum for inter-process communication."""
    
    def test_commands_have_string_values(self):
        """Test that all commands have string values for multiprocessing compatibility."""
        assert Commands.CONNECT.value == "connect"
        assert Commands.DISCONNECT.value == "disconnect"
        assert Commands.START_ACQUISITION.value == "start_acquisition"
        assert Commands.SET_CENTER_AND_SPAN.value == "set_center_and_span"
        assert Commands.SET_START_STOP.value == "set_start_stop"
        assert Commands.SET_CENTER_FREQUENCY.value == "set_center_frequency"
        assert Commands.LOW_RES_SWEEP.value == "low_res_sweep"
        assert Commands.SWEEPING_RANGE_OF_AMPLITUDES.value == "sweeping_range_of_amplitudes"
        assert Commands.SEND_COMMAND.value == "send_command"
        assert Commands.GET_MACHINE_VALUES.value == "get_machine_values"
        assert Commands.INITIAL_SETUP.value == "initial_setup"
    
    def test_commands_are_unique(self):
        """Test that all command values are unique."""
        values = [cmd.value for cmd in Commands]
        assert len(values) == len(set(values)), "Duplicate command values found"
    
    def test_new_commands_are_properly_formatted(self):
        """Test that new commands follow proper naming conventions."""
        # Test that new machine-related commands are properly formatted
        assert Commands.GET_MACHINE_VALUES.value == "get_machine_values"
        assert Commands.INITIAL_SETUP.value == "initial_setup"
        
        # Ensure they use underscores, not hyphens or spaces
        for cmd in Commands:
            assert " " not in cmd.value, f"Command {cmd.name} contains spaces"
            assert "-" not in cmd.value, f"Command {cmd.name} contains hyphens"
    
    def test_commands_enum_completeness(self):
        """Test that we have all expected commands."""
        expected_commands = {
            "CONNECT", "DISCONNECT", "START_ACQUISITION", 
            "SET_CENTER_AND_SPAN", "SET_START_STOP", "SET_CENTER_FREQUENCY",
            "LOW_RES_SWEEP", "SWEEPING_RANGE_OF_AMPLITUDES", "SEND_COMMAND",
            "GET_MACHINE_VALUES", "INITIAL_SETUP"
        }
        actual_commands = {cmd.name for cmd in Commands}
        assert actual_commands == expected_commands


class TestGPIBCommands:
    """Test the GPIBCommands enum for instrument communication."""
    
    def test_query_commands(self):
        """Test query command formats."""
        assert GPIBCommands.QUERY_IDENTITY.value == "ID?"
        assert GPIBCommands.QUERY_MAGNITUDE.value == "A?"
        assert GPIBCommands.QUERY_PHASE.value == "B?"
        assert GPIBCommands.QUERY_FREQUENCY.value == "X?"
    
    def test_machine_status_query_commands(self):
        """Test machine status query commands."""
        assert GPIBCommands.QUERY_CENTER.value == "CENTER?"
        assert GPIBCommands.QUERY_SPAN.value == "SPAN?"
        assert GPIBCommands.QUERY_START.value == "START?"
        assert GPIBCommands.QUERY_STOP.value == "STOP?"
        assert GPIBCommands.QUERY_RBW.value == "RBW?"
        assert GPIBCommands.QUERY_OSC1.value == "OSC1?"
        
        # Verify these are valid query commands (end with ?)
        machine_status_queries = [
            GPIBCommands.QUERY_CENTER, GPIBCommands.QUERY_SPAN, 
            GPIBCommands.QUERY_START, GPIBCommands.QUERY_STOP,
            GPIBCommands.QUERY_RBW, GPIBCommands.QUERY_OSC1
        ]
        for query_cmd in machine_status_queries:
            assert query_cmd.value.endswith("?"), f"{query_cmd.name} should end with '?'"
    
    def test_sweep_commands(self):
        """Test sweep control commands."""
        assert GPIBCommands.SWEEP_MODE_SINGLE.value == "SWM2"
        assert GPIBCommands.SWEEP_TRIGGER.value == "SWTRG"
    
    def test_frequency_commands_formatting(self):
        """Test frequency command string formatting."""
        assert GPIBCommands.CENTER.value == "CENTER = {} HZ"
        assert GPIBCommands.SPAN.value == "SPAN = {} HZ"
        assert GPIBCommands.START.value == "START = {} HZ"
        assert GPIBCommands.STOP.value == "STOP = {} HZ"
        
        # Test formatting works
        assert GPIBCommands.CENTER.value.format(1000) == "CENTER = 1000 HZ"
        assert GPIBCommands.SPAN.value.format(5000) == "SPAN = 5000 HZ"
    
    def test_amplitude_commands(self):
        """Test amplitude control commands."""
        assert GPIBCommands.OSCILLATOR_1.value == "OSC1 = {} DBM"
        assert GPIBCommands.OSCILLATOR_1.value.format(-10) == "OSC1 = -10 DBM"
    
    def test_rbw_commands(self):
        """Test resolution bandwidth commands."""
        assert GPIBCommands.RBW.value == "RBW = {} HZ"
        assert GPIBCommands.RBW.value.format(100) == "RBW = 100 HZ"
    
    def test_gpib_commands_completeness(self):
        """Test that all expected GPIB commands are defined."""
        expected_gpib_commands = {
            # Query commands
            "QUERY_IDENTITY", "QUERY_MAGNITUDE", "QUERY_PHASE", "QUERY_FREQUENCY",
            # Machine status query commands  
            "QUERY_CENTER", "QUERY_SPAN", "QUERY_START", "QUERY_STOP", "QUERY_RBW", "QUERY_OSC1",
            # Sweep control commands
            "SWEEP_MODE_SINGLE", "SWEEP_TRIGGER",
            # Frequency control commands
            "CENTER", "SPAN", "START", "STOP",
            # Amplitude control commands
            "OSCILLATOR_1",
            # Resolution bandwidth commands
            "RBW"
        }
        actual_gpib_commands = {cmd.name for cmd in GPIBCommands}
        assert actual_gpib_commands == expected_gpib_commands


class TestSweepTimings:
    """Test the SweepTimings enum for timing values."""
    
    def test_timing_values(self):
        """Test that timing values are reasonable integers."""
        assert isinstance(SweepTimings.RBW_10_HZ.value, int)
        assert isinstance(SweepTimings.RBW_100_HZ.value, int)
        assert SweepTimings.RBW_10_HZ.value > 0
        assert SweepTimings.RBW_100_HZ.value > 0
    
    def test_expected_timing_values(self):
        """Test specific timing values."""
        assert SweepTimings.RBW_10_HZ.value == 218  # seconds
        assert SweepTimings.RBW_100_HZ.value == 41   # seconds
    
    def test_timing_relationship(self):
        """Test that lower RBW takes longer (more accurate)."""
        assert SweepTimings.RBW_10_HZ.value > SweepTimings.RBW_100_HZ.value


class TestDefaultValues:
    """Test the DefaultValues configuration class."""
    
    def test_visa_configuration(self):
        """Test VISA-related default values."""
        assert DefaultValues.VISA_RESOURCE_NAME == 'GPIB0::17::INSTR'
        assert DefaultValues.DEVICE_ID == 'HP4195A'
        assert DefaultValues.VISA_TIMEOUT == 5000  # milliseconds
        assert isinstance(DefaultValues.VISA_TIMEOUT, int)
    
    def test_frequency_defaults(self):
        """Test frequency-related default values."""
        assert DefaultValues.DEFAULT_SPAN == 10000  # Hz
        assert isinstance(DefaultValues.DEFAULT_SPAN, int)
        assert DefaultValues.DEFAULT_SPAN > 0
    
    def test_rbw_defaults(self):
        """Test resolution bandwidth default values."""
        assert DefaultValues.DEFAULT_RBW_LOW_RES == 10   # Hz
        assert DefaultValues.DEFAULT_RBW_NORMAL == 100   # Hz
        assert isinstance(DefaultValues.DEFAULT_RBW_LOW_RES, int)
        assert isinstance(DefaultValues.DEFAULT_RBW_NORMAL, int)
        
        # Low res should be lower frequency (higher precision)
        assert DefaultValues.DEFAULT_RBW_LOW_RES < DefaultValues.DEFAULT_RBW_NORMAL
    
    def test_all_defaults_are_positive(self):
        """Test that all numeric defaults are positive."""
        assert DefaultValues.VISA_TIMEOUT > 0
        assert DefaultValues.DEFAULT_SPAN > 0
        assert DefaultValues.DEFAULT_RBW_LOW_RES > 0
        assert DefaultValues.DEFAULT_RBW_NORMAL > 0


class TestConstantsIntegration:
    """Test integration between different constant classes."""
    
    def test_sweep_timings_match_rbw_defaults(self):
        """Test that sweep timings exist for the default RBW values."""
        # We should have timing data for our default RBW values
        assert hasattr(SweepTimings, 'RBW_10_HZ')  # matches DEFAULT_RBW_LOW_RES
        assert hasattr(SweepTimings, 'RBW_100_HZ') # matches DEFAULT_RBW_NORMAL
    
    def test_gpib_commands_work_with_defaults(self):
        """Test that GPIB commands work with default values."""
        # Test that we can format commands with default values
        center_cmd = GPIBCommands.CENTER.value.format(1000)
        span_cmd = GPIBCommands.SPAN.value.format(DefaultValues.DEFAULT_SPAN)
        rbw_cmd = GPIBCommands.RBW.value.format(DefaultValues.DEFAULT_RBW_NORMAL)
        
        assert "1000" in center_cmd
        assert "10000" in span_cmd
        assert "100" in rbw_cmd
