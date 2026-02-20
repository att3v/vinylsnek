import argparse

from .database import VinylSnekDatabase


def main():
    parser = argparse.ArgumentParser(
        description="VinylSnek - A tool for managing your vinyl collection."
    )
    parser.add_argument(
        "--db-path", default="catalog.db", help="Path to the SQLite database file."
    )
    parser.add_argument(
        "--add", help="Add a new vinyl record to the collection by barcode."
    )
    parser.add_argument(
        "--list", action="store_true", help="List all vinyl records in the collection."
    )
    parser.add_argument(
        "--remove", help="Remove a vinyl record from the collection by name."
    )

    args = parser.parse_args()

    db = VinylSnekDatabase(args.db_path)

    if args.add:
        print(f"Adding vinyl record: {args.add}")
        barcodes = args.add.split(",")
        db.add_vinyl(barcodes)  # For now, we only handle the first barcode in the list.

    elif args.list:
        print("Listing all vinyl records in the collection:")
        db.print_table()

    elif args.remove:
        print(f"Removing vinyl record: {args.remove}")
        # Code to remove the specified vinyl record from the collection would go here.

    else:
        print("No valid arguments provided. Use --help for more information.")
