class AppError(Exception):
    """Base class for application exceptions."""

    error: str
    detail: str | None

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail

    def __str__(self) -> str:
        if self.detail:
            return f"{self.error}: {self.detail}"
        return self.error


class SongNotFoundError(AppError):
    error = "Song not found"


class LyricsFetchError(AppError):
    error = "Lyrics fetch error"


class LyricsServiceError(AppError):
    error = "Lyrics service error"


class InvalidLyricsQueryError(LyricsServiceError):
    error = "Invalid lyrics query"


class InvalidLyricsError(LyricsServiceError):
    error = "Invalid lyrics"


class NoBestMatchLyricsError(LyricsServiceError):
    error = "No best match lyrics found"


class SongRepositoryError(AppError):
    error = "Song repository error"


class CoverDownloadError(SongRepositoryError):
    error = "Cover download error"
