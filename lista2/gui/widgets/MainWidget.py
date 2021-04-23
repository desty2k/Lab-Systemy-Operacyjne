
from qtpy.QtWidgets import QWidget, QVBoxLayout


class MainWidget(QWidget):

    def __init__(self, parent):
        super(MainWidget, self).__init__(parent)
        self.widgets = []

        self.widget_layout = QVBoxLayout(self)
        self.setLayout(self.widget_layout)

    def addWidget(self, widget: QWidget):
        self.widget_layout.addWidget(widget)
        self.widgets.append(widget)
