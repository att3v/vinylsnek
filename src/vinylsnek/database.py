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
    highest_price_discogs = Column(Float)
    lowest_price_discogs = Column(Float)
    discogs_release_id = Column(Integer)
    date_purchased = Column(Date)


class VinylSnekDatabase:
    def __init__(self, db_path: str = "catalog.db") -> None:
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        self.engine = engine
        self.snek = VinylSnekClient(USER_TOKEN)

    def add_vinyl(self, barcodes: list[str]) -> None:
        release_ids = self.snek.get_id_by_barcodes(barcodes)
        records = []

        if release_ids:
            for release_id in release_ids:
                release_info = self.snek.get_release_by_id(release_id)
                record = Record(
                    artist=", ".join(release_info.artists),
                    album=release_info.title,
                    year=release_info.year,
                    description=", ".join(release_info.description),
                    highest_price_discogs=release_info.highest_price_discogs,
                    lowest_price_discogs=release_info.lowest_price_discogs,
                    discogs_release_id=release_info.discogs_release_id,
                    date_purchased=date.today(),
                )
                records.append(record)

        with Session(self.engine) as session:
            for record in records:
                session.add(record)
            session.commit()
    
    def delete_vinyl(self, discogs_release_id: int) -> None:
        with Session(self.engine) as session:
            record = session.query(Record).filter_by(discogs_release_id=discogs_release_id).first()
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
                    }
                    for record in records
                ]
            )
