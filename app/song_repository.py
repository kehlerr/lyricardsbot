import hashlib
import logging
import os

from settings import APP_NAME

from .exceptions import CoverDownloadError
from .models import CoverType, Song
from .song_genius_repository import SongGeniusRepository

logger = logging.getLogger(APP_NAME)


class SongRepository:
    COVERS_SONGS_DIR_NAME = "songs"
    COVERS_ARTISTS_DIR_NAME = "artists"

    def __init__(
        self,
        genius_repository: SongGeniusRepository,
        queries_dir_path: str,
        lyrics_dir_path: str,
        covers_dir_path: str,
    ) -> None:
        self._genius_repo = genius_repository
        self._lyrics_dir_path = lyrics_dir_path
        self._covers_dir_path = covers_dir_path
        self._queries_dir_path = queries_dir_path

        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        if not os.path.exists(self._queries_dir_path):
            os.makedirs(self._queries_dir_path)

        if not os.path.exists(self._lyrics_dir_path):
            os.makedirs(self._lyrics_dir_path)

        if not os.path.exists(self._covers_dir_path):
            os.makedirs(self._covers_dir_path)

        self._covers_songs_dir_path = os.path.join(self._covers_dir_path, self.COVERS_SONGS_DIR_NAME)
        if not os.path.exists(self._covers_songs_dir_path):
            os.makedirs(self._covers_songs_dir_path)

        self._covers_artists_dir_path = os.path.join(self._covers_dir_path, self.COVERS_ARTISTS_DIR_NAME)
        if not os.path.exists(self._covers_artists_dir_path):
            os.makedirs(self._covers_artists_dir_path)

    async def get_song_by_query(self, query: str) -> Song | None:
        song = self._load_song_by_query(query)
        if not song:
            song = await self._genius_repo.get_song_by_query(query)

        if song:
            self._store_song_query(song, query)

        return song

    def _load_song_by_query(self, query: str) -> Song | None:
        try:
            query_path = self._song_query_file_path(query)
            if not os.path.isfile(query_path):
                return None

            with open(query_path, "rb") as fp:
                return Song.load_from_json(fp)
        except OSError as exc:
            logger.error("Error occured while reading lyrics file: %s", exc)
        except Exception:
            logger.error("Unable to load query: %s", query)

        return None

    def _store_song_query(self, song: Song, query: str) -> None:
        try:
            with open(self._song_query_file_path(query), "wb") as fp:
                song.dump_as_json(fp)
        except OSError as exc:
            logger.error("Error occured while writing lyrics file: %s", exc)

    def _song_query_file_path(self, query: str) -> str:
        fname = hashlib.sha256(query.encode("utf-8")).hexdigest()
        return os.path.join(self._queries_dir_path, fname)

    async def get_lyrics_by_song_id(self, song_id: int) -> str | None:
        if lyrics := self._load_lyrics(song_id):
            return lyrics

        if not (lyrics := await self._genius_repo.get_lyrics_by_song_id(song_id)):
            return None
        self._store_lyrics(song_id, lyrics)
        return lyrics

    def _load_lyrics(self, song_id: int) -> str | None:
        try:
            lyrics_path = self._song_lyrics_file_path(song_id)
            if not os.path.isfile(lyrics_path):
                return None

            with open(lyrics_path, "r") as fp:
                return fp.read()
        except OSError as exc:
            logger.error("Error occured while reading lyrics file: %s", exc)
            return None

    def _store_lyrics(self, song_id: int, lyrics: str) -> None:
        try:
            with open(self._song_lyrics_file_path(song_id), "w") as fp:
                fp.write(lyrics)
        except OSError as exc:
            logger.error("Error occured while writing lyrics file: %s", exc)

    def _song_lyrics_file_path(self, song_id: int) -> str:
        return os.path.join(self._lyrics_dir_path, str(song_id))

    async def get_cover(self, song: Song, cover_type: CoverType) -> bytes:
        if cover_type == CoverType.ARTIST:
            img_path = self._cover_file_path(song.artist_image_url, self._covers_artists_dir_path)
            fn = self._genius_repo.get_artist_cover_image
        else:
            img_path = self._cover_file_path(song.song_image_url, self._covers_songs_dir_path)
            fn = self._genius_repo.get_song_cover_image

        if img := self._load_cover(img_path):
            return img

        if not (img := await fn(song)):
            raise CoverDownloadError("Song cover download failed")

        self._store_cover(img, img_path)

        return img

    def _store_cover(self, img: bytes, img_path: str) -> None:
        try:
            with open(img_path, "wb") as fp:
                fp.write(img)
        except OSError:
            logger.error("Error occured while writing cover file: %s", img_path)

    def _load_cover(self, img_path: str) -> bytes | None:
        try:
            if not os.path.isfile(img_path):
                return None

            with open(img_path, "rb") as fp:
                return fp.read()
        except OSError:
            logger.error("Error occured while reading cover file: %s", img_path)
            return None

    def _cover_file_path(self, img_url: str, parent_dir: str) -> str:
        filename = hashlib.sha256(img_url.encode("utf-8")).hexdigest()
        return os.path.join(parent_dir, filename)
