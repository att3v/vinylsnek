import webbrowser

import qdarktheme
import requests
from pydantic_core import ValidationError
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
                             QLineEdit, QMainWindow, QPushButton, QTableView,
                             QVBoxLayout, QWidget)

from .client import ReleaseInfo
from .database import VinylSnekDatabase
from .table_model import ReleaseCandidateModel

INFO_FIELD_TRANSLATIONS = {
    "album": "Album",
    "artist": "Artist",
    "year": "Release Year",
    "lowest_price_discogs": "Lowest Price (Discogs)",
    "description": "Description",
    "discogs_release_id": "Discogs Release ID",
    "discogs_url": "",
}


def list_as_table_model(releases: list[ReleaseInfo]):
    return ReleaseCandidateModel(
        [
            {
                "title": record["title"],
                "country": record["country"],
                "year": record["year"],
                "discogs_release_id": record["discogs_release_id"],
                "discogs_url": record["discogs_url"],
            }
            for record in releases
        ]
    )


class AddRecordDialog(QDialog):
    def __init__(self, db: VinylSnekDatabase, parent=None):
        super().__init__(parent)
        self.db = db
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

    def get_matching_releases(self):
        barcode = self.get_barcode()
        return self.db.query_for_barcode(barcode)


class ChooseRecordDialog(QDialog):
    def __init__(self, records, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Record")
        self.setGeometry(200, 200, 700, 500)
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout()

        label = QLabel("Multiple records found. Please choose one:")
        layout.addWidget(label)

        self.table_view = QTableView()
        self.table_view.setWordWrap(True)
        self.table_view.setModel(records)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setStyleSheet("QTableView::item { padding: 6px 10px; }")
        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()
        layout.addWidget(self.table_view)

        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.accept)
        layout.addWidget(submit_button)

        self.setLayout(layout)


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
            label = QLabel(f"{INFO_FIELD_TRANSLATIONS.get(key, key.capitalize())}")
            label_font = label.font()
            label_font.setBold(True)
            label.setFont(label_font)
            label.setMinimumWidth(150)

            if key == "discogs_url" and value:
                link_button = QPushButton("Open on Discogs")
                link_button.clicked.connect(
                    lambda checked, url=value: webbrowser.open(url)
                )
                value_label = link_button
            elif key == "discogs_release_id":
                value_layout = QHBoxLayout()
                value_label = QLabel(str(value))
                value_label.setWordWrap(True)
                copy_button = QPushButton("📋")
                copy_button.setMaximumWidth(40)
                copy_button.clicked.connect(
                    lambda checked, text=str(value): self.copy_to_clipboard(text)
                )
                value_layout.addWidget(value_label)
                value_layout.addWidget(copy_button)
                detail_layout.addWidget(label)
                detail_layout.addLayout(value_layout)
                right_layout.addLayout(detail_layout)
                continue
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

    def copy_to_clipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)


class MainWindow(QMainWindow):
    def __init__(self, records, db: VinylSnekDatabase):
        super().__init__()
        self.records_model = records
        self.db = db
        self.detail_windows = []
        self.setWindowTitle("VinylSnek")
        self.setGeometry(100, 100, 1000, 600)
        self.setMinimumSize(600, 200)

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
        dialog = AddRecordDialog(self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_matching_releases()
            pagination = results.get("pagination", {})
            results = results.get("results", [])
            if not pagination or pagination.get("items", 0) == 0:
                error_dialog = QDialog(self)
                error_dialog.setWindowTitle("Error")
                error_layout = QVBoxLayout()
                error_label = QLabel("No records found for the given barcode.")
                error_layout.addWidget(error_label)
                close_button = QPushButton("Close")
                close_button.clicked.connect(error_dialog.close)
                error_layout.addWidget(close_button)
                error_dialog.setLayout(error_layout)
                error_dialog.exec()
                return
            elif pagination.get("items", 0) > 1 and results:
                records = []
                for release in results:
                    record_info = {
                        "title": release.get("title"),
                        "country": release.get("country"),
                        "year": release.get("year"),
                        "discogs_release_id": release.get("id"),
                        "discogs_url": release.get("resource_url"),
                    }
                    records.append(record_info)

                records_model = list_as_table_model(records)
                choose_dialog = ChooseRecordDialog(records_model, self)
                if choose_dialog.exec() == QDialog.DialogCode.Accepted:
                    selected_index = choose_dialog.table_view.currentIndex()
                    selected_row = selected_index.row()
                    selected_release_id = records_model.records_list[selected_row][
                        "discogs_release_id"
                    ]
                    try:
                        self.db.add_vinyl(selected_release_id)
                    except ValidationError:
                        error_dialog = QDialog(self)
                        error_dialog.setWindowTitle("Error")
                        error_layout = QVBoxLayout()
                        error_label = QLabel(
                            "Discogs data is bad. This record does not seem to have a valid release ID."
                        )
                        error_layout.addWidget(error_label)
                        close_button = QPushButton("Close")
                        close_button.clicked.connect(error_dialog.close)
                        error_layout.addWidget(close_button)
                        error_dialog.setLayout(error_layout)
                        error_dialog.exec()
            else:
                self.db.add_vinyl(results[0]["id"])

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
