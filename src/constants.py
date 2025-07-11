"""
Constants and ENUMs for the HP4195A Reader application.
This module defines command constants and other shared values used across the application.
"""

from enum import Enum, auto


class Commands(Enum):
    """Enumeration for all commands that can be sent between GUI and instrument interface."""
    
    # Connection commands
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    
    # Data acquisition commands
    START_ACQUISITION = "start_acquisition"
    
    # Frequency control commands
    SET_CENTER_AND_SPAN = "set_center_and_span"
    SET_START_STOP = "set_start_stop"
    SET_CENTER_FREQUENCY = "set_center_frequency"
    
    # Sweep commands
    LOW_RES_SWEEP = "low_res_sweep"
    SWEEPING_RANGE_OF_AMPLITUDES = "sweeping_range_of_amplitudes"
    
    # General command sending
    SEND_COMMAND = "send_command"


class GPIBCommands(Enum):
    """Enumeration for GPIB commands sent to the HP4195A instrument."""
    
    # Query commands
    QUERY_IDENTITY = "ID?"
    QUERY_MAGNITUDE = "A?"
    QUERY_PHASE = "B?"
    QUERY_FREQUENCY = "X?"
    
    # Sweep control commands
    SWEEP_MODE_SINGLE = "SWM2"
    SWEEP_TRIGGER = "SWTRG"
    
    # Frequency control commands
    CENTER = "CENTER = {} HZ"
    SPAN = "SPAN = {} HZ"
    START = "START = {} HZ"
    STOP = "STOP = {} HZ"
    
    # Amplitude control commands
    OSCILLATOR_1 = "OSC1 = {} DBM"
    
    # Resolution bandwidth commands
    RBW = "RBW = {} HZ"


class SweepTimings(Enum):
    """Standard timing values for different sweep resolutions."""
    
    RBW_10_HZ = 218  # seconds for 10 Hz resolution bandwidth
    RBW_100_HZ = 41  # seconds for 100 Hz resolution bandwidth


class DefaultValues:
    """Default configuration values for the application."""
    
    VISA_RESOURCE_NAME = 'GPIB0::17::INSTR'
    DEVICE_ID = 'HP4195A'
    VISA_TIMEOUT = 5000  # milliseconds
    DEFAULT_SPAN = 10000  # Hz
    DEFAULT_RBW_LOW_RES = 10  # Hz
    DEFAULT_RBW_NORMAL = 100  # Hz
