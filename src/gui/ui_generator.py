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
        control_panel_layout.setSpacing(10)
        control_panel_layout.setAlignment(QtCore.Qt.AlignTop) # Align widgets to the top

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
        plot_layout.addStretch()
        plot_layout.addWidget(self.p_cb)
        plot_layout.addWidget(self.mag_cb)
        plot_layout.addWidget(self.phase_cb)
        plot_layout.addStretch()
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
        freq_group = self.generate_frequency_sweep_section()
        control_panel_layout.addWidget(freq_group)

        # --- Amplitude Sweep Controls ---
        amp_group = self.generate_amplitude_sweep_section()
        control_panel_layout.addWidget(amp_group)
        
        control_panel_layout.addStretch(1) # Pushes everything else up

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
        control_panel_widget.setMinimumWidth(420) # Set a minimum width to prevent crushing
        return control_panel_widget

    def generate_frequency_sweep_section(self):
        group = QtWidgets.QGroupBox("Frequency Sweep")
        # Use a grid layout for perfect column alignment
        layout = QtWidgets.QGridLayout()
        # THIS IS THE FIX: Make the second column (inputs) stretchable, 
        # leaving the first column (labels) at its preferred size.
        layout.setColumnStretch(1, 1)

        # Row 0: Peak Freq
        layout.addWidget(QtWidgets.QLabel("Est. Peak Freq (Hz):"), 0, 0)
        self.peak_freq_input = QtWidgets.QLineEdit()
        layout.addWidget(self.peak_freq_input, 0, 1)

        # Row 1: Span
        layout.addWidget(QtWidgets.QLabel("Span (Hz):"), 1, 0)
        self.span_input = QtWidgets.QLineEdit("10000")
        layout.addWidget(self.span_input, 1, 1)

        # Row 2: Button
        self.peak_scan_button = QtWidgets.QPushButton("Scan Around Peak")
        layout.addWidget(self.peak_scan_button, 2, 0, 1, 2) # Span button across both columns

        # Row 3: Separator
        layout.addWidget(self.create_separator(), 3, 0, 1, 2)

        # Row 4: Start Freq
        layout.addWidget(QtWidgets.QLabel("Start Freq (Hz):"), 4, 0)
        self.start_freq_input = QtWidgets.QLineEdit()
        layout.addWidget(self.start_freq_input, 4, 1)

        # Row 5: Stop Freq
        layout.addWidget(QtWidgets.QLabel("Stop Freq (Hz):"), 5, 0)
        self.stop_freq_input = QtWidgets.QLineEdit()
        layout.addWidget(self.stop_freq_input, 5, 1)

        # Row 6: Button
        self.range_scan_button = QtWidgets.QPushButton("Scan Frequency Range")
        layout.addWidget(self.range_scan_button, 6, 0, 1, 2)

        # Row 7: Separator
        layout.addWidget(self.create_separator(), 7, 0, 1, 2)

        # Row 8: Button
        self.low_res_sweep_button = QtWidgets.QPushButton("Full Low-Res Sweep")
        layout.addWidget(self.low_res_sweep_button, 8, 0, 1, 2)

        group.setLayout(layout)
        return group

    def generate_amplitude_sweep_section(self):
        group = QtWidgets.QGroupBox("Amplitude Sweep")
        # Use a grid layout for stable columns
        layout = QtWidgets.QGridLayout()
        layout.setColumnStretch(1, 1) # Make the input column stretchable

        layout.addWidget(QtWidgets.QLabel("Start Amplitude (dBm):"), 0, 0)
        self.start_amplitude_input = QtWidgets.QLineEdit("-10")
        layout.addWidget(self.start_amplitude_input, 0, 1)

        layout.addWidget(QtWidgets.QLabel("Stop Amplitude (dBm):"), 1, 0)
        self.stop_amplitude_input = QtWidgets.QLineEdit("0")
        layout.addWidget(self.stop_amplitude_input, 1, 1)

        layout.addWidget(QtWidgets.QLabel("Step (dBm):"), 2, 0)
        self.step_amplitude_input = QtWidgets.QLineEdit("1")
        layout.addWidget(self.step_amplitude_input, 2, 1)
        
        self.sweeping_range_of_amplitudes_button = QtWidgets.QPushButton("Start Amplitude Sweep")
        layout.addWidget(self.sweeping_range_of_amplitudes_button, 3, 0, 1, 2)

        group.setLayout(layout)
        return group

    def generate_command_section(self):
        group = QtWidgets.QGroupBox("Direct GPIB Command")
        # Use a grid layout for stable columns
        layout = QtWidgets.QGridLayout()
        layout.setColumnStretch(1, 1)

        layout.addWidget(QtWidgets.QLabel("Command:"), 0, 0)
        self.command_box = QtWidgets.QLineEdit()
        layout.addWidget(self.command_box, 0, 1)

        self.command_button = QtWidgets.QPushButton("Send Command")
        layout.addWidget(self.command_button, 1, 0, 1, 2)

        layout.addWidget(QtWidgets.QLabel("Response:"), 2, 0)
        self.response_box = QtWidgets.QLineEdit()
        self.response_box.setReadOnly(True)
        layout.addWidget(self.response_box, 2, 1)
        
        group.setLayout(layout)
        return group
        
    def create_separator(self):
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        return line

    def set_tooltips_and_connections(self):
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
        self.file_menu = self.main_menu.addMenu('&File')
        self.about_menu = self.main_menu.addMenu('&About')
        save_action = QtWidgets.QAction('&Save As...', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file_dialog)
        self.file_menu.addAction(save_action)
        exit_action = QtWidgets.QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)
        help_action = QtWidgets.QAction('&Help', self)
        help_action.setShortcut('Ctrl+H')
        help_action.triggered.connect(self.help_dialog)
        self.about_menu.addAction(help_action)
