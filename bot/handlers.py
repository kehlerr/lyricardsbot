import io
import logging
from enum import StrEnum
from typing import cast

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BufferedInputFile, Message

import bot.texts as T
from app import (
    AppError,
    CoverDownloadError,
    CoverType,
    Handlers,
    ImageBuilder,
    InvalidLyricsQueryError,
    LyricsFetchError,
    LyricsService,
    SongGeniusRepository,
    SongNotFoundError,
    SongRepository,
)
from settings import (
    APP_NAME,
    COVERS_DIR_PATH,
    FONTS_DIR_PATH,
    GENIUS_API_TOKEN,
    LYRICS_DIR_PATH,
    QUERIES_DIR_PATH,
    QUERY_LENGTH_LIMIT,
    TELEGRAM_BOT_USERNAME,
)

logger = logging.getLogger(APP_NAME)


router = Router()


class QueryType(StrEnum):
    DEFAULT = "default"
    ARTIST_COVER = "artist_cover"
    CUSTOM_COVER = "custom_cover"


_core_handlers = Handlers(
    SongRepository(
        SongGeniusRepository(GENIUS_API_TOKEN),
        QUERIES_DIR_PATH,
        LYRICS_DIR_PATH,
        COVERS_DIR_PATH,
    ),
    LyricsService(),
    ImageBuilder(FONTS_DIR_PATH),
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(T.WELCOME_TEXT, parse_mode="Markdown")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(T.HELP_TEXT, parse_mode="Markdown")


@router.message(Command("artist"))
async def process_lyrics_query_artist_cover(message: Message, bot: Bot) -> None:
    if not message.text:
        await message.answer(T.INVALID_LYRICS_QUERY_ERROR_TEXT, parse_mode="Markdown")
        return

    await _process_lyrics_query(message, bot, message.text.split(maxsplit=1)[-1], QueryType.ARTIST_COVER)


@router.message(F.photo)
async def process_lyrics_query_custom_cover(message: Message, bot: Bot) -> None:
    if not message.photo:
        await message.answer(T.INVALID_LYRICS_QUERY_ERROR_TEXT, parse_mode="Markdown")
        return

    query = message.caption or message.text or ""
    if not query:
        await message.answer(T.INVALID_LYRICS_QUERY_ERROR_TEXT, parse_mode="Markdown")
        return

    await _process_lyrics_query(message, bot, query, QueryType.CUSTOM_COVER)


@router.message()
async def on_received_message(message: Message, bot: Bot) -> None:
    await _process_lyrics_query(message, bot, message.text or "", QueryType.DEFAULT)


async def _process_lyrics_query(message: Message, bot: Bot, query: str, query_type: QueryType) -> None:
    await bot.send_chat_action(message.chat.id, "typing")

    query = query.replace(TELEGRAM_BOT_USERNAME, "").strip()
    if not query:
        await message.answer(T.INVALID_LYRICS_QUERY_ERROR_TEXT, parse_mode="Markdown")
        return

    if len(query) > QUERY_LENGTH_LIMIT:
        await message.answer(T.TOO_LONG_QUERY_ERROR_TEXT, parse_mode="Markdown")
        return

    match query_type:
        case QueryType.CUSTOM_COVER:
            photo_buffer = io.BytesIO()
            await bot.download(file=cast(list, message.photo)[-1].file_id, destination=photo_buffer)

            photo_buffer.seek(0)
            handler_fn = _core_handlers.get_lyrics_on_song_cover(query, CoverType.CUSTOM, photo_buffer.read())
        case QueryType.ARTIST_COVER:
            handler_fn = _core_handlers.get_lyrics_on_song_cover(query, CoverType.ARTIST)
        case _:
            handler_fn = _core_handlers.get_lyrics_on_song_cover(query, CoverType.SONG)

    try:
        image = await handler_fn
    except InvalidLyricsQueryError:
        error_text = T.INVALID_LYRICS_QUERY_ERROR_TEXT
    except CoverDownloadError:
        error_text = T.COVER_DOWNLOAD_ERROR_TEXT
    except LyricsFetchError:
        error_text = T.LYRICS_FETCH_ERROR_TEXT
    except SongNotFoundError:
        error_text = T.SONG_NOT_FOUND_ERROR_TEXT.format(query)
    except AppError:
        error_text = T.APP_ERROR_TEXT
    except Exception as exc:
        error_text = T.DEFAULT_ERROR_TEXT
        logger.exception(exc)
    else:
        photo = BufferedInputFile(file=image, filename="photo.png")
        await message.answer_photo(photo=photo)
        return

    await message.answer(error_text, parse_mode="Markdown")
