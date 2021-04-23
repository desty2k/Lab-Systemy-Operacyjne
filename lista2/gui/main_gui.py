from qtpy.QtWidgets import QApplication, QPushButton, QWidgetAction, QMenu
from qtpy.QtCore import Qt, qInstallMessageHandler

import sys
import pickle
import random
import logging
import traceback

import qrainbowstyle
from qrainbowstyle.windows import FramelessWindow
from qrainbowstyle.widgets import StylePickerHorizontal

from gui.algorithms import *
from gui.utils import qt_message_handler, Logger
from gui.widgets.MainWidget import MainWidget
from gui.widgets.AlgorithmsTable import AlgorithmsTable
from gui.models.Request import Request
from gui.models.AlgorithmsTableModel import AlgorithmsTableModel

LOGGING_LEVEL = logging.INFO
PICKLED_FILENAME = "requests.pick"

START_POS = 0
DISK_SIZE = 200
REQUESTS_COUNT = 10000

MIN_ARRIVE_TIME = 0
MAX_ARRIVE_TIME = 50000

REAL_TIME_COUNT = 200
MIN_DEADLINE = 0
MAX_DEADLINE = 30


class MainWindow(FramelessWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.que = []
        self.algorithms = [FCFS, SSTF, SCAN, C_SCAN, C_LOOK, SSTF_EDF, SSTF_FDF_SCAN]

        self.menu = QMenu(self)
        self.style_picker_action = QWidgetAction(self.menu)
        self.style_picker = StylePickerHorizontal(self)
        self.style_picker_action.setDefaultWidget(self.style_picker)
        self.menu.addAction(self.style_picker_action)
        self.menu.setTitle("Simulation")
        self.addMenu(self.menu)

        self.main_widget = MainWidget(self)
        self.addContentWidget(self.main_widget)

    def createRequests(self) -> None:
        """Fills queue with disk access requests."""
        for x in range(REQUESTS_COUNT - REAL_TIME_COUNT):
            self.que.append(Request(random.randint(MIN_ARRIVE_TIME, MAX_ARRIVE_TIME),
                                    random.randint(0, DISK_SIZE)))

        for x in range(REAL_TIME_COUNT):
            self.que.append(Request(random.randint(MIN_ARRIVE_TIME, MAX_ARRIVE_TIME),
                                    random.randint(0, DISK_SIZE),
                                    real_time=True, deadline=random.randint(MIN_DEADLINE, MAX_DEADLINE)))

        self.que.sort(key=lambda req: req.arrive_time)
        for index, request in enumerate(self.que):
            request.set_id(index + 1)

    def saveProcessesToFile(self) -> None:
        """Saves requests to file using pickle."""
        with open(PICKLED_FILENAME, "wb") as file:
            pickle.dump(self.que, file)

    def loadProcessesFromFile(self) -> None:
        """Load requests from files using pickle."""
        with open(PICKLED_FILENAME, "rb") as file:
            self.que = pickle.load(file)

    def setupAlgorithms(self):
        self.table = AlgorithmsTable(self.main_widget)
        self.tableModel = AlgorithmsTableModel(self.table)
        self.tableModel.setDiskSize(DISK_SIZE)
        self.table.setModel(self.tableModel)
        self.main_widget.addWidget(self.table)

        for algorithm in self.algorithms:
            algorithm_instance = algorithm(self.que, START_POS, DISK_SIZE)
            self.tableModel.addAlgorithm(algorithm_instance)

        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.tableModel.start)
        self.main_widget.addWidget(self.start_button)


if __name__ == '__main__':
    log = Logger()
    qInstallMessageHandler(qt_message_handler)

    def exception_hook(exctype, value, tb):
        logging.critical(''.join(traceback.format_exception(exctype, value, tb)))
        sys.exit(1)
    sys.excepthook = exception_hook

    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setQuitOnLastWindowClosed(True)

    app = QApplication(sys.argv)
    app.setStyleSheet(qrainbowstyle.load_stylesheet(style="oceanic"))

    win = MainWindow()
    win.createRequests()
    win.show()
    win.setupAlgorithms()

    sys.exit(app.exec())
