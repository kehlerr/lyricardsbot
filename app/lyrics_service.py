import logging
import re

from fuzzywuzzy import fuzz

from settings import APP_NAME, TELEGRAM_BOT_USERNAME

from .exceptions import InvalidLyricsError, NoBestMatchLyricsError
from .models import LyricsQuery

logger = logging.getLogger(APP_NAME)


class LyricsService:

    BEST_SCORE_THRESHOLD = 20
    LINE_SKIP_PATTERNS = [
        "verse",
        "chorus",
        "bridge",
        "outro",
        "intro",
        "[",
        "]",
        "embed",
        "lyrics",
    ]

    def parse_lyrics_query(self, query: str) -> LyricsQuery:
        query = query.replace(TELEGRAM_BOT_USERNAME, "")
        query = " ".join(query.split())

        lines_after: int | None = None
        lines_before: int | None = None

        # Паттерн для поиска индикатора в начале строки: +N или -M (N,M = 1-9)
        start_pattern = r"^([+-])(\d)\s*"
        while query:
            start_match = re.match(start_pattern, query)
            if not start_match:
                break

            sign, digit = start_match.groups()
            digit_int = int(digit)

            if sign == "+":
                lines_after = digit_int
            else:  # sign == '-'
                lines_before = digit_int

            # Удаляем индикатор из начала строки
            query = query[start_match.end() :]

        # Паттерн для поиска индикатора в конце строки: +N или -M (N,M = 1-9)
        end_pattern = r"\s*([+-])(\d)\s*$"
        while query:
            end_match = re.search(end_pattern, query)
            if not end_match:
                break

            sign, digit = end_match.groups()
            digit_int = int(digit)

            # Извлекаем число в зависимости от знака
            if sign == "+":
                lines_after = digit_int
            else:  # sign == '-'
                lines_before = digit_int

            # Удаляем индикатор из конца строки
            query = query[: end_match.start()]

        return LyricsQuery(lyrics=query.strip(), lines_before=lines_before, lines_after=lines_after)

    def get_best_lines(
        self,
        query: str,
        lyrics: str,
        lines_before: int | None = None,
        lines_after: int | None = None,
    ) -> list[str]:
        lines = tuple(line.strip() for line in lyrics.split("\n") if line.strip())

        # Filtering empty, too short and service lines like [Verse 1], [Chorus], etc.
        filtered_lines = []

        for line in lines:
            if not line:
                continue
            line_lower = line.lower()
            if not any(pattern in line_lower for pattern in self.LINE_SKIP_PATTERNS):
                if len(line) >= 3:
                    filtered_lines.append(line)

        if not filtered_lines:
            raise InvalidLyricsError("Empty lyrics list after filtering")

        # Finding best matching lines
        best_match_line = None
        best_match_lines_idx: list[int] = []
        best_score = None

        query_normalized = query.strip().lower()

        for idx, line in enumerate(filtered_lines):
            line_normalized = line.lower()
            ratio_score = fuzz.ratio(query_normalized, line_normalized)
            partial_score = fuzz.partial_ratio(query_normalized, line_normalized)
            token_sort_score = fuzz.token_sort_ratio(query_normalized, line_normalized)

            max_score = max(ratio_score, partial_score, token_sort_score)
            if best_score is not None and max_score < best_score:
                continue

            if best_score is None or max_score > best_score:
                best_match_line = line
                best_match_lines_idx = [idx]
                best_score = max_score
                continue

            if best_match_line == line:
                best_match_lines_idx.append(idx)

        # If no best match within threshold, raise exception
        if best_score and best_score < self.BEST_SCORE_THRESHOLD:
            raise NoBestMatchLyricsError(f"No best match lyrics found, best score is: {best_score}")

        matched_lines = self._collect_matched_lines(filtered_lines, best_match_lines_idx, lines_before, lines_after)
        cleaned_lines = self._get_cleaned_lines(matched_lines)
        if not cleaned_lines:
            raise InvalidLyricsError("Empty lines list after collecting matched lines and cleaning")

        return cleaned_lines

    def _collect_matched_lines(
        self,
        lines: list[str],
        matched_indices: list[int],
        lines_before: int | None,
        lines_after: int | None,
    ) -> list[str]:
        if not matched_indices:
            return []

        if not lines_before and not lines_after:
            idx = matched_indices[0]
            return [lines[idx]]

        total_collected: list[list[str]] = []

        for idx in matched_indices:
            start_idx = max(0, idx - (lines_before or 0))
            end_idx = min(len(lines), idx + (lines_after or 0) + 1)

            total_collected.append(lines[start_idx:end_idx])

        return max(total_collected, key=len)

    def _get_cleaned_lines(self, lines: list[str], full: bool = True) -> list[str]:
        cleaned_lines = []

        for i, line in enumerate(lines):
            if not line:
                continue

            cleaned_line = line

            # Cleaning parentheses at the end of the line
            cleaned_line = re.sub(r"\([^)]*\)\s*$", "", cleaned_line)

            # Cleaning parentheses with 1-6 characters inside, not at the end of the line
            cleaned_line = re.sub(r"\([^)]{1,6}\)(?!\s*$)", "", cleaned_line)

            # Cleaning dashes and commas at the end of the line
            if full and i == len(lines) - 1:
                # Cleaning dashes at the end of the last line
                cleaned_line = re.sub(r"-\s*$", "", cleaned_line)
                cleaned_line = re.sub(r"—\s*$", "", cleaned_line)
                # Cleaning commas at the end of the last line
                cleaned_line = re.sub(r",\s*$", "", cleaned_line)

            # Cleaning multiple spaces
            cleaned_line = re.sub(r"\s+", " ", cleaned_line).strip()

            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        return cleaned_lines

    def make_artists_line(
        self,
        primary_artist: str,
        primary_artists: list[str] | None = None,
        featured_artists: list[str] | None = None,
    ) -> str:

        try:
            primary_artist = self._get_cleaned_lines([primary_artist], full=False)[0]
        except IndexError:
            primary_artist = ""

        if primary_artists:
            primary_artists = [
                artist for artist in self._get_cleaned_lines(primary_artists, full=False) if artist != primary_artist
            ]

        if featured_artists:
            featured_artists = [
                artist
                for artist in self._get_cleaned_lines(featured_artists, full=False)
                if artist not in (primary_artist, *(primary_artists or []))
            ]

        result = primary_artist

        if primary_artists:
            result = f"{result} & {', '.join(primary_artists)}"

        if featured_artists:
            result = f"{result} feat. {', '.join(featured_artists)}"

        return result

    def make_song_title(self, title: str) -> str:
        cleaned_title = self._get_cleaned_lines([title], full=False)
        try:
            return cleaned_title[0]
        except IndexError:
            return ""
