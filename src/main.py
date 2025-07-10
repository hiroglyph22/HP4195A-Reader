import sys
import os
import threading
import logging.config
from PyQt5 import QtWidgets
from multiprocessing import Queue, freeze_support

import hp4195a_interface as hp
import multi_logging as ml

from main_window import MainWindow

if __name__ == '__main__':
    freeze_support()

    command_queue = Queue()
    message_queue = Queue()
    data_queue = Queue()
    logging_queue = Queue()

    dp = hp.hp4195a_interface(command_queue, message_queue, data_queue, logging_queue)
    dp.daemon = True
    dp.start()

    app = QtWidgets.QApplication(sys.argv)
    gp = MainWindow(command_queue, message_queue, data_queue, logging_queue)

    if getattr(sys, 'frozen', False):
        dir_name = os.path.dirname(sys.executable)
    else:
        dir_name = os.path.dirname(__file__)

    log_config_file_path = os.path.join(dir_name, 'logging.conf')

    logging.config.fileConfig(log_config_file_path, disable_existing_loggers=False)
    lp = threading.Thread(target=ml.logger_thread, args=(logging_queue,))
    lp.daemon = True
    lp.start()

    sys.exit(app.exec_())
    dp.join()
    logging_queue.put(None)
    lp.join()
