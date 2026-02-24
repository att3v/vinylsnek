import requests
from os import getenv
from pydantic import BaseModel

USER_TOKEN = getenv("DISCOGS_USER_TOKEN")


class ReleaseInfo(BaseModel):
    title: str
    artists: list[str]
    year: int
    styles: list[str]
    description: list[str]
    highest_price_discogs: float | None
    lowest_price_discogs: float | None
    discogs_release_id: int
    record_cover_url: str | None
    discogs_url: str | None = None


class VinylSnekClient:
    def __init__(self, user_token: str):
        self.api_base_url = "https://api.discogs.com"
        self.headers = {
            "Authorization": f"Discogs token={user_token}",
            "User-Agent": "VinylSnek/0.1",
        }

    def get_id_by_barcodes(self, barcodes: list[str]) -> list[int] | None:
        ids = []
        for code in barcodes:
            results = (
                requests.get(
                    self.api_base_url + "/database/search",
                    params={"barcode": code},
                    headers=self.headers,
                )
                .json()
                .get("results", [])
            )
            if results:
                ids.append(results[0].get("id"))  # Pick first :D
        return ids

    def get_release_by_id(self, release_id: int) -> dict[str, str]:
        release = requests.get(
            self.api_base_url + f"/releases/{release_id}", headers=self.headers
        ).json()
        return self.from_release(release)

    def get_release_lowest_price(self, release_id: int) -> float | None:
        response = requests.get(
            self.api_base_url + f"/marketplace/stats/{release_id}",
            headers=self.headers,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("lowest_price", {}).get("value")
        else:
            print(response.status_code, response.text)

    def from_release(
        self, release: dict, highest_price: float | None = None
    ) -> "ReleaseInfo":
        descriptions: list[str] = []
        # TODO: Handle also 7" formats, etc. (desciptions should be more detailed)
        for format in release.get("formats", []):
            text = format.get("text")
            name = format.get("name")
            qty = format.get("qty")
            if all([text, name, qty]):
                text = text.replace(",", "")
                name = name.replace(",", "")
                descriptions.append(f"{text} {name} x{format['qty']}")

        images = release.get("data", {}).get("images", [])
        for image in images:
            if image.get("type") == "primary" and image.get("uri"):
                release.get("data", {})["cover_image"] = image["uri"]
                break

        print(f"{release['artists'][0]['name']} - {release['title']}")
        return ReleaseInfo(
            title=release["title"],
            artists=[artist["name"] for artist in release.get("artists", [])],
            year=release.get("year"),
            styles=release.get("styles", []),
            description=descriptions,
            highest_price_discogs=highest_price,
            lowest_price_discogs=self.get_release_lowest_price(release.get("id")),
            discogs_release_id=release.get("id"),
            record_cover_url=release.get("data", {}).get("cover_image"),
            discogs_url="https://www.discogs.com/release/" + str(release.get("id")),
        )


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
