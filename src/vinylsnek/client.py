import json
from pprint import pprint
import requests

from discogs_client import Client as client  # type: ignore
from discogs_client import Release  # type: ignore
from pydantic import BaseModel

USER_TOKEN = "cRTiVuCPHVEytVezUxVuKIVXQCzOePcZlMBgFfLJ"


class ReleaseInfo(BaseModel):
    title: str
    artists: list[str]
    year: int
    styles: list[str]
    description: list[str]
    highest_price_discogs: float | None
    lowest_price_discogs: float | None
    discogs_release_id: int


def from_release(release: Release, highest_price: float | None = None) -> "ReleaseInfo":

    descriptions: list[str] = []
    for format in release.formats:
        text = format.get("text")
        name = format.get("name")
        qty = format.get("qty")
        if all([text, name, qty]):
            descriptions.append(f"{format['text']} {format['name']} x{format['qty']}")

    # content = vars(release)
    # pprint(content)

    return ReleaseInfo(
        title=release.title,
        artists=[artist.name for artist in release.artists],
        year=release.year,
        styles=release.styles,
        description=descriptions,
        highest_price_discogs=highest_price,
        lowest_price_discogs=release.data.get("lowest_price"),
        discogs_release_id=release.id,
    )


class VinylSnekClient(client):
    def __init__(self, user_token):
        client.__init__(self, "VinylSnek/0.1", user_token=user_token)

    def get_id_by_barcodes(self, barcodes: list[str]) -> list[int] | None:
        ids = []
        for code in barcodes:
            results = self.search(code, type="barcode")
            if results:
                ids.append(results[0].id)   # Pick first :D
        return ids

    def get_release_by_id(self, release_id: int) -> dict[str, str]:
        release = self.release(release_id)
        # highest_price = self.get_price_suggestion_by_id(release_id)
        return from_release(release)

    # def get_price_suggestion_by_id(self, release_id: int) -> float | None:
    #     print(release_id)
    #     response = requests.get(
    #         f"https://api.discogs.com/marketplace/price_suggestions/{release_id}",
    #         headers={"Authorization": f"Discogs token={USER_TOKEN}"},
    #     )
    #     print(response.status_code)
    #     if response.status_code == 200:
    #         data = response.json()
    #         pprint(data)
    #         if "listings" in data and len(data["listings"]) > 0:
    #             return max(listing["price"] for listing in data["listings"])


if __name__ == "__main__":
    vinyl_snek_client = VinylSnekClient(USER_TOKEN)
    release_id = vinyl_snek_client.get_id_by_barcode("8024391152973")
    if release_id:
        release_info = vinyl_snek_client.get_release_by_id(release_id)
        print(release_info.model_dump_json(indent=4))
        release_id = vinyl_snek_client.get_id_by_barcode("196588441219")
    if release_id:
        release_info = vinyl_snek_client.get_release_by_id(release_id)
        print(release_info.model_dump_json(indent=4))
        release_id = vinyl_snek_client.get_id_by_barcode("198029239119")
    if release_id:
        release_info = vinyl_snek_client.get_release_by_id(release_id)
        print(release_info.model_dump_json(indent=4))
