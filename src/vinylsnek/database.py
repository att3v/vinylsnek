from datetime import date

from sqlalchemy import Column, Date, Float, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base
from tabulate import tabulate

from .client import USER_TOKEN, VinylSnekClient
from .table_model import RecordModel

Base = declarative_base()


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True)
    artist = Column(String, nullable=False)
    album = Column(String, nullable=False)
    year = Column(Integer)
    description = Column(String)
    lowest_price_discogs = Column(Float)
    discogs_release_id = Column(Integer)
    date_purchased = Column(Date)
    release_cover_url = Column(String)
    discogs_url = Column(String)


class VinylSnekDatabase:
    def __init__(self, db_path: str = "catalog.db") -> None:
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        self.engine = engine
        self.snek = VinylSnekClient(USER_TOKEN)

    def query_for_barcode(self, barcode: str) -> list[int]:
        return self.snek.search_by_barcode(barcode)

    def add_vinyl(self, release_id: int) -> None:
        release_info = self.snek.get_release_by_id(release_id)
        if release_info:
            record = Record(
                artist=", ".join(release_info.artists),
                album=release_info.title,
                year=release_info.year,
                description=", ".join(release_info.description),
                lowest_price_discogs=release_info.lowest_price_discogs,
                discogs_release_id=release_info.discogs_release_id,
                date_purchased=date.today(),
                release_cover_url=release_info.record_cover_url,
                discogs_url=release_info.discogs_url,
            )

            with Session(self.engine) as session:
                session.add(record)
                session.commit()

        else:
            print(f"Release with ID {release_id} not found in Discogs.")

    def delete_vinyl(self, discogs_release_id: int) -> None:
        with Session(self.engine) as session:
            record = (
                session.query(Record)
                .filter_by(discogs_release_id=discogs_release_id)
                .first()
            )
            if record:
                session.delete(record)
                session.commit()

    def print_table(self) -> None:
        headers = [
            "Artist",
            "Album",
            "Year",
            "Description",
            "Lowest Price (Discogs)",
            "Discogs Release ID",
        ]
        content = []
        with Session(self.engine) as session:
            records = session.query(Record).all()
            for record in records:
                content.append(
                    [
                        record.artist,
                        record.album,
                        record.year,
                        record.description,
                        record.lowest_price_discogs,
                        record.discogs_release_id,
                    ]
                )
        print(tabulate(content, headers=headers, tablefmt="fancy_grid"))

    def as_table_model(self):
        with Session(self.engine) as session:
            records = session.query(Record).all()
            return RecordModel(
                [
                    {
                        "artist": record.artist,
                        "album": record.album,
                        "year": record.year,
                        "description": record.description.replace(", ", "\n"),
                        "lowest_price_discogs": record.lowest_price_discogs,
                        "discogs_release_id": record.discogs_release_id,
                        "record_cover_url": record.release_cover_url,
                        "discogs_url": record.discogs_url,
                    }
                    for record in records
                ]
            )
