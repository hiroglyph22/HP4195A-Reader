from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon

class UIGenerator:
    '''
    A mixin class to hold all the UI generation methods, keeping the
    MainWindow class cleaner and focused on logic.
    '''
    def generate_menu_bar(self):
        self.main_menu = self.menuBar()
        self.file_menu = self.main_menu.addMenu('File')
        self.about_menu = self.main_menu.addMenu('About')
        self.generate_menu_save_button()
        self.generate_menu_exit_button()
        self.generate_menu_help_button()

    def generate_menu_save_button(self):
        self.save_button_action = QtWidgets.QAction(QIcon('exit24.png'), 'Save As...', self)
        self.save_button_action.setShortcut('Ctrl+S')
        self.save_button_action.setStatusTip('Save As')
        self.save_button_action.triggered.connect(self.save_file_dialog)
        self.file_menu.addAction(self.save_button_action)

    def generate_menu_exit_button(self):
        self.exit_button = QtWidgets.QAction(QIcon('exit24.png'), 'Exit', self)
        self.exit_button.setShortcut('Ctrl+Q')
        self.exit_button.setStatusTip('Exit application')
        self.exit_button.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_button)

    def generate_menu_help_button(self):
        self.help_button = QtWidgets.QAction(QIcon('exit24.png'), 'Help', self)
        self.help_button.setShortcut('Ctrl+H')
        self.help_button.setStatusTip('Help')
        self.help_button.triggered.connect(self.help_dialog)
        self.about_menu.addAction(self.help_button)

    def generate_connection_button(self):
        self.connect_button = QtWidgets.QPushButton('Connect', self)
        self.connect_button.setToolTip('Connect to a HP4195A Network Analyser')
        self.connect_button.move(1720, 30)
        self.connect_button.resize(180, 100)
        self.connect_button.clicked.connect(self.connect)

    def generate_acquire_button(self):
        self.acquire_button = QtWidgets.QPushButton('Acquire Data', self)
        self.acquire_button.setToolTip('Acquire data from a HP4195A Network Analyser')
        self.acquire_button.move(1720, 130)
        self.acquire_button.resize(180, 100)
        self.acquire_button.clicked.connect(self.start_acquisition)

    def generate_save_button(self):
        self.save_button = QtWidgets.QPushButton('Save', self)
        self.save_button.setToolTip('Save the data')
        self.save_button.move(1720, 230)
        self.save_button.resize(180, 100)
        self.save_button.clicked.connect(self.save_file_dialog)

    def generate_autofind_peak_button(self):
        self.autofind_peak_button = QtWidgets.QPushButton('Auto-find Peak', self)
        self.autofind_peak_button.setToolTip('Automatically find and mark the peak magnitude')
        self.autofind_peak_button.move(1720, 330)
        self.autofind_peak_button.resize(180, 100)
        self.autofind_peak_button.clicked.connect(self.autofind_peak)

    def generate_pause_button(self):
        self.pause_button = QtWidgets.QPushButton('Pause', self)
        self.pause_button.setToolTip('Pause or resume continuous data acquisition')
        self.pause_button.move(1720, 430)
        self.pause_button.resize(180, 100)
        self.pause_button.setCheckable(True)
        self.pause_button.clicked.connect(self.toggle_pause)

    def generate_center_on_peak_button(self):
        self.center_peak_button = QtWidgets.QPushButton('Center on Peak', self)
        self.center_peak_button.setToolTip('Set the center frequency to the current peak')
        self.center_peak_button.move(1720, 530)
        self.center_peak_button.resize(180, 100)
        self.center_peak_button.clicked.connect(self.center_on_peak)

    def generate_q_factor_button(self):
        self.q_factor_button = QtWidgets.QPushButton('Calculate Q-Factor', self)
        self.q_factor_button.setToolTip('Fit a curve and calculate the Q-Factor from the peak')
        self.q_factor_button.move(1720, 630)
        self.q_factor_button.resize(180, 100)
        self.q_factor_button.clicked.connect(self.calculate_q_factor)

    def generate_persistance_checkbox(self):
        self.p_cb = QtWidgets.QCheckBox('Persist', self)
        self.p_cb.resize(100, 30)
        self.p_cb.move(10, 900)
        self.p_cb.setToolTip('Set display to persist')
        self.p_cb.stateChanged.connect(self.change_persist_state)

    def generate_mag_enable_checkbox(self):
        self.mag_cb = QtWidgets.QCheckBox('Magnitude', self)
        self.mag_cb.toggle()
        self.mag_cb.resize(100, 30)
        self.mag_cb.move(100, 900)
        self.mag_cb.setToolTip('Display magnitude data')
        self.mag_cb.stateChanged.connect(self.change_mag_state)

    def generate_phase_enable_checkbox(self):
        self.phase_cb = QtWidgets.QCheckBox('Phase', self)
        self.phase_cb.toggle()
        self.phase_cb.resize(100, 30)
        self.phase_cb.move(210, 900)
        self.phase_cb.setToolTip('Display phase data')
        self.phase_cb.stateChanged.connect(self.change_phase_state)

    def generate_peak_scan_section(self):
        self.peak_scan_label = QtWidgets.QLabel('Est. Peak Freq (Hz):', self)
        self.peak_scan_label.resize(120, 30)
        self.peak_scan_label.move(10, 935)
        self.peak_freq_input = QtWidgets.QLineEdit(self)
        self.peak_freq_input.move(140, 935)
        self.peak_freq_input.resize(200, 30)

        self.span_label = QtWidgets.QLabel('Span (Hz):', self)
        self.span_label.resize(120, 30)
        self.span_label.move(350, 935)
        self.span_input = QtWidgets.QLineEdit(self)
        self.span_input.setText('10000')
        self.span_input.move(450, 935)
        self.span_input.resize(200, 30)

        self.peak_scan_button = QtWidgets.QPushButton('Scan', self)
        self.peak_scan_button.setToolTip('Set center and span to find a peak')
        self.peak_scan_button.move(660, 935)
        self.peak_scan_button.resize(180, 30)
        self.peak_scan_button.clicked.connect(self.start_peak_scan)
        
    def generate_low_res_sweep_button(self):
        self.low_res_sweep_button = QtWidgets.QPushButton('Low Res Sweep', self)
        self.low_res_sweep_button.setToolTip('Perform a quick, low-resolution sweep of the full spectrum')
        self.low_res_sweep_button.move(850, 935)
        self.low_res_sweep_button.resize(180, 30)
        self.low_res_sweep_button.clicked.connect(self.start_low_res_sweep)

    def generate_range_scan_section(self):
        self.start_freq_label = QtWidgets.QLabel('Start Freq (Hz):', self)
        self.start_freq_label.resize(120, 30)
        self.start_freq_label.move(10, 970)
        self.start_freq_input = QtWidgets.QLineEdit(self)
        self.start_freq_input.move(140, 970)
        self.start_freq_input.resize(200, 30)

        self.stop_freq_label = QtWidgets.QLabel('Stop Freq (Hz):', self)
        self.stop_freq_label.resize(120, 30)
        self.stop_freq_label.move(350, 970)
        self.stop_freq_input = QtWidgets.QLineEdit(self)
        self.stop_freq_input.move(450, 970)
        self.stop_freq_input.resize(200, 30)

        self.range_scan_button = QtWidgets.QPushButton('Set Range & Scan', self)
        self.range_scan_button.setToolTip('Set start and stop frequency and acquire data')
        self.range_scan_button.move(660, 970)
        self.range_scan_button.resize(180, 30)
        self.range_scan_button.clicked.connect(self.start_range_scan)

    def generate_command_box(self):
        self.command_box = QtWidgets.QLineEdit(self)
        self.command_box.move(140, 1005)
        self.command_box.resize(1570,30)
        self.command_box.textChanged.connect(self.toggle_connect_button)
        self.command_box_label = QtWidgets.QLabel('GPIB Command:', self)
        self.command_box_label.resize(120,30)
        self.command_box_label.move(10,1005)

    def generate_command_button(self):
        self.command_button = QtWidgets.QPushButton('Send Command', self)
        self.command_button.move(1720,1005)
        self.command_button.resize(180,30)
        self.command_button.setToolTip('Send the GPIB command')
        self.command_button.clicked.connect(self.send_command)

    def generate_response_box(self):
        self.response_box = QtWidgets.QLineEdit(self)
        self.response_box.move(140, 1040)
        self.response_box.resize(1760,30)
        self.response_box_label = QtWidgets.QLabel('Response:', self)
        self.response_box_label.resize(120,30)
        self.response_box_label.move(10,1040)