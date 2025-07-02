import csv
import markdown
import logging
import logging.handlers
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui, QtWebEngineWidgets
from PyQt5.QtGui import QIcon
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import FuncFormatter


class MainWindow(QtWidgets.QMainWindow):
    '''
    This class is for the main GUI window, it creates the graph, textboxes, buttons etc. and their events. It does not directly communicate with the hardware but instead puts messages in a command queue which are handled by another process.
    '''
    def __init__(self, command_queue, message_queue, data_queue, logging_queue):
        super(MainWindow, self).__init__()

        self.window_icon = QIcon('icon.png')

        # create data queues
        self.command_queue = command_queue
        self.message_queue = message_queue
        self.data_queue = data_queue
        self.logging_queue = logging_queue

        # main window settings
        self.title = 'HP4195A'
        self.width = 1920
        self.height = 1080

        # create logging queue and handler
        self.qh = logging.handlers.QueueHandler(self.logging_queue)
        self.root = logging.getLogger()
        self.root.setLevel(logging.DEBUG)
        self.root.addHandler(self.qh)
        self.logger = logging.getLogger(__name__)

        self.connected = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setFixedSize(self.width, self.height)
        self.setWindowIcon(self.window_icon)

        self.graph = PlotCanvas(self,
                                  data_queue=self.data_queue,
                                  width=17,
                                  height=8.5)
        self.graph.move(0,20)

        self.generate_connection_button()
        self.generate_acquire_button()
        self.generate_save_button()
        self.generate_command_box()
        self.generate_command_button()
        self.generate_response_box()
        self.generate_persistance_checkbox()
        self.generate_mag_enable_checkbox()
        self.generate_phase_enable_checkbox()
        self.generate_menu_bar()
        self.generate_autofind_peak_button()
        self.generate_pause_button()

        self.acquire_button.setEnabled(False)
        self.save_button.setEnabled(True)
        self.autofind_peak_button.setEnabled(False)

        self.show()

        self.timer = QtCore.QTimer()
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.start_acquisition)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def generate_menu_bar(self):
        self.main_menu = self.menuBar()
        self.file_menu = self.main_menu.addMenu('File')
        self.about_menu = self.main_menu.addMenu('About')

        self.generate_menu_save_button()
        self.generate_menu_exit_button()
        self.generate_menu_help_button()

    def generate_menu_save_button(self):
        self.save_button = QtWidgets.QAction(QIcon('exit24.png'),
                                             'Save As...',
                                             self)
        self.save_button.setShortcut('Ctrl+S')
        self.save_button.setStatusTip('Save As')
        self.save_button.triggered.connect(self.save_file_dialog)
        self.file_menu.addAction(self.save_button)

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

    def generate_command_box(self):
        self.command_box = QtWidgets.QLineEdit(self)
        self.command_box.move(140, 970)
        self.command_box.resize(1570,30)
        self.command_box.textChanged.connect(self.toggle_connect_button)
        self.command_box_label = QtWidgets.QLabel('GPIB Command:', self)
        self.command_box_label.resize(120,30)
        self.command_box_label.move(10,970)

    def generate_command_button(self):
        self.command_button = QtWidgets.QPushButton('Send Command', self)
        self.command_button.move(1720,970)
        self.command_button.resize(180,30)
        self.command_button.setToolTip('Send the GPIB command')
        self.command_button.clicked.connect(self.send_command)
        self.command_button.setEnabled(False)

    def generate_response_box(self):
        self.response_box = QtWidgets.QLineEdit(self)
        self.response_box.move(140, 1010)
        self.response_box.resize(1760,30)
        self.response_box_label = QtWidgets.QLabel('Response:', self)
        self.response_box_label.resize(120,30)
        self.response_box_label.move(10,1010)

    def generate_persistance_checkbox(self):
        self.p_cb = QtWidgets.QCheckBox('Persist', self)
        self.p_cb.resize(100,30)
        self.p_cb.move(10, 900)
        self.p_cb.setToolTip('Set display to persist')
        self.p_cb.stateChanged.connect(self.change_persist_state)

    def generate_mag_enable_checkbox(self):
        self.mag_cb = QtWidgets.QCheckBox('Magnitude', self)
        self.mag_cb.toggle()
        self.mag_cb.resize(100,30)
        self.mag_cb.move(100, 900)
        self.mag_cb.setToolTip('Display magnitude data')
        self.mag_cb.stateChanged.connect(self.change_mag_state)

    def generate_phase_enable_checkbox(self):
        self.phase_cb = QtWidgets.QCheckBox('Phase', self)
        self.phase_cb.toggle()
        self.phase_cb.resize(100,30)
        self.phase_cb.move(210, 900)
        self.phase_cb.setToolTip('Display phase data')
        self.phase_cb.stateChanged.connect(self.change_phase_state)

    def change_persist_state(self):
        if self.graph.persist:
            self.graph.persist = False
            self.mag_cb.setEnabled(True)
            self.phase_cb.setEnabled(True)
            self.logger.info('Persistence: Disabled')
        else:
            self.graph.persist = True
            self.mag_cb.setEnabled(False)
            self.phase_cb.setEnabled(False)
            self.logger.info('Persistence: Enabled')

    def change_mag_state(self):
        if self.graph.magnitude:
            self.graph.magnitude = False
            self.logger.info('Magnitude: Disabled')
            self.graph.plot()
        else:
            self.graph.magnitude = True
            self.logger.info('Magnitude: Enabled')
            self.graph.plot()

    def change_phase_state(self):
        if self.graph.phase:
            self.graph.phase = False
            self.logger.info('Phase: Disabled')
            self.graph.plot()
        else:
            self.graph.phase = True
            self.logger.info('Phase: Enabled')
            self.graph.plot()

    def toggle_connect_button(self):
        if len(self.command_box.text()) > 0 and self.connected:
            self.command_button.setEnabled(True)
        else:
            self.command_button.setEnabled(False)

    def connect(self):
        if self.connected:
            self.logger.info('Disconnecting from HP4195A')
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            self.command_queue.put('disconnect')
            if self.message_queue.get():
                self.logger.info('Successfully disconnected from HP4195A')
                QtWidgets.QApplication.restoreOverrideCursor()
                self.connect_button.setText("Connect")
                self.acquire_button.setEnabled(False)
                self.connected = False
            else:
                self.logger.info('Disconnection from HP4195 failed')
        else:
            self.logger.info('Attempting to connect to HP4195A')
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            self.command_queue.put('connect')
            if self.message_queue.get():
                self.logger.info('Successfully connected to HP4195A')
                QtWidgets.QApplication.restoreOverrideCursor()
                self.connect_button.setText("Disconnect")
                self.acquire_button.setEnabled(True)
                self.connected = True
            else:
                self.logger.info('Connection to HP4195 failed')

    def start_acquisition(self):
        self.logger.info('Starting data acquisition')
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.acquire_button.setEnabled(False)
        self.command_queue.put('start_acquisition')
        reply = self.message_queue.get()
        if reply:
            self.logger.info('Successfully acquired data')
            QtWidgets.QApplication.restoreOverrideCursor()
            self.save_button.setEnabled(True)
            self.autofind_peak_button.setEnabled(True)
            self.graph.peak_freq = None
            self.graph.peak_mag = None
        else:
            self.logger.info('Data acquisition failed')
            self.acquire_button.setEnabled(True)

    def autofind_peak(self):
        self.logger.info('Finding peak magnitude')
        if not hasattr(self.graph, 'mag_data') or self.graph.mag_data.size == 0:
            self.logger.warning('No magnitude data available to find peak.')
            return
        try:
            # Find the index of the maximum magnitude value
            mag_data_np = np.array(self.graph.mag_data)
            peak_index = np.argmax(mag_data_np)
            peak_mag = mag_data_np[peak_index]
            peak_freq = self.graph.freq_data[peak_index]

            self.logger.info(f'Peak found: {peak_mag:.2f} dBm at {peak_freq/1e6:.2f} MHz')
            # Set the marker on the plot canvas
            self.graph.mark_peak(peak_freq, peak_mag)
            self.graph.plot() # Redraw the plot to show the marker
        except (ValueError, IndexError) as e:
            self.logger.error(f'Could not find peak. Error: {e}')

    def update_plot(self):
        self.logger.info('Updating plot')
        self.graph.plot()

    def send_command(self):
        command = self.command_box.text()
        self.command_queue.put('send_command')
        self.command_queue.put(command)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        response = self.data_queue.get()
        self.logger.info('Data queue size = {}'.format(self.data_queue.qsize()))
        if len(response) > 0:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.response_box.setText('{}: {}'.format(command, response))
            self.command_box.setText('')

    def save_file_dialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self,"Save File","","All Files (*);;Text Files (*.txt);;CSV Files (*.csv)", options=options)
        if file_name:
            self.save_file(file_name)

    def save_file(self, file_name):
        file_name = file_name +'.csv'
        self.logger.info('Saving data to: {}'.format(file_name))
        rows = zip(self.graph.freq_data,
                   self.graph.mag_data,
                   self.graph.phase_data)
        with open(file_name, "w") as output:
            writer = csv.writer(output, lineterminator='\n')
            writer.writerow(['Frequency', 'Magnitude', 'Phase'])
            for row in rows:
                writer.writerow(row)

    def help_dialog(self):
        help_window = Help_Window()
        help_window.exec_()

    def closeEvent(self, event):
        if True:
            if self.connected:
                self.connect()
            self.logging_queue.put(None)
            event.accept()
        else:
            event.ignore()

    def update_span(self, span):
        self.logger.info('Updating span to: {}'.format(span))
        self.command_queue.put('update_span')
        self.command_queue.put(span)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        response = self.data_queue.get()
        if response:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.logger.info('Span updated successfully')
        else:
            self.logger.error('Failed to update span')


    def generate_pause_button(self):
        self.pause_button = QtWidgets.QPushButton('Pause', self)
        self.pause_button.setToolTip('Pause or resume continuous data acquisition')
        self.pause_button.move(1720, 430) # Position it below the other buttons
        self.pause_button.resize(180, 100)
        self.pause_button.setCheckable(True) # Makes the button a toggle
        self.pause_button.clicked.connect(self.toggle_pause)

    def toggle_pause(self, paused):
        if paused:
            self.timer.stop()
            self.pause_button.setText('Resume')
            self.logger.info('Data acquisition paused')
        else:
            self.timer.start()
            self.pause_button.setText('Pause')
            self.logger.info('Data acquisition resumed')
    
    


class PlotCanvas(FigureCanvas):
    '''
    This class is for the figure that displays the data, it reads data off the data queue and updates the graph depending on the settings.
    '''
    def __init__(self,
                 parent=None,
                 data_queue=None,
                 width=5,
                 height=4,
                 dpi=100):
        self.data_queue = data_queue
        self.persist = False
        self.magnitude = True
        self.phase = True

        self.peak_freq = None
        self.peak_mag = None

        self.freq_data = range(1, 100)
        self.mag_data = [0 for i in range(1, 100)]
        self.phase_data = [0 for i in range(1, 100)]

        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='black')
        self.mag_ax = self.fig.add_subplot(111)
        self.mag_ax.set_facecolor('black')
        self.phase_ax = self.mag_ax.twinx()

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                      QtWidgets.QSizePolicy.Expanding,
                                      QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()

    def mark_peak(self, freq, mag):
        '''Saves the coordinates of the peak to be marked on the plot.'''
        self.peak_freq = freq
        self.peak_mag = mag

    def plot(self):
        from queue import Empty
        if self.persist == False:
            self.mag_ax.clear()
            self.phase_ax.clear()

        try:
            # Try to get data without blocking
            self.mag_data = self.data_queue.get_nowait()
            self.phase_data = self.data_queue.get_nowait()
            self.freq_data = self.data_queue.get_nowait()
        except Empty:
            # If the queue is empty, do nothing and just redraw the existing data
            pass

        # --- Style Configuration ---
        self.mag_ax.set_xlabel('Frequency (Hz)', color='white')
        self.mag_ax.set_ylabel('Magnitude (dBm)', color='yellow')
        self.phase_ax.set_ylabel('Phase (deg)', color='cyan')
        self.phase_ax.yaxis.set_label_position('right')

        self.phase_ax.set_xlim(np.min(self.freq_data), np.max(self.freq_data))
        self.phase_ax.set_ylim(np.min(self.phase_data)-20, np.max(self.phase_data)+20)
        self.mag_ax.set_xlim(np.min(self.freq_data), np.max(self.freq_data))
        self.mag_ax.set_ylim(np.min(self.mag_data)-20, np.max(self.mag_data)+20)

        self.mag_ax.tick_params(axis='x', colors='white')
        self.mag_ax.tick_params(axis='y', colors='yellow')
        self.phase_ax.tick_params(axis='y', colors='cyan')


        for spine in self.mag_ax.spines.values():
            spine.set_edgecolor('white')
        self.phase_ax.spines['right'].set_edgecolor('cyan')
        self.mag_ax.spines['left'].set_edgecolor('yellow')

        self.mag_ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x/1e6:.0f} MHz'))
        self.mag_ax.yaxis.set_major_formatter(FuncFormatter(lambda y, pos: f'{y:.0f} dBm'))
        self.phase_ax.yaxis.set_major_formatter(FuncFormatter(lambda y, pos: f'{y:.0f} °'))


        # --- Plotting ---
        # Matplotlib handles empty lists gracefully, so this will not error on startup
        if self.magnitude:
            self.mag_ax.plot(self.freq_data, self.mag_data, color='yellow', linewidth=1.5)

        if self.phase:
            self.phase_ax.plot(self.freq_data, self.phase_data, color='cyan', linewidth=1.5)
        
        # peak marker
        if self.peak_freq is not None and self.peak_mag is not None:
            self.mag_ax.annotate(f'Peak\n{self.peak_mag:.2f} dBm',
                xy=(self.peak_freq, self.peak_mag),
                xytext=(self.peak_freq, self.peak_mag + 15),
                color='red',
                fontsize=10,
                ha='center',
                arrowprops=dict(facecolor='red', shrink=0.05, width=2, headwidth=8)
            )

        self.mag_ax.grid(color='gray', linestyle='-', linewidth=0.5)

        self.fig.tight_layout()
        self.draw()


class Help_Window(QtWidgets.QDialog):
    '''
    This class is for the help window that displays the readme file to the user, it reads the readme file and displays the information as html using the markdown syntax.
    '''
    def __init__(self):
        super(Help_Window, self).__init__()
        self.setWindowTitle("Help")
        self.setWindowIcon(QIcon('hp_icon.png'))
        self.view = QtWebEngineWidgets.QWebEngineView(self)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.view)
        self.file = QtCore.QFile('README.md')
        if not self.file.open(QtCore.QIODevice.ReadOnly):
            QtGui.QMessageBox.information(None, 'info', self.file.errorString())
        self.stream = QtCore.QTextStream(self.file)
        self.html = markdown.markdown(self.stream.readAll())

        self.view.setHtml(self.html)