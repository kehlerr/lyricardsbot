from settings import QUERY_LENGTH_LIMIT

from .exceptions import LyricsFetchError, SongNotFoundError, InvalidLyricsQueryError, TooLongQueryError
from .image_builder import ImageBuilder
from .lyrics_service import LyricsService
from .models import CoverType, LyricsQuery
from .song_repository import SongRepository


class Handlers:

    def __init__(
        self,
        song_repo: SongRepository,
        lyrics_service: LyricsService,
        image_builder: ImageBuilder,
    ) -> None:
        self._song_repo = song_repo
        self._lyrics_service = lyrics_service
        self._image_builder = image_builder

    def parse_as_lyrics_query(self, query: str, append_query: str | None) -> LyricsQuery:
        lyrics_query = self._lyrics_service.parse_lyrics_query(query)

        if append_query:
            lyrics_query.merge(self._lyrics_service.parse_lyrics_query(append_query))

        query_text  = lyrics_query.lyrics
        if not query_text:
            raise InvalidLyricsQueryError

        if len(query_text) > QUERY_LENGTH_LIMIT:
            raise TooLongQueryError

        return lyrics_query

    async def get_lyrics_on_song_cover(
        self,
        lyrics_query: LyricsQuery,
        cover_type: CoverType,
        cover_bytes: bytes | None = None,
    ) -> bytes:

        song = await self._song_repo.get_song_by_query(lyrics_query.lyrics)
        if not song:
            raise SongNotFoundError(f"by query: {lyrics_query.lyrics}")

        lyrics = await self._song_repo.get_lyrics_by_song_id(song.id)
        if not lyrics:
            raise LyricsFetchError(f"by song id: {song.id}")

        if not cover_bytes:
            cover_bytes = await self._song_repo.get_cover(song, cover_type)

        img = self._image_builder.create(
            lines=self._lyrics_service.get_best_lines(
                lyrics_query.lyrics,
                lyrics,
                lyrics_query.lines_before,
                lyrics_query.lines_after,
            ),
            song_artist=self._lyrics_service.make_artists_line(song.artist, song.primary_artists),
            song_title=self._lyrics_service.make_song_title(song.title),
            cover_bytes=cover_bytes,
        )

        img_bytes = img.read()

        if not img_bytes:
            raise  # TODO

        return img_bytes
