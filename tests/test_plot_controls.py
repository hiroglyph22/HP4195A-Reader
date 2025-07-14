import pytest
import numpy as np
from unittest.mock import MagicMock

def test_autofind_peak(app):
    """
    Tests that the autofind_peak method correctly identifies the peak
    in a given dataset and updates the graph's state.
    """
    # Arrange
    # Create sample data with a clear peak at 3000 Hz
    freq_data = np.array([1000, 2000, 3000, 4000, 5000])
    mag_data = np.array([-20, -10, 5, -12, -22])
    
    # Assign the data directly to the app's graph object.
    # The 'app' fixture creates a real MainWindow with a real PlotCanvas.
    app.graph.freq_data = freq_data
    app.graph.mag_data = mag_data

    # To test the interaction, we mock the plot method on the real graph instance
    app.graph.plot = MagicMock()

    # Act
    app.autofind_peak()

    # Assert
    # Check that the graph object's state was updated with the correct peak values
    assert app.graph.peak_freq == 3000
    assert app.graph.peak_mag == 5
    
    # Check that the relevant UI buttons were enabled
    assert app.center_peak_button.isEnabled()
    assert app.q_factor_button.isEnabled()
    
    # Check that the plot was updated
    app.graph.plot.assert_called_once()

def test_center_on_peak(app, queues, mocker):
    """
    Tests that the center_on_peak method sends the correct command
    to the backend.
    """
    # Arrange
    # Simulate that a peak has already been found and its frequency stored
    peak_frequency = 4500.0
    app.graph.peak_freq = peak_frequency
    
    # The start_acquisition method will block waiting for a message.
    # We mock the method itself to prevent the block and check that it's called.
    app.start_acquisition = MagicMock()

    # Act
    app.center_on_peak()

    # Assert
    # Check that the correct command and frequency were sent to the backend
    assert queues["command"].get() == 'set_center_frequency'
    assert queues["command"].get() == peak_frequency
    
    # Check that a new data acquisition was triggered
    app.start_acquisition.assert_called_once()


def test_calculate_q_factor(app):
    """
    Tests that the Q-factor is calculated correctly by fitting a curve
    to the data.
    """
    # Arrange
    # Define the parameters for a perfect Lorentzian peak
    center_freq = 10000.0
    fwhm = 100.0  # Full Width at Half Maximum
    amplitude = 1.0 # Linear amplitude (0 dBm)

    # Generate realistic frequency and magnitude data based on the Lorentzian formula
    freq_data = np.linspace(center_freq - 5 * fwhm, center_freq + 5 * fwhm, 401)
    y_linear = amplitude * (fwhm/2)**2 / ((freq_data - center_freq)**2 + (fwhm/2)**2)
    mag_data_dbm = 10 * np.log10(y_linear)

    # Set up the app's graph with the data and the known peak
    app.graph.freq_data = freq_data
    app.graph.mag_data = mag_data_dbm
    app.graph.peak_freq = center_freq
    app.graph.peak_mag = 10 * np.log10(amplitude)

    # Mock the methods on the graph object that would be called
    app.graph.set_q_factor_data = MagicMock()
    app.graph.plot = MagicMock()

    # Act
    app.calculate_q_factor()

    # Assert
    # The theoretical Q-factor is center_freq / fwhm
    expected_q_factor = center_freq / fwhm
    
    # Check that the graph's set_q_factor_data method was called
    app.graph.set_q_factor_data.assert_called_once()
    
    # Get the arguments that were passed to the method
    args, kwargs = app.graph.set_q_factor_data.call_args
    
    # The calculated Q-factor is the third argument
    calculated_q_factor = args[2]
    
    # Check that the calculated Q-factor is very close to the theoretical value
    assert abs(calculated_q_factor - expected_q_factor) < 0.01

    # Check that the plot was updated
    app.graph.plot.assert_called_once()
