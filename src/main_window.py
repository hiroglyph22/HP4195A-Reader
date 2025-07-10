import logging
import logging.handlers
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon

from gui.ui_generator import UIGenerator
from gui.plot_canvas import PlotCanvas
from logic.instrument_controls import InstrumentControls
from logic.plot_controls import PlotControls
from logic.file_handler import FileHandler
from logic.ui_logic import UiLogic

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

        self.title = 'HP4195A'
        self.width = 1920
        self.height = 1120
        
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
        self.setWindowIcon(QIcon('assets/icon.png'))

        self.graph = PlotCanvas(self, data_queue=self.data_queue, width=17, height=8.5)
        self.graph.move(0,20)

        # Call all the UI generation methods from the UIGenerator mixin
        self.generate_UI()
        
        self.show()

        self.timer = QtCore.QTimer()
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.start_acquisition)

    def closeEvent(self, event):
        if self.connected:
            self.connect()
        self.logging_queue.put(None)
        event.accept()