from PyQt5.QtWidgets import QComboBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt

class CheckableComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.setEditable(True)             
        self.lineEdit().setReadOnly(True)  
        self.setModel(QStandardItemModel(self))
        self.view().viewport().installEventFilter(self)

    def wheelEvent(self, event):
        event.ignore()

    def eventFilter(self, widget, event):
        if widget == self.view().viewport() and event.type() == event.MouseButtonRelease:
            index = self.view().indexAt(event.pos())
            item = self.model().itemFromIndex(index)
            if item:
                item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)
                self.updateText()
            return True 
        return super().eventFilter(widget, event)

    def hidePopup(self):
        super().hidePopup()
        self.updateText()

    def updateText(self):
        self.lineEdit().setText(", ".join(self.get_checked_items()))

    def addItems(self, texts, checked_texts=None):
        checked_texts = checked_texts or []
        for text in texts:
            item = QStandardItem(text)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setData(Qt.Checked if text in checked_texts else Qt.Unchecked, Qt.CheckStateRole)
            self.model().appendRow(item)
        self.updateText()

    def get_checked_items(self):
        return [self.model().item(i).text() for i in range(self.count()) if self.model().item(i).checkState() == Qt.Checked]