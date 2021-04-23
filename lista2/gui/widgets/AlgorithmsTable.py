
from qtpy.QtWidgets import QTableView, QFrame, QAbstractScrollArea, QAbstractItemView, QTableWidget, QHeaderView
from qtpy.QtCore import Qt, Signal, QPoint, Slot, QModelIndex


class AlgorithmsTable(QTableView):

    def __init__(self, *args, **kwargs):
        super(AlgorithmsTable, self).__init__(*args, **kwargs)

        self.setAutoFillBackground(True)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)

        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setWordWrap(True)

        self.setGridStyle(Qt.SolidLine)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        hheader = self.horizontalHeader()
        # hheader.setStretchLastSection(True)
        hheader.setVisible(False)
        hheader.setMinimumSectionSize(0)

        vheader = self.verticalHeader()
        vheader.setSortIndicatorShown(False)
        vheader.setVisible(True)
        vheader.setSectionResizeMode(QHeaderView.Stretch)

        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        # self.setSelectionBehavior(QAbstractItemView.SelectRows)

    def setModel(self, model):
        super().setModel(model)
        for i in range(self.model().columnCount()):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        for i in range(self.model().rowCount()):
            self.verticalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
