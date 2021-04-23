from qtpy.QtCore import QAbstractTableModel, Qt, Slot, Signal, QThread
from qtpy.QtGui import QBrush

from gui.models.Algorithm import QAlgorithm


class AlgorithmsTableModel(QAbstractTableModel):
    updated = Signal()

    def __init__(self, parent=None):
        super(AlgorithmsTableModel, self).__init__(parent)
        self.algorithms = []
        self.head_pos = 0
        self.disk_size = 0

        self.threads = []

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.algorithms)

    def columnCount(self, parent=None, *args, **kwargs):
        return self.disk_size

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if 0 <= index.row() < self.rowCount() and 0 <= index.column() < self.columnCount():
            alg = self.algorithms[index.row()]
            data = alg.disk[index.column()]
            if role == Qt.DisplayRole:
                return data
            elif role == Qt.TextColorRole:
                if index.column() == alg.head_pos:
                    return QBrush(Qt.black)
                elif data > 0:
                    return QBrush(Qt.black)

            elif role == Qt.BackgroundRole:
                if index.column() == alg.head_pos:
                    return QBrush(Qt.red)
                elif data > 0:
                    return QBrush(Qt.green)
                elif data == 0:
                    return QBrush()
        self.update()

    def setDiskSize(self, size):
        self.disk_size = size

    @Slot(QAlgorithm)
    def addAlgorithm(self, algorithm):
        algorithm_thread = QThread()
        algorithm.setDiskSize(self.disk_size)
        algorithm.moveToThread(algorithm_thread)

        algorithm_thread.started.connect(algorithm.run)
        self.algorithms.append(algorithm)
        self.threads.append(algorithm_thread)
        self.update()

    @Slot()
    def start(self):
        for thread in self.threads:
            thread.start()

    @Slot()
    def clear(self):
        """Clear the table"""
        self.beginResetModel()
        self.algorithms.clear()
        self.endResetModel()

    @Slot()
    def update(self):
        """Update table when data changed"""
        self.beginResetModel()
        self.endResetModel()

    def headerData(self, section, orientation, role=None):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return orientation

            elif orientation == Qt.Vertical:
                return self.algorithms[section].__class__.__name__
