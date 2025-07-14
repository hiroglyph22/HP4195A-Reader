# HP4195A Reader - User Operating Guide

## Document Information
- **Document Title**: HP4195A Reader User Operating Guide
- **Version**: 1.0
- **Date**: July 14, 2025

## Table of Contents
1. [Getting Started](#getting-started)
2. [Basic Operation](#basic-operation)
3. [Advanced Features](#advanced-features)
4. [Data Management](#data-management)
5. [Troubleshooting](#troubleshooting)

---

## 1. Getting Started

### Prerequisites
- HP4195A Network/Spectrum Analyzer connected via GPIB
- HP4195A Reader software installed
- GPIB interface connected to computer

### First Launch
1. **Start the Application**
   - Double-click the HP4195A Reader icon
   - Wait for the main window to load

2. **Connect to Instrument**
   - Click the **Connect** button
   - Wait for "Connected" status to appear
   - If connection fails, check GPIB cables and instrument power

---

## 2. Basic Operation

### Taking a Simple Measurement

1. **Connect to Instrument**
   - Click **Connect** button
   - Verify "Connected" status

2. **Acquire Data**
   - Click **Acquire Data** button
   - Wait for plot to update with measurement data
   - Yellow line = Magnitude, Cyan line = Phase

3. **Find Peak**
   - Click **Auto-find Peak** to locate maximum response
   - Peak will be marked with red annotation

### Setting Frequency Range

#### Method 1: Center and Span
1. Enter **Center Frequency** (Hz): e.g., `1000000` for 1 MHz
2. Enter **Span** (Hz): e.g., `10000` for 10 kHz
3. Click **Peak Scan** button

#### Method 2: Start and Stop
1. Enter **Start Frequency** (Hz): e.g., `995000`
2. Enter **Stop Frequency** (Hz): e.g., `1005000`
3. Click **Range Scan** button

### Machine Configuration
1. **Open Configuration**
   - Go to **Tools** → **Machine Setup**

2. **Quick Setup**
   - Enter Center Frequency, Span, Resolution Bandwidth
   - Click **Populate Table from Quick Setup**
   - Click **Apply Settings**

3. **Save Configuration**
   - Click **Export to JSON**
   - Choose filename and location

---

## 3. Advanced Features

### High-Resolution Measurements
- Click **Low Res Sweep** for high-precision measurements
- Takes longer (up to 4 minutes) but provides better accuracy
- Use for critical frequency measurements

### Q-Factor Analysis
1. Take measurement of resonant device
2. Click **Auto-find Peak** to locate resonance
3. Click **Q Factor** button
4. Review fitted curve and calculated Q-factor value

### Amplitude Sweeps
1. **Setup Parameters**
   - Start Amplitude (dBm): e.g., `-20`
   - Stop Amplitude (dBm): e.g., `0`
   - Step Size (dBm): e.g., `2`
   - Resolution: `100 Hz` (normal) or `10 Hz` (high precision)

2. **Run Sweep**
   - Click **Sweeping Range of Amplitudes**
   - Choose directory to save data
   - Monitor progress through individual windows
   - Final overlay window shows all amplitudes

### Continuous Monitoring
- Click **Start Auto-Update** for continuous measurements
- Useful for monitoring system stability
- Click **Stop Auto-Update** to stop

---

## 4. Data Management

### Saving Data
1. **Manual Save**
   - Go to **File** → **Save Data**
   - Choose CSV format for data analysis
   - Use descriptive filename with date

2. **Automatic Save** (Amplitude Sweeps)
   - Data automatically saved during amplitude sweeps
   - Files saved in directory you selected
   - Individual CSV file for each amplitude level

### Configuration Management
1. **Export Settings**
   - **Tools** → **Machine Setup** → **Export to JSON**
   - Save current instrument configuration

2. **Import Settings**
   - **Tools** → **Machine Setup** → **Import from JSON**
   - Load previously saved configuration

### File Naming Convention
- Use format: `Component_TestType_YYYYMMDD_HHMM`
- Examples:
  - `Filter_A_FreqResponse_20250714_1430.csv`
  - `Oscillator_B_AmplitudeSweep_20250714_1545.csv`

---

## 5. Troubleshooting

### Connection Problems

**Problem**: Cannot connect to HP4195A
- **Check**: GPIB cable connections
- **Check**: HP4195A is powered on and warmed up
- **Try**: Restart the software
- **Try**: Check GPIB address (default: 17)

### Measurement Issues

**Problem**: No data on plot
- **Check**: Input signal is connected and appropriate level
- **Try**: Click **Acquire Data** again
- **Check**: Frequency settings match your signal

**Problem**: Measurement takes too long
- **Cause**: High resolution bandwidth (10 Hz) takes longer
- **Solution**: Use 100 Hz resolution for normal measurements
- **Solution**: Reduce frequency span to minimum needed

**Problem**: Noisy or distorted data
- **Check**: Input signal level (may be too high)
- **Check**: Proper 50Ω impedance matching
- **Try**: Reduce input signal amplitude

### Software Issues

**Problem**: Plot not updating
- **Try**: Click **Acquire Data** again
- **Try**: Restart the application
- **Check**: Connection status

**Problem**: Application freezes
- **Wait**: Allow up to 4 minutes for high-resolution measurements
- **Try**: Restart application if truly frozen

---

## Quick Reference

### Common Operations
- **F1**: Help window
- **Connect**: Establish instrument communication
- **Acquire Data**: Take single measurement
- **Auto-find Peak**: Locate maximum response
- **Peak Scan**: Measure around center frequency
- **Range Scan**: Measure between start/stop frequencies

### Typical Measurement Times
- **Normal Resolution (100 Hz)**: ~30 seconds
- **High Resolution (10 Hz)**: ~4 minutes
- **Amplitude Sweep**: Varies by number of steps

### Default Settings
- **GPIB Address**: 17
- **Resolution Bandwidth**: 100 Hz
- **Default Span**: 10 kHz

---

*For technical support or detailed specifications, refer to the CODE_DOCUMENTATION.md file.*

**Last Updated**: July 14, 2025