from PyQt6.QtCore import QAbstractTableModel, Qt


class RecordModel(QAbstractTableModel):
    def __init__(self, records):
        super().__init__()
        self.records_list: list[dict[str, str | int | float]] = records
        self.headers = [
            "Artist",
            "Album",
            "Year",
            "Format",
            "Description",
            "Lowest Price",
        ]

    def rowCount(self, parent=None):
        return len(self.records_list)

    def columnCount(self, parent=None):
        return len(self.headers)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            if 0 <= section < len(self.headers):
                return self.headers[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            record = self.records_list[index.row()]
            col = index.column()

            if col == 0:
                return record["artist"]
            elif col == 1:
                return record["album"]
            elif col == 2:
                return str(record["year"])
            elif col == 3:
                return record["format"] or "N/A"
            elif col == 4:
                return record["description"]
            elif col == 5:
                return (
                    f"{record['lowest_price_discogs']:.2f}€"
                    if record["lowest_price_discogs"]
                    else "N/A"
                )
        return None

    def sort(
        self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder
    ) -> None:
        key_map = {
            0: lambda r: (r.get("artist") or "").lower(),
            1: lambda r: (r.get("album") or "").lower(),
            2: lambda r: (r.get("year") or 0),
            3: lambda r: (r.get("description") or "").lower(),
            4: lambda r: (
                r.get("lowest_price_discogs")
                if r.get("lowest_price_discogs")
                else float("inf")
            ),
        }
        key = key_map.get(column, lambda r: r)
        reverse = order == Qt.SortOrder.DescendingOrder
        self.layoutAboutToBeChanged.emit()
        self.records_list.sort(key=key, reverse=reverse)
        self.layoutChanged.emit()


class ReleaseCandidateModel(QAbstractTableModel):

    def __init__(self, records):
        super().__init__()
        # print(records)
        self.records_list: list[dict[str, str | int | float]] = records
        self.headers = [
            "Title",
            "Country",
            "Year",
            "Discogs Release ID",
        ]

    def as_dict(self):
        return {
            "records_list": self.records_list,
            "headers": self.headers,
        }

    def rowCount(self, parent=None):
        return len(self.records_list)

    def columnCount(self, parent=None):
        return len(self.headers)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            if 0 <= section < len(self.headers):
                return self.headers[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            record = self.records_list[index.row()]
            col = index.column()

            if col == 0:
                return record["title"]
            if col == 1:
                return record["country"]
            elif col == 2:
                return str(record["year"])
            elif col == 3:
                return str(record["discogs_release_id"])
        return None
