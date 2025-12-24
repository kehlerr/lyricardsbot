import logging
import os
from dataclasses import dataclass
from io import BytesIO
from typing import cast

from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as TImage
from PIL.ImageDraw import ImageDraw as TImageDraw
from PIL.ImageFont import FreeTypeFont
from PIL.ImageFont import ImageFont as TImageFont

from settings import APP_NAME, FONTS_DIR_PATH

from .exceptions import AppError

logger = logging.getLogger(APP_NAME)


@dataclass
class LyricsLineData:
    lyrics_text: list[str]
    line_widths: list[float]
    line_heights: list[float]
    total_line_height: float


class ImageBuilderError(AppError):
    error = "Image creation error"


def get_wrapped_lines(
    text: str,
    font: FreeTypeFont | TImageFont,
    max_width_soft: int,
    max_width_hard: int | None = None,
) -> list[str]:
    lines = []
    current_line: list[str] = []

    words = text.split()
    words_cnt = len(words)

    for idx, word in enumerate(text.split(), start=1):
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)

        if bbox[2] <= max_width_soft:
            current_line.append(word)
        else:
            if current_line:
                if max_width_hard and bbox[2] <= max_width_hard:
                    if idx == words_cnt:
                        current_line.append(word)
                        break
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                # Word itself is longer than max_width, add it as a separate line
                lines.append(word)

    if current_line:
        lines.append(" ".join(current_line))

    return lines


class ImageBuilder:
    IMAGE_WIDTH = 1050
    IMAGE_HEIGHT = 1156
    IMAGE_SIZE = (IMAGE_WIDTH, IMAGE_HEIGHT)

    FOOTER_HEIGHT = 155
    FOOTER_Y = IMAGE_HEIGHT - FOOTER_HEIGHT
    FOOTER_PADDING = 50
    FOOTER_TEXT_X = FOOTER_PADDING
    MAX_FOOTER_WIDTH = IMAGE_WIDTH - (FOOTER_PADDING * 2)

    TITLE_PADDING = 130
    MAX_TITLE_WIDTH = MAX_FOOTER_WIDTH - FOOTER_PADDING * 2 - TITLE_PADDING
    OFFSET_BETWEEN_TITLE_AND_ARTIST_L1 = 32
    OFFSET_BETWEEN_TITLE_AND_ARTIST_L2 = 26
    OFFSET_BETWEEN_TITLE_LINES = 6

    LYRICS_BOTTOM_POSITION_Y = IMAGE_HEIGHT - FOOTER_HEIGHT - 104
    LYRICS_LINE_MAX_WIDTH_SOFT = 640
    LYRICS_LINE_MAX_WIDTH_HARD = 720
    LYRICS_LINE_PADDING = 8
    LYRICS_LINE_OFFSET_X = 45
    LYRICS_LINE_SPACING = 20
    LYRICS_LINE_HEIGHT = 46
    LYRICS_WRAPPED_LINE_SPACING = 8
    LYRICS_WRAPPED_LINE_OFFSET_X = LYRICS_LINE_OFFSET_X + 15

    LYRICS_LINE_BACKGROUND_COLOR = (253, 253, 253, 232)
    LYRICS_LINE_TEXT_COLOR = (0, 0, 0, 255)
    LYRICS_LINE_BORDER_COLOR = (250, 249, 246, 192)

    FOOTER_COLOR = (12, 12, 12)
    TITLE_COLOR = (253, 253, 253)
    TITLE_SHADOW_COLOR = (8, 8, 8, 160)
    ARTIST_COLOR = (196, 196, 196)
    ARTIST_SHADOW_COLOR = (6, 6, 6, 180)

    TITLE_FONT_SIZE_L1 = 38
    TITLE_FONT_SIZE_L2 = 34
    ARTIST_FONT_SIZE_L1 = 25
    ARTIST_FONT_SIZE_L2 = 25
    LYRICS_FONT_SIZE = 30

    def __init__(self, fonts_dir_path: str = FONTS_DIR_PATH) -> None:
        title_font_path = os.path.join(fonts_dir_path, "Onest-Bold.ttf")
        artist_font_path = os.path.join(fonts_dir_path, "Onest-Light.ttf")
        lyrics_font_path = os.path.join(fonts_dir_path, "Roboto-Light.ttf")
        self.title_font_l1 = ImageFont.truetype(title_font_path, self.TITLE_FONT_SIZE_L1)
        self.title_font_l2 = ImageFont.truetype(title_font_path, self.TITLE_FONT_SIZE_L2)
        self.artist_font_l1 = ImageFont.truetype(artist_font_path, self.ARTIST_FONT_SIZE_L1)
        self.artist_font_l2 = ImageFont.truetype(artist_font_path, self.ARTIST_FONT_SIZE_L2)
        self.lyrics_font = ImageFont.truetype(lyrics_font_path, self.LYRICS_FONT_SIZE)

    def create(
        self,
        lines: list[str],
        song_artist: str,
        song_title: str,
        cover_path: str | None = None,
        cover_bytes: bytes | None = None,
        output_path: str | None = None,
    ) -> BytesIO:
        result_image = self._prepare_image()
        cover_image = self._prepare_cover_image(img_bytes=cover_bytes, img_path=cover_path)
        self._process_cover_image(cover_image, result_image)
        self._draw_lyrics_text(result_image, lines)
        self._prepare_footer(result_image, song_artist, song_title)

        if output_path:
            result_image.save(output_path, format="PNG", quality=95)

        img_bytes = BytesIO()
        result_image.save(img_bytes, format="PNG", quality=95)
        img_bytes.seek(0)

        return img_bytes

    def _prepare_image(self) -> Image.Image:
        # Preparing empty base image
        return Image.new("RGBA", self.IMAGE_SIZE, (0, 0, 0, 255))

    def _prepare_footer(self, base_image: Image.Image, song_artist: str, song_title: str) -> None:
        # Creating the footer panel
        footer = ImageDraw.Draw(base_image)
        footer.rectangle(
            [
                (0, self.IMAGE_HEIGHT - self.FOOTER_HEIGHT),
                (self.IMAGE_WIDTH, self.IMAGE_HEIGHT),
            ],
            fill=self.FOOTER_COLOR,
        )
        self._process_footer_text(footer, song_artist, song_title)

    def _process_footer_text(self, footer: TImageDraw, song_artist: str, song_title: str) -> None:

        title_lines = get_wrapped_lines(song_title, self.title_font_l1, self.MAX_TITLE_WIDTH)
        title_lines_count = len(title_lines)

        if title_lines_count == 0:
            raise ImageBuilderError("Unable to process song title")

        if title_lines_count == 2:
            title_font = self.title_font_l2
            artist_font = self.artist_font_l2
            offset_between_title_and_artist = self.OFFSET_BETWEEN_TITLE_AND_ARTIST_L2
        else:
            title_font = self.title_font_l1
            artist_font = self.artist_font_l1
            offset_between_title_and_artist = self.OFFSET_BETWEEN_TITLE_AND_ARTIST_L1

        if title_lines:
            title_line_height = title_font.size
            total_title_height = (
                title_lines_count * title_line_height + (title_lines_count - 1) * self.OFFSET_BETWEEN_TITLE_LINES
            )
        else:
            raise ImageBuilderError("Invalid title lines")

        # Drawing text title line(s) with shadow
        if title_lines_count == 2:
            title_start_y = self.FOOTER_Y + 17
        else:
            title_start_y = self.FOOTER_Y + 32

        shadow_offset = 3
        curr_title_line_y = float(title_start_y)
        for line in title_lines:
            line_x, line_y = self.FOOTER_TEXT_X, curr_title_line_y

            footer.text(
                (line_x + shadow_offset, line_y + shadow_offset),
                line,
                font=title_font,
                fill=self.TITLE_SHADOW_COLOR,
                # anchor="lm"
            )
            footer.text(
                (line_x, line_y),
                line,
                font=title_font,
                fill=self.TITLE_COLOR,
                # anchor="lm"
            )
            curr_title_line_y += title_line_height + self.OFFSET_BETWEEN_TITLE_LINES

        # Drawing text artist text with shadow
        artist_x = self.FOOTER_TEXT_X
        artist_y = title_start_y + total_title_height + offset_between_title_and_artist
        shadow_offset = 1
        footer.text(
            (artist_x + shadow_offset, artist_y + shadow_offset),
            song_artist,
            font=artist_font,
            fill=self.ARTIST_SHADOW_COLOR,
            anchor="lm",
        )
        footer.text(
            (artist_x, artist_y),
            song_artist,
            font=artist_font,
            fill=self.ARTIST_COLOR,
            anchor="lm",
        )

    def _prepare_cover_image(self, img_bytes: bytes | None = None, img_path: str | None = None) -> TImage:
        if not img_bytes and not img_path:
            raise ImageBuilderError("Either img_bytes or img_path must be provided")

        if img_bytes:
            cover_image = Image.open(BytesIO(img_bytes))
        else:
            cover_image = Image.open(cast(str, img_path))

        return cover_image.convert("RGBA")

    def _process_cover_image(self, cover_image: Image.Image, base_image: Image.Image) -> None:
        cover_area_width = self.IMAGE_WIDTH
        cover_area_height = self.IMAGE_HEIGHT - self.FOOTER_HEIGHT

        cover_ratio = cover_image.width / cover_image.height
        area_ratio = cover_area_width / cover_area_height

        if cover_ratio > area_ratio:
            # Resizing by height
            new_height = cover_area_height
            new_width = int(new_height * cover_ratio)
        else:
            # Resizing by width
            new_width = cover_area_width
            new_height = int(new_width / cover_ratio)

        resized_cover = cover_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Centering cover position
        x_offset = (self.IMAGE_WIDTH - new_width) // 2
        y_offset = (cover_area_height - new_height) // 2

        # Pasting cover to center of base image
        base_image.paste(resized_cover, (x_offset, y_offset))

    def _draw_lyrics_text(self, base_image: Image.Image, lyrics_lines: list[str]) -> None:
        lyrics_image = Image.new("RGBA", self.IMAGE_SIZE, (0, 0, 0, 0))
        draw = ImageDraw.Draw(lyrics_image, "RGBA")

        lyrics_data = self._prepare_lyrics_lines(lyrics_lines)

        curr_y = float(self.LYRICS_BOTTOM_POSITION_Y) - (
            sum(line_data.total_line_height for line_data in lyrics_data)
            + (len(lyrics_data) - 1) * self.LYRICS_LINE_SPACING
        )
        for line_data in lyrics_data:
            self._process_line_text(draw, line_data, curr_y)
            curr_y += line_data.total_line_height + self.LYRICS_LINE_SPACING

        base_image.alpha_composite(lyrics_image)

    def _prepare_lyrics_lines(self, lines: list[str]) -> list[LyricsLineData]:
        lyrics_data = []

        for line in lines:
            processed_lines = []
            line_widths = []
            line_heights = []
            total_line_height = 0.0
            for wrapped_line in get_wrapped_lines(
                line,
                self.lyrics_font,
                self.LYRICS_LINE_MAX_WIDTH_SOFT,
                self.LYRICS_LINE_MAX_WIDTH_HARD,
            ):
                processed_lines.append(wrapped_line)
                text_bbox = self.lyrics_font.getbbox(wrapped_line)
                line_widths.append(text_bbox[2] - text_bbox[0])
                line_heights.append(self.lyrics_font.size + self.LYRICS_LINE_PADDING * 2)

            total_line_height += sum(line_heights) + (len(processed_lines) - 1) * self.LYRICS_WRAPPED_LINE_SPACING

            lyrics_data.append(
                LyricsLineData(
                    lyrics_text=processed_lines,
                    line_widths=line_widths,
                    line_heights=line_heights,
                    total_line_height=total_line_height,
                )
            )

        return lyrics_data

    def _process_line_text(self, draw: TImageDraw, line_data: LyricsLineData, current_y: float) -> None:

        text_start_x = self.LYRICS_LINE_OFFSET_X

        for idx, wrapped_line in enumerate(line_data.lyrics_text):
            # Calculating rectangle coordinates for current line
            text_start_x = self.LYRICS_LINE_OFFSET_X if idx == 0 else self.LYRICS_WRAPPED_LINE_OFFSET_X
            rect_x1 = text_start_x
            rect_x2 = text_start_x + line_data.line_widths[idx] + self.LYRICS_LINE_PADDING * 2
            rect_y1 = current_y
            rect_y2 = rect_y1 + line_data.line_heights[idx]

            draw.rounded_rectangle(
                [rect_x1, rect_y1, rect_x2, rect_y2],
                radius=2,
                fill=self.LYRICS_LINE_BACKGROUND_COLOR,
                outline=self.LYRICS_LINE_BORDER_COLOR,
                width=1,
            )

            text_x = text_start_x + self.LYRICS_LINE_PADDING
            text_y = rect_y1 + (rect_y2 - rect_y1) // 2

            draw.text(
                (text_x, text_y),
                wrapped_line,
                font=self.lyrics_font,
                fill=self.LYRICS_LINE_TEXT_COLOR,
                anchor="lm",
            )

            current_y = rect_y2 + self.LYRICS_WRAPPED_LINE_SPACING

            if current_y > self.LYRICS_BOTTOM_POSITION_Y:
                break
