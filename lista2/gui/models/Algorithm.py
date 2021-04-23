from qtpy.QtCore import QObject, Signal, Slot


class QAlgorithm(QObject):
    """Runnable algorithm object."""

    def __init__(self):
        super(QAlgorithm, self).__init__(parent=None)
        self.que = []
        self.disk = []
        self.head_pos = 0

    @Slot()
    def run(self):
        pass

    @Slot(int)
    def setDiskSize(self, size):
        self.disk = [0] * size

    @Slot(int)
    def addRequest(self, pos):
        pos = pos - 1
        self.disk[pos] = self.disk[pos] + 1

    @Slot(int)
    def removeRequest(self, pos):
        pos = pos - 1
        self.disk[pos] = self.disk[pos] - 1

    @Slot(int)
    def setHeadPos(self, pos):
        self.head_pos = pos
