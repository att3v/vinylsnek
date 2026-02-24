import webbrowser

import qdarktheme
import requests
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .database import VinylSnekDatabase


class AddRecordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Record")
        self.setGeometry(200, 200, 400, 150)

        layout = QVBoxLayout()

        label = QLabel("Record Barcode:")
        self.barcode_input = QLineEdit()
        layout.addWidget(label)
        layout.addWidget(self.barcode_input)

        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.accept)
        layout.addWidget(submit_button)

        self.setLayout(layout)

    def get_barcode(self):
        return self.barcode_input.text()


class RecordDetailsDialog(QDialog):
    def __init__(self, record, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Details")
        self.setGeometry(200, 200, 700, 300)
        self.setWindowModality(Qt.WindowModality.NonModal)

        master_layout = QVBoxLayout()

        layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        if cover_url := record.get("record_cover_url"):
            try:
                headers = {
                    "User-Agent": "VinylSnek/0.1 +https://github.com/att3v/vinylsnek"
                }
                response = requests.get(cover_url, timeout=5, headers=headers)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    if not pixmap.isNull():
                        cover_label = QLabel()
                        cover_label.setPixmap(
                            pixmap.scaledToWidth(
                                250, Qt.TransformationMode.SmoothTransformation
                            )
                        )
                        left_layout.addWidget(cover_label)
                    else:
                        error_label = QLabel("Could not load cover art (invalid image)")
                        left_layout.addWidget(error_label)
                else:
                    error_label = QLabel(
                        f"Failed to load image (HTTP {response.status_code})"
                    )
                    left_layout.addWidget(error_label)
            except Exception as e:
                error_label = QLabel(f"Could not load cover art: {str(e)}")
                left_layout.addWidget(error_label)
        else:
            error_label = QLabel("No cover art available")
            left_layout.addWidget(error_label)

        left_layout.addStretch()
        layout.addLayout(left_layout)

        right_layout = QVBoxLayout()
        for key, value in record.items():
            if key in ["record_cover_url"]:
                continue
            detail_layout = QHBoxLayout()
            label = QLabel(f"{key.capitalize()}:")
            label.setMinimumWidth(150)

            if key == "discogs_url" and value:
                link_button = QPushButton("Open on Discogs")
                link_button.clicked.connect(
                    lambda checked, url=value: webbrowser.open(url)
                )
                value_label = link_button
            else:
                value_label = QLabel(str(value))
                value_label.setWordWrap(True)

            detail_layout.addWidget(label)
            detail_layout.addWidget(value_label)
            right_layout.addLayout(detail_layout)

        right_layout.addStretch()
        layout.addLayout(right_layout)

        master_layout.addLayout(layout)

        button_layout = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        master_layout.addLayout(button_layout)

        self.setLayout(master_layout)


class MainWindow(QMainWindow):
    def __init__(self, records, db: VinylSnekDatabase):
        super().__init__()
        self.records_model = records
        self.db = db
        self.detail_windows = []
        self.setWindowTitle("VinylSnek")
        self.setGeometry(100, 100, 1000, 600)

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
        self.table_view.doubleClicked.connect(self.on_row_double_clicked)

        self.records_model = table
        self.records_model.layoutChanged.connect(self.table_view.resizeRowsToContents)
        layout.addWidget(self.table_view)

        button_layout = QHBoxLayout()

        add_button = QPushButton("Add Record")
        add_button.clicked.connect(lambda: self.open_add_record_dialog())

        remove_button = QPushButton("Remove Record")
        remove_button.clicked.connect(self.remove_selected_record)

        edit_button = QPushButton("Edit Record")
        edit_button.clicked.connect(self.edit_selected_record)

        filter_button = QPushButton("Filter Records")
        filter_button.clicked.connect(self.filter_records)

        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(filter_button)
        layout.addLayout(button_layout)

    def on_row_double_clicked(self, index):
        row_index = index.row()
        record = self.records_model.records_list[row_index]
        dialog = RecordDetailsDialog(record, self)
        dialog.show()
        self.detail_windows.append(dialog)

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

    def edit_selected_record(self):
        # TODO: Implement edit functionality
        pass

    def filter_records(self):
        # TODO: Implement filter functionality
        pass


def main():
    db = VinylSnekDatabase()
    records = db.as_table_model()
    app = QApplication([])
    qdarktheme.setup_theme("dark")
    window = MainWindow(records, db)
    window.show()
    app.exec()
