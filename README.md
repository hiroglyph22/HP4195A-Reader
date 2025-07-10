# HP4195A Reader

A Python program for connecting to and interfacing with a HP4195A Network/Spectrum Analyser to view and save the data.

## Requirements

### Hardware
- HP4195A Network/Spectrum Analyser
- NI HP-IB GPIB-USB-HS IEEE488 Controller

### Software
- Python 3.0 +
- PyQt5 (+ PyQtWebEngine)
- PyVISA
- NumPy
- Matplotlib
- Markdown
- cx_Freeze
- Scipy

### Supporting Documents
The following documents provide useful information regarding the 4195A Network/Spectrum Analyser and the Prologix GPIB-ETHERNET Controller including GPIB command definitions and data register names:

* [4195A-4395A GPIB Command Correspondence Table](http://www.tentech.ca/downloads/hardware/HP4195A/4195A-4395A%20GPIB%20Command%20Correspondance.pdf)

* [4195A Network/Spectrum Analyser Operation Manual](https://www.keysight.com/upload/cmc_upload/All/04195_90000_final.pdf)

### Installing

To run the program install the dependencies as specified above using pip, conda or a similar package management system. Then clone this repository, navigate to the project directory in a command terminal and type

```
python src/main.py
```

The software can also be built into an executable with cx_Freeze. From the project directory run the following command in a terminal window

```
python setup.py build
```

### Testing

```
python -m pytest
```

### Todo

- [x]  Get continuous plot
    - [x]  Automatically updates plot but also needs to automatically acquire data
- [x]  Auto Span and Center functionality
    - [x]  Find peak of the graph
    - [x]  Add pause and resume auto-updating
    - [x]  Figure out how to span with GPIB
    - [x]  Figure out how to center with GPIB
    - [x]  Get estimated input from user
        - [x]  Add button
    - [x]  Do a single sweep at 10 Hz
- [x]  Auto Span and Center Update
    - [x]  Add additional low-resolution sweep that makes it look better
- [x]  Find how long it takes to sweep given a certain resolution
- [x]  Finding q-factor
- [ ]  Overlapping graph
    - [x]  Get user input for range of frequencies
    - [ ]  Change amplitude and do a sweep per certain amplitude
    - [ ]  Have graph overlay for amplitude frequency while the next amplitude curve is being swept
    - [ ]  Pop up another window when data for all range of amplitudes are selected
- [x]  Put UI generating function calls in UI_generator
- [x]  Add initial test suite
    - [ ] Update test_set_output_power in tests
- [ ]  Clean up hp4195a_interface.py

### License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
