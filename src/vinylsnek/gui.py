import qdarktheme
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
                             QLineEdit, QMainWindow, QPushButton, QTableView,
                             QVBoxLayout, QWidget)

from .database import VinylSnekDatabase


class AddRecordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Record")
        self.setGeometry(200, 200, 400, 150)

        layout = QVBoxLayout()

        # Barcode label and input
        label = QLabel("Record Barcode:")
        self.barcode_input = QLineEdit()
        layout.addWidget(label)
        layout.addWidget(self.barcode_input)

        # Submit button
        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.accept)
        layout.addWidget(submit_button)

        self.setLayout(layout)

    def get_barcode(self):
        return self.barcode_input.text()


class MainWindow(QMainWindow):
    def __init__(self, records, db: VinylSnekDatabase):
        super().__init__()
        self.records_model = records
        self.db = db
        self.setWindowTitle("VinylSnek")
        self.setGeometry(100, 100, 1300, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        table = records
        self.table_view = QTableView()
        self.table_view.setWordWrap(True)
        self.table_view.setModel(table)
        self.table_view.setSortingEnabled(True)
        self.table_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setStyleSheet("QTableView::item { padding: 6px 10px; }")
        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        self.records_model = table
        self.records_model.layoutChanged.connect(self.table_view.resizeRowsToContents)
        layout.addWidget(self.table_view)

        button_layout = QHBoxLayout()

        add_button = QPushButton("Add Record")
        add_button.clicked.connect(lambda: self.open_add_record_dialog())

        remove_button = QPushButton("Remove Record")
        remove_button.clicked.connect(self.remove_selected_record)

        filter_button = QPushButton("Filter Records")
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addWidget(filter_button)
        layout.addLayout(button_layout)

    def open_add_record_dialog(self):
        dialog = AddRecordDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            barcode = dialog.get_barcode()
            self.db.add_vinyl([barcode])

            updated_records = self.db.as_table_model()
            new_records = [
                r
                for r in updated_records.records_list
                if r not in self.records_model.records_list
            ]
            self.records_model.layoutAboutToBeChanged.emit()
            self.records_model.records_list.extend(new_records)
            self.records_model.layoutChanged.emit()

    def remove_selected_record(self):
        selected_indexes = self.table_view.selectedIndexes()
        if not selected_indexes:
            return
        row_index = selected_indexes[0].row()
        record = self.records_model.records_list[row_index]
        self.db.delete_vinyl(record["discogs_release_id"])
        self.records_model.layoutAboutToBeChanged.emit()
        self.records_model.records_list.pop(row_index)
        self.records_model.layoutChanged.emit()


def main():
    db = VinylSnekDatabase()
    records = db.as_table_model()
    app = QApplication([])
    qdarktheme.setup_theme("dark")
    window = MainWindow(records, db)
    window.show()
    app.exec()
