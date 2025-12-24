import logging
from json import JSONDecodeError
from typing import Any

import httpx
import lyricsgenius  # type: ignore
from asyncer import asyncify

from settings import APP_NAME, GENIUS_HEADERS

from .models import Song

logger = logging.getLogger(APP_NAME)


class SongGeniusRepository:

    SEARCH_PATH = "https://genius.com/api/search/multi/"
    ALLOWED_HIT_TYPES = ("song", "lyric")

    def __init__(self, genius_token: str | None = None) -> None:
        self.genius_client = lyricsgenius.Genius(genius_token)
        self.client_raw = httpx.AsyncClient(headers=GENIUS_HEADERS)

    async def get_song_by_query(self, query: str) -> Song | None:
        search_data = await self._search_by_lyrics_query(query)
        if not search_data:
            logger.warning(f"No search data found for query: {query}")
            return None

        song_data = {}
        for section in search_data.get("sections", []):
            for hit in section.get("hits", []):
                if hit.get("type") not in self.ALLOWED_HIT_TYPES:
                    continue

                song_data = hit.get("result", {})
                break

        if not song_data or "id" not in song_data:
            logger.warning("Not found song in sections")
            return None

        song = Song.from_genius(song_data)
        logger.info(f"Found song: {song.artist} - {song.title}; query: {query}")
        return song

    async def _search_by_lyrics_query(self, query: str) -> dict[str, Any] | None:
        clean_query = query.replace("[", "").replace("]", "").replace("(", "").replace(")", "")

        song_data_response = await self.client_raw.get(self.SEARCH_PATH, params={"q": clean_query})
        if song_data_response.status_code != 200:
            logger.error(f"API Genius error: {song_data_response.status_code}")
            return None

        try:
            search_response = song_data_response.json()["response"]
        except JSONDecodeError as exc:
            logger.error(f"Error occured on parsing JSON: {exc}")
            return None
        except KeyError:
            logger.error("Invalid data, no 'response' key")
            return None

        if not search_response:
            logger.warning(f"Empty response for query: {query}")
            return None

        return search_response

    async def get_lyrics_by_song_id(self, song_id: int) -> str | None:
        lyrics = await asyncify(self.genius_client.lyrics)(song_id=song_id)
        if not lyrics:
            logger.warning(f"Song lyrics not found for song ID: {song_id}")
            return None
        return lyrics

    async def get_song_cover_image(self, song: Song) -> bytes | None:
        cover_url = song.song_image_url
        if not cover_url:
            logger.warning(f"Cover not found for {song.artist} - {song.title}")
            return None

        return await self._fetch_image(cover_url)

    async def get_artist_cover_image(self, song: Song) -> bytes | None:
        cover_url = song.artist_image_url
        if not cover_url:
            logger.warning(f"Cover not found for artist {song.artist}")
            return None

        return await self._fetch_image(cover_url)

    async def _fetch_image(self, image_url: str) -> bytes | None:
        response = await self.client_raw.get(image_url)
        if response.status_code != 200:
            logger.error(f"Error occured on downlading image: {response.status_code}")
            return None

        return response.content
