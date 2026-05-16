from dataclasses import dataclass

import httpx

from app.config import get_settings

ARTIC_FIELDS = "id,title,artist_display,place_of_origin,date_display"


class ArticAPIError(Exception):
    pass


class ArtworkNotFoundError(ArticAPIError):
    pass


@dataclass(slots=True)
class ArtworkData:
    external_id: int
    title: str
    artist_display: str | None
    place_of_origin: str | None
    date_display: str | None


async def fetch_artwork(external_id: int) -> ArtworkData:
    settings = get_settings()
    url = f"{settings.ARTIC_API_URL}/{external_id}"
    params = {"fields": ARTIC_FIELDS}

    async with httpx.AsyncClient(timeout=settings.ARTIC_TIMEOUT) as client:
        try:
            response = await client.get(url, params=params)
        except httpx.RequestError as exc:
            raise ArticAPIError("Failed to reach Art Institute API.") from exc

    if response.status_code == 404:
        raise ArtworkNotFoundError(f"Artwork with external_id={external_id} was not found.")

    if response.status_code >= 400:
        raise ArticAPIError("Art Institute API returned an unexpected error.")

    payload = response.json()
    data = payload.get("data")
    if not data:
        raise ArtworkNotFoundError(f"Artwork with external_id={external_id} was not found.")

    return ArtworkData(
        external_id=int(data["id"]),
        title=data["title"],
        artist_display=data.get("artist_display"),
        place_of_origin=data.get("place_of_origin"),
        date_display=data.get("date_display"),
    )
