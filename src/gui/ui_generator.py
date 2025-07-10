from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon

class UIGenerator:
    '''
    A mixin class to hold all the UI generation methods, keeping the
    MainWindow class cleaner and focused on logic.
    '''
    def generate_UI(self):
        """
        Generates the entire UI and returns the main control panel widget.
        """
        self.generate_menu_bar()

        # Main vertical layout for the entire control panel on the right
        control_panel_layout = QtWidgets.QVBoxLayout()

        # --- Top-level Action Buttons ---
        actions_group = QtWidgets.QGroupBox("Main Actions")
        actions_layout = QtWidgets.QGridLayout()
        self.connect_button = QtWidgets.QPushButton('Connect')
        self.acquire_button = QtWidgets.QPushButton('Acquire Data')
        self.save_button = QtWidgets.QPushButton('Save Data')
        self.pause_button = QtWidgets.QPushButton('Pause')
        self.pause_button.setCheckable(True)
        actions_layout.addWidget(self.connect_button, 0, 0)
        actions_layout.addWidget(self.acquire_button, 0, 1)
        actions_layout.addWidget(self.save_button, 1, 0)
        actions_layout.addWidget(self.pause_button, 1, 1)
        actions_group.setLayout(actions_layout)
        control_panel_layout.addWidget(actions_group)

        # --- Plotting Controls ---
        plot_group = QtWidgets.QGroupBox("Plotting Controls")
        plot_layout = QtWidgets.QHBoxLayout()
        self.p_cb = QtWidgets.QCheckBox('Persist')
        self.mag_cb = QtWidgets.QCheckBox('Magnitude')
        self.mag_cb.setChecked(True)
        self.phase_cb = QtWidgets.QCheckBox('Phase')
        self.phase_cb.setChecked(True)
        plot_layout.addWidget(self.p_cb)
        plot_layout.addWidget(self.mag_cb)
        plot_layout.addWidget(self.phase_cb)
        plot_group.setLayout(plot_layout)
        control_panel_layout.addWidget(plot_group)

        # --- Peak Analysis ---
        peak_group = QtWidgets.QGroupBox("Peak Analysis")
        peak_layout = QtWidgets.QGridLayout()
        self.autofind_peak_button = QtWidgets.QPushButton('Auto-find Peak')
        self.center_peak_button = QtWidgets.QPushButton('Center on Peak')
        self.q_factor_button = QtWidgets.QPushButton('Calculate Q-Factor')
        peak_layout.addWidget(self.autofind_peak_button, 0, 0, 1, 2)
        peak_layout.addWidget(self.center_peak_button, 1, 0)
        peak_layout.addWidget(self.q_factor_button, 1, 1)
        peak_group.setLayout(peak_layout)
        control_panel_layout.addWidget(peak_group)

        # --- Frequency Sweep Controls ---
        freq_group = QtWidgets.QGroupBox("Frequency Sweep")
        freq_layout = QtWidgets.QFormLayout()
        self.peak_freq_input = QtWidgets.QLineEdit()
        self.span_input = QtWidgets.QLineEdit("10000")
        self.peak_scan_button = QtWidgets.QPushButton("Scan around Peak")
        self.start_freq_input = QtWidgets.QLineEdit()
        self.stop_freq_input = QtWidgets.QLineEdit()
        self.range_scan_button = QtWidgets.QPushButton("Scan Frequency Range")
        self.low_res_sweep_button = QtWidgets.QPushButton("Full Low-Res Sweep")
        freq_layout.addRow("Est. Peak Freq (Hz):", self.peak_freq_input)
        freq_layout.addRow("Span (Hz):", self.span_input)
        freq_layout.addRow(self.peak_scan_button)
        freq_layout.addRow(QtWidgets.QLabel("--- OR ---"))
        freq_layout.addRow("Start Freq (Hz):", self.start_freq_input)
        freq_layout.addRow("Stop Freq (Hz):", self.stop_freq_input)
        freq_layout.addRow(self.range_scan_button)
        freq_layout.addRow(QtWidgets.QLabel("--- OR ---"))
        freq_layout.addRow(self.low_res_sweep_button)
        freq_group.setLayout(freq_layout)
        control_panel_layout.addWidget(freq_group)

        # --- Amplitude Sweep Controls ---
        amp_group = self.generate_sweeping_range_of_amplitudes_section()
        control_panel_layout.addWidget(amp_group)
        
        control_panel_layout.addStretch(1) # Pushes everything up

        # --- GPIB Command Section ---
        command_group = self.generate_command_section()
        control_panel_layout.addWidget(command_group)

        # --- Set Tooltips and Connections ---
        self.set_tooltips_and_connections()
        
        # --- Set initial button states ---
        self.set_initial_button_states()

        # Create the main widget to hold the layout
        control_panel_widget = QtWidgets.QWidget()
        control_panel_widget.setLayout(control_panel_layout)
        return control_panel_widget

    def generate_sweeping_range_of_amplitudes_section(self):
        group = QtWidgets.QGroupBox("Amplitude Sweep")
        layout = QtWidgets.QFormLayout()
        self.start_amplitude_input = QtWidgets.QLineEdit("-20")
        self.stop_amplitude_input = QtWidgets.QLineEdit("0")
        self.step_amplitude_input = QtWidgets.QLineEdit("1")
        self.sweeping_range_of_amplitudes_button = QtWidgets.QPushButton("Start Amplitude Sweep")
        layout.addRow("Start Amplitude (dBm):", self.start_amplitude_input)
        layout.addRow("Stop Amplitude (dBm):", self.stop_amplitude_input)
        layout.addRow("Step (dBm):", self.step_amplitude_input)
        layout.addRow(self.sweeping_range_of_amplitudes_button)
        group.setLayout(layout)
        return group

    def generate_command_section(self):
        group = QtWidgets.QGroupBox("Direct GPIB Command")
        layout = QtWidgets.QFormLayout()
        self.command_box = QtWidgets.QLineEdit()
        self.response_box = QtWidgets.QLineEdit()
        self.response_box.setReadOnly(True)
        self.command_button = QtWidgets.QPushButton("Send Command")
        layout.addRow("Command:", self.command_box)
        layout.addRow(self.command_button)
        layout.addRow("Response:", self.response_box)
        group.setLayout(layout)
        return group

    def set_tooltips_and_connections(self):
        # Connections
        self.connect_button.clicked.connect(self.connect)
        self.acquire_button.clicked.connect(self.start_acquisition)
        self.save_button.clicked.connect(self.save_file_dialog)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.p_cb.stateChanged.connect(self.change_persist_state)
        self.mag_cb.stateChanged.connect(self.change_mag_state)
        self.phase_cb.stateChanged.connect(self.change_phase_state)
        self.autofind_peak_button.clicked.connect(self.autofind_peak)
        self.center_peak_button.clicked.connect(self.center_on_peak)
        self.q_factor_button.clicked.connect(self.calculate_q_factor)
        self.peak_scan_button.clicked.connect(self.start_peak_scan)
        self.range_scan_button.clicked.connect(self.start_range_scan)
        self.low_res_sweep_button.clicked.connect(self.start_low_res_sweep)
        self.sweeping_range_of_amplitudes_button.clicked.connect(self.start_sweeping_range_of_amplitudes)
        self.command_box.textChanged.connect(self.toggle_connect_button)
        self.command_button.clicked.connect(self.send_command)
        
        # Tooltips
        self.connect_button.setToolTip('Connect to a HP4195A Network Analyser')
        self.acquire_button.setToolTip('Acquire a single trace from the instrument')
        self.save_button.setToolTip('Save the current trace data to a CSV file')
        self.pause_button.setToolTip('Pause or resume continuous data acquisition')
        self.p_cb.setToolTip('Overlay new traces on top of old ones')
        self.autofind_peak_button.setToolTip('Automatically find and mark the peak magnitude')
        self.center_peak_button.setToolTip('Set the instrument\'s center frequency to the current peak')
        self.q_factor_button.setToolTip('Fit a curve and calculate the Q-Factor from the peak')
        self.sweeping_range_of_amplitudes_button.setToolTip('Sweep across a range of amplitude levels, saving data at each step.')
        self.command_button.setToolTip('Send a raw GPIB command to the instrument')

    def set_initial_button_states(self):
        self.acquire_button.setEnabled(False)
        self.autofind_peak_button.setEnabled(False)
        self.center_peak_button.setEnabled(False)
        self.q_factor_button.setEnabled(False)
        self.peak_scan_button.setEnabled(False)
        self.low_res_sweep_button.setEnabled(False)
        self.range_scan_button.setEnabled(False)
        self.command_button.setEnabled(False)
        self.sweeping_range_of_amplitudes_button.setEnabled(False)

    def generate_menu_bar(self):
        self.main_menu = self.menuBar()
        self.file_menu = self.main_menu.addMenu('File')
        self.about_menu = self.main_menu.addMenu('About')
        # Menu actions
        save_action = QtWidgets.QAction('Save As...', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file_dialog)
        self.file_menu.addAction(save_action)
        
        exit_action = QtWidgets.QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)

        help_action = QtWidgets.QAction('Help', self)
        help_action.setShortcut('Ctrl+H')
        help_action.triggered.connect(self.help_dialog)
        self.about_menu.addAction(help_action)
