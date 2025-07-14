# HP4195A Reader - Code Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Module Structure](#module-structure)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Communication Protocol](#communication-protocol)
6. [GUI Components](#gui-components)
7. [Configuration Management](#configuration-management)
8. [Testing Framework](#testing-framework)
9. [Build and Deployment](#build-and-deployment)
10. [Development Guidelines](#development-guidelines)

## Architecture Overview

The HP4195A Reader is a multi-process Python application designed for communication with HP4195A Network/Spectrum Analyzers via GPIB interface. The application follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│ GUI Process (Main Thread)                                      │
│    ├── Main Window (PyQt5)                                     │
│    ├── Plot Canvas (Matplotlib)                                │
│    ├── Control Panels                                          │
│    └── Configuration Windows                                   │
└─────────────────┬───────────────────────────────────────────────┘
                  │ (Queues: Command, Message, Data, Logging)
┌─────────────────▼───────────────────────────────────────────────┐
│ Instrument Interface Process                                   │
│    ├── VISA/GPIB Communication                                 │
│    ├── Command Processing                                      │
│    ├── Data Acquisition                                        │
│    └── Response Handling                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Why Multiprocessing?

The HP4195A Reader uses **separate processes** to prevent the GUI from freezing during long instrument measurements (up to 4 minutes). This keeps the user interface responsive while hardware operations run in the background.

### Communication via Queues

**Four queues** connect the processes:

- **Command Queue**: GUI → Instrument ("start_acquisition", "connect", etc.)
- **Message Queue**: Instrument → GUI (True/False success status)  
- **Data Queue**: Instrument → GUI (measurement arrays)
- **Logging Queue**: All processes → Logging (error messages, status)

### How It Works

#### User Action Example
```python
# User clicks "Acquire Data"
self.command_queue.put('start_acquisition')    # Send command
if self.message_queue.get():                   # Wait for success
    self.graph.plot(force_refresh=True)        # Update plot
```

#### Instrument Response
```python
# Instrument process receives command
command = self.command_queue.get()             # Receive command
data = instrument.query("A?")                  # Get measurement  
self.message_queue.put(True)                   # Send success
self.data_queue.put(data)                      # Send data
```

### Key Benefits
- **Non-blocking GUI**: Interface stays responsive during 4-minute measurements
- **Crash isolation**: GPIB errors don't kill the GUI
- **Clean separation**: Hardware logic separate from user interface
- **Robust logging**: All processes log to same file safely

### Process Lifecycle

**Startup** (`main.py`):
1. **Create 4 communication queues** (`main.py` lines 19-22):
   ```python
   command_queue = Queue()
   message_queue = Queue()
   data_queue = Queue()
   logging_queue = Queue()
   ```

2. **Start instrument process** (`main.py` lines 24-26):
   ```python
   # Create and start the instrument interface process
   dp = hp4195a.HP4195AInterface(command_queue, message_queue, data_queue, logging_queue)
   dp.daemon = True    # Process dies when main process terminates
   dp.start()          # Creates new process and calls HP4195AInterface.run()
   ```

3. **Start GUI process** (`main.py` lines 28-29):
   ```python
   # Main GUI runs in the main process
   app = QtWidgets.QApplication(sys.argv)
   gp = MainWindow(command_queue, message_queue, data_queue, logging_queue)
   ```

4. **Start logging thread** (`main.py` lines 36-38):
   ```python
   # Logging runs as a thread within the main process
   lp = threading.Thread(target=ml.logger_thread, args=(logging_queue,))
   lp.daemon = True
   lp.start()
   ```

### Process Creation Details

**Instrument Process Creation**:
- **File**: `main.py`
- **Class**: `HP4195AInterface` (inherits from `multiprocessing.Process`)
- **Entry Point**: `HP4195AInterface.run()` method in `hp4195a_interface.py`
- **Process Type**: Daemon process (automatically terminates when main process exits)

**GUI Process**:
- **File**: `main.py` 
- **Runs in**: Main process (no separate process creation)
- **Framework**: PyQt5 application with event loop

**Logging Thread**:
- **File**: `multi_logging.py`
- **Function**: `logger_thread()`
- **Type**: Daemon thread within main process
- **Purpose**: Centralized log collection from all processes

**Operation**:
- GUI sends commands through queues
- Instrument process executes GPIB operations
- Data flows back through queues to update plots

**Shutdown**:
- GUI signals processes to terminate
- Instrument disconnects cleanly
- All processes exit gracefully

This design ensures the HP4195A Reader remains responsive and reliable even during complex, time-intensive measurement operations.

### Key Design Principles
- **Process Isolation**: GUI and instrument communication run in separate processes
- **Queue-based Communication**: Inter-process communication via multiprocessing queues
- **Modular Design**: Clear separation between GUI, logic, and hardware interface
- **Event-driven Architecture**: GUI responds to user actions and instrument data
- **Comprehensive Testing**: Unit tests for all major components

## Module Structure

```
src/
├── main.py                     # Application entry point
├── main_window.py             # Main window class and application setup
├── constants.py               # Application constants and enums
├── hp4195a_interface.py       # Instrument communication interface
├── multi_logging.py           # Multi-process logging setup
├── gui/                       # GUI components
│   ├── ui_generator.py        # UI element generation
│   ├── plot_canvas.py         # Matplotlib plotting widget
│   ├── machine_values_window.py # Machine configuration window
│   ├── amplitude_sweep_viewer.py # Single sweep display
│   ├── final_sweep_viewer.py  # Multi-sweep overlay display
│   └── help_window.py         # Help and documentation
├── logic/                     # Business logic
│   ├── ui_logic.py           # Main UI logic and event handling
│   ├── instrument_controls.py # Instrument control logic
│   ├── plot_controls.py      # Plot manipulation logic
│   └── file_handler.py       # File I/O operations
└── assets/
    └── icon.png              # Application icon
```

## Core Components

### 1. Main Application (`main.py`, `main_window.py`)

**Purpose**: Application initialization and main window setup.

**Key Classes**:
- `MainWindow`: Primary application window and process manager
- Application setup and configuration loading

**Responsibilities**:
- Initialize multiprocessing queues
- Start instrument interface process
- Set up GUI components
- Handle application lifecycle

### 2. Instrument Interface (`hp4195a_interface.py`)

**Purpose**: Hardware communication and command processing.

**Key Classes**:
- `HP4195AInterface`: Main instrument communication class

**Responsibilities**:
- VISA/GPIB connection management
- Command interpretation and execution
- Data acquisition from instrument
- Error handling and recovery

**Command Processing Flow**:
```python
def handle_command(self, command: str) -> None:
    """Process commands received from GUI"""
    if command == Commands.CONNECT.value:
        self._handle_connect()
    elif command == Commands.START_ACQUISITION.value:
        self._handle_start_acquisition()
    # ... other commands
```

### 3. GUI Framework (`gui/`)

**Purpose**: User interface components and visualization.

**Key Components**:

#### Plot Canvas (`plot_canvas.py`)
- Real-time data visualization using Matplotlib
- Dual-axis plotting (magnitude and phase)
- Peak marking and Q-factor display
- Data persistence and overlay capabilities

#### Machine Values Window (`machine_values_window.py`)
- Instrument configuration management
- Real-time parameter display
- Settings import/export (CSV/JSON)
- Quick setup functionality

#### Sweep Viewers
- `amplitude_sweep_viewer.py`: Individual sweep display
- `final_sweep_viewer.py`: Multi-sweep overlay with selection

### 4. Business Logic (`logic/`)

**Purpose**: Application logic and data processing.

#### UI Logic (`ui_logic.py`)
- Main application logic coordinator
- Event handling and state management
- Integration between GUI and instrument interface

#### Instrument Controls (`instrument_controls.py`)
- High-level instrument control operations
- Multi-step workflows (sweeps, measurements)
- Data validation and error handling

#### Plot Controls (`plot_controls.py`)
- Plot manipulation and analysis
- Peak detection algorithms
- Q-factor calculation

## Data Flow

### 1. Command Flow (GUI → Instrument)
```
User Action → UI Event → Command Queue → Instrument Interface → GPIB Command → HP4195A
```

### 2. Data Flow (Instrument → GUI)
```
HP4195A → GPIB Response → Instrument Interface → Data Queue → GUI → Plot Update
```

### 3. Queue Types
- **Command Queue**: GUI to instrument commands
- **Message Queue**: Status and success/failure messages
- **Data Queue**: Measurement data and responses
- **Logging Queue**: Multi-process logging coordination

## Communication Protocol

### GPIB Commands (defined in `constants.py`)

#### Query Commands
```python
QUERY_IDENTITY = "ID?"           # Instrument identification
QUERY_MAGNITUDE = "A?"           # Magnitude data
QUERY_PHASE = "B?"              # Phase data
QUERY_FREQUENCY = "X?"          # Frequency data
QUERY_CENTER = "CENTER?"        # Center frequency
QUERY_SPAN = "SPAN?"           # Frequency span
```

#### Control Commands
```python
CENTER = "CENTER = {} HZ"       # Set center frequency
SPAN = "SPAN = {} HZ"          # Set frequency span
RBW = "RBW = {} HZ"           # Set resolution bandwidth
OSCILLATOR_1 = "OSC1 = {} DBM" # Set oscillator amplitude
```

#### Sweep Commands
```python
SWEEP_MODE_SINGLE = "SWM2"      # Single sweep mode
SWEEP_TRIGGER = "SWTRG"         # Trigger sweep
```

### Command Processing Pattern
```python
# 1. GUI sends command
self.command_queue.put(Commands.START_ACQUISITION.value)

# 2. Instrument interface processes
def _handle_start_acquisition(self):
    success = self.acquire_all_data()
    self.message_queue.put(success)
    if success:
        self._send_data_to_queue()

# 3. GUI receives response
if self.message_queue.get():
    self.graph.plot(force_refresh=True)
```

## GUI Components

### Main Window Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Menu Bar: File | Tools | Help                               │
├─────────────────────────────────────────────────────────────┤
│ Connection Panel: [Connect] [Status]                       │
├─────────────────────────────────────────────────────────────┤
│ Control Panel: [Acquire] [Auto-find Peak] [Center Peak]    │
├─────────────────────────────────────────────────────────────┤
│ Plot Canvas: Real-time Matplotlib Display                  │
│              - Magnitude (yellow) and Phase (cyan) plots   │
│              - Peak markers and annotations                 │
│              - Q-factor fitting curves                     │
├─────────────────────────────────────────────────────────────┤
│ Input Controls: Frequency Settings and Amplitude Sweeps    │
├─────────────────────────────────────────────────────────────┤
│ Command Interface: Direct GPIB Command Entry               │
└─────────────────────────────────────────────────────────────┘
```

### Window Management
- **Modal dialogs**: Machine Values, Help windows
- **Persistent windows**: Amplitude sweep viewers
- **Memory management**: Proper window cleanup and reference handling

## Configuration Management

### Machine Configuration (`machine_values_window.py`)

**Features**:
- Real-time instrument parameter display
- Editable configuration table
- Import/Export functionality (CSV/JSON)
- Quick setup with auto-calculation

**Configuration Parameters**:
- Center Frequency (Hz)
- Frequency Span (Hz)
- Start/Stop Frequencies (Hz)
- Resolution Bandwidth (Hz)
- Oscillator Amplitude (dBm)
- Sweep Mode
- Connection Status

**File Formats**:

#### JSON Export Format
```json
{
  "hp4195a_configuration": {
    "center_frequency": 1000000.0,
    "span": 10000.0,
    "start_frequency": 995000.0,
    "stop_frequency": 1005000.0,
    "resolution_bandwidth": 100.0,
    "oscillator_1_amplitude": -10.0,
    "sweep_mode": "Single",
    "device_id": "HP4195A",
    "connection_status": "Connected"
  },
  "exported_at": "2025-07-14T14:15:46",
  "exported_by": "HP4195A Reader Application"
}
```

## Testing Framework

### Test Structure (`tests/`)
```
tests/
├── conftest.py                    # PyTest configuration and fixtures
├── test_backend.py               # Backend and integration tests
├── test_constants.py             # Constants and enums validation
├── test_hp4195a_interface.py     # Instrument interface tests
├── test_gui_logic.py             # GUI logic and event handling
├── test_machine_setup.py         # Configuration management tests
├── test_plot_controls.py         # Plot manipulation tests
├── test_file_handler.py          # File I/O operations tests
└── test_sweeping_amplitudes.py   # Amplitude sweep functionality
```

### Testing Patterns

#### Mock-based Testing
```python
@pytest.fixture
def mock_instrument():
    """Mock instrument interface for testing"""
    mock = Mock()
    mock.connected = True
    mock.command_queue = Mock()
    mock.message_queue = Mock()
    mock.data_queue = Mock()
    return mock
```

#### GUI Testing with PyQt
```python
def test_machine_values_window(qtbot):
    """Test machine values window functionality"""
    window = MachineValuesWindow()
    qtbot.addWidget(window)
    
    # Test user interactions
    window.center_freq_input.setText("1000000")
    window.populate_from_quick_setup()
    
    # Verify results
    assert window.machine_values['center_frequency'] == 1000000.0
```

### Test Coverage Areas
- **Unit Tests**: Individual component functionality
- **Integration Tests**: Component interaction and data flow
- **GUI Tests**: User interface and event handling
- **Error Handling**: Exception scenarios and recovery
- **Configuration**: Import/export and validation

## Build and Deployment

### Development Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python src/main.py

# Run tests
python -m pytest

# Build executable
python setup.py build
```

### Executable Build (`setup.py`)
- Uses cx_Freeze for Python-to-executable compilation
- Includes all dependencies and assets
- Creates standalone distribution in `build/` directory

### Requirements Management
- `requirements.txt`: Production dependencies
- Development dependencies managed separately
- Version pinning for stability

## Development Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Comprehensive docstrings for all public methods
- Clear variable and function naming

### Error Handling
```python
def acquire_data(self) -> bool:
    """Acquire data with proper error handling"""
    try:
        response = self.instrument.query("A?")
        data = np.fromstring(response, dtype=float, sep=',')
        if len(data) > 0:
            self.mag_data = data.tolist()
            return True
        return False
    except (ValueError, AttributeError) as e:
        self.logger.error(f"Error acquiring data: {e}")
        return False
```

### Logging Best Practices
- Use structured logging with appropriate levels
- Multi-process logging coordination
- Log file rotation and management
- Performance-sensitive operations logged at DEBUG level

### Performance Considerations
- Non-blocking GUI operations
- Efficient data transfer between processes
- Memory management for large datasets
- Optimized plotting for real-time updates

### Security Considerations
- Input validation for user-provided data
- Safe file I/O operations
- GPIB command sanitization
- Error message sanitization (no sensitive data exposure)

---

## Appendix

### Common Development Tasks

#### Adding a New GPIB Command
1. Add command to `GPIBCommands` enum in `constants.py`
2. Implement handler in `hp4195a_interface.py`
3. Add GUI control in appropriate UI module
4. Write tests for new functionality

#### Adding a New GUI Window
1. Create window class inheriting from appropriate PyQt5 base
2. Implement UI layout and event handlers
3. Integrate with main application logic
4. Add tests for window functionality

#### Extending Data Export Formats
1. Add format support to `file_handler.py`
2. Update machine values window export options
3. Implement format-specific serialization
4. Add tests for new format

---

*Last Updated: July 14, 2025*
*Version: 1.0*