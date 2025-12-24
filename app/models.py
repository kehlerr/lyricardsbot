from enum import StrEnum
from io import BufferedReader, BufferedWriter
from typing import Any, Self

import orjson as json
from pydantic import BaseModel, Field


class Song(BaseModel):
    id: int
    title: str
    artist: str
    primary_artists: list[str] = Field(default_factory=list)
    featured_artists: list[str] = Field(default_factory=list)
    song_image_url: str
    artist_image_url: str

    @classmethod
    def from_genius(cls, genius_song_data: dict[str, Any]) -> Self:

        artist_data = genius_song_data["primary_artist"]
        artist_name = artist_data["name"]

        primary_artists = [
            artist["name"] for artist in genius_song_data.get("primary_artists", []) if artist["name"] != artist_name
        ]
        featured_artists = list(
            {
                artist["name"]
                for artist in genius_song_data.get("featured_artists", [])
                if artist["name"] != artist_name
            }.difference(primary_artists)
        )

        return cls(
            id=genius_song_data["id"],
            title=genius_song_data["title"],
            artist=artist_data["name"],
            primary_artists=primary_artists,
            featured_artists=featured_artists,
            song_image_url=genius_song_data["song_art_image_url"],
            artist_image_url=artist_data["image_url"],
        )

    @classmethod
    def load_from_json(cls, fp: BufferedReader) -> Self:
        data = json.loads(fp.read())
        return cls.model_validate(data)

    def dump_as_json(self, fp: BufferedWriter) -> None:
        fp.write(json.dumps(self.model_dump()))


class LyricsQuery(BaseModel):
    lyrics: str = Field(max_length=64)
    lines_before: int | None = Field(default=None, ge=0)
    lines_after: int | None = Field(default=None, ge=0)


class CoverType(StrEnum):
    SONG = "song"
    ARTIST = "artist"
    CUSTOM = "custom"
