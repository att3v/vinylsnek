import qdarktheme
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from .database import VinylSnekDatabase


class MainWindow(QMainWindow):
    def __init__(self, records):
        super().__init__()
        self.setWindowTitle("VinylSnek")
        self.setGeometry(100, 100, 1200, 600)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        table = records
        table_view = QTableView()
        table_view.setWordWrap(True)
        table_view.setModel(table)
        table_view.setSortingEnabled(True)
        table_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        table_view.horizontalHeader().setStretchLastSection(True)
        table_view.setStyleSheet("QTableView::item { padding: 6px 10px; }")
        table_view.resizeColumnsToContents()
        table_view.resizeRowsToContents()
        table.layoutChanged.connect(table_view.resizeRowsToContents)
        layout.addWidget(table_view)


def main():
    db = VinylSnekDatabase()
    records = db.as_table_model()
    app = QApplication([])
    qdarktheme.setup_theme("dark")
    window = MainWindow(records)
    window.show()
    app.exec()
