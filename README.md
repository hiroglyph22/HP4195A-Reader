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

### Supporting Documents
The following documents provide useful information regarding the 4195A Network/Spectrum Analyser and the Prologix GPIB-ETHERNET Controller including GPIB command definitions and data register names:

* [4195A-4395A GPIB Command Correspondence Table](http://www.tentech.ca/downloads/hardware/HP4195A/4195A-4395A%20GPIB%20Command%20Correspondance.pdf)

* [4195A Network/Spectrum Analyser Operation Manual](https://www.keysight.com/upload/cmc_upload/All/04195_90000_final.pdf)

### Installing

To run the program install the dependencies as specified above using pip, conda or a similar package management system. Then clone this repository, navigate to the project directory in a command terminal and type

```
python hp4195a_reader.py
```

The software can also be built into an executable with cx_Freeze. From the project directory run the following command in a terminal window

```
python setup.py build
```

### License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
