import logging
import logging.handlers
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon

from .gui.ui_generator import UIGenerator
from .gui.plot_canvas import PlotCanvas
from .logic.instrument_controls import InstrumentControls
from .logic.plot_controls import PlotControls
from .logic.file_handler import FileHandler
from .logic.ui_logic import UiLogic

class MainWindow(QtWidgets.QMainWindow, 
                 UIGenerator, 
                 InstrumentControls, 
                 PlotControls, 
                 FileHandler, 
                 UiLogic):
    '''
    This class is for the main GUI window. It handles events and
    application logic by inheriting from focused mixin classes.
    '''
    def __init__(self, command_queue, message_queue, data_queue, logging_queue):
        super(MainWindow, self).__init__()

        self.command_queue = command_queue
        self.message_queue = message_queue
        self.data_queue = data_queue
        self.logging_queue = logging_queue

        self.title = 'HP4195A Network Analyser Interface'
        
        self.qh = logging.handlers.QueueHandler(self.logging_queue)
        self.root = logging.getLogger()
        self.root.setLevel(logging.DEBUG)
        self.root.addHandler(self.qh)
        self.logger = logging.getLogger(__name__)

        self.connected = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setMinimumSize(1280, 720) # Set a reasonable minimum size
        self.resize(1920, 1080)
        try:
            # Assuming assets are inside src.
            self.setWindowIcon(QIcon('src/assets/icon.png'))
        except Exception as e:
            self.logger.warning(f"Could not load window icon: {e}")

        # Create a central widget and a main layout
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10) # Add some margins
        main_layout.setSpacing(10) # Add spacing between widgets

        # Create the plot
        self.graph = PlotCanvas(self, data_queue=self.data_queue, width=16, height=9)
        
        # The UI generator returns the main control panel widget
        control_panel_widget = self.generate_UI()

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)  # Important: Allows the inner widget to resize
        scroll_area.setWidget(control_panel_widget) # Place the generated panel inside the scroll area
        
        scroll_area.setMinimumWidth(400)

        main_layout.addWidget(self.graph, 3)    # Give plot a stretch factor of 3
        main_layout.addWidget(scroll_area, 1) # Give panel a stretch factor of 1
        
        self.show()

        self.timer = QtCore.QTimer()
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.start_acquisition)

    def runOnUiThread(self, f):
        QtCore.QMetaObject.invokeMethod(self, 'do_runOnUiThread', QtCore.Qt.QueuedConnection, QtCore.Q_ARG(object, f))

    @QtCore.pyqtSlot(object)
    def do_runOnUiThread(self, f):
        f()

    def closeEvent(self, event):
        if self.connected:
            # Simulate putting a 'True' on the queue for the disconnect to complete
            self.message_queue.put(True)
            self.connect()
        self.logging_queue.put(None)
        event.accept()