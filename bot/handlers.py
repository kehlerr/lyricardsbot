from io import BytesIO
import logging
from enum import StrEnum
from typing import Any, cast

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BufferedInputFile, Message


import bot.texts as T
from app import (
    AppError,
    CoverType,
    Handlers,
    ImageBuilder,
    LyricsService,
    SongGeniusRepository,
    SongRepository,
)
from settings import (
    APP_NAME,
    COVERS_DIR_PATH,
    FONTS_DIR_PATH,
    GENIUS_API_TOKEN,
    LYRICS_DIR_PATH,
    QUERIES_DIR_PATH,
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
    message_text = message.text and message.text.split(maxsplit=1)[-1] or ""
    await _process_lyrics_query(message, bot, message_text, QueryType.ARTIST_COVER)


@router.message(F.photo)
async def process_lyrics_query_custom_cover(message: Message, bot: Bot) -> None:
    query = message.caption or message.text or ""
    await _process_lyrics_query(message, bot, query, QueryType.CUSTOM_COVER, custom_cover_file_id=cast(list, message.photo)[-1].file_id)


@router.message()
async def on_received_message(message: Message, bot: Bot) -> None:
    await _process_lyrics_query(message, bot, message.text or "", QueryType.DEFAULT)


async def _process_lyrics_query(message: Message, bot: Bot, query: str, query_type: QueryType, custom_cover_file_id: Any | None = None) -> None:
    await bot.send_chat_action(message.chat.id, "typing")

    additional_query = message.reply_to_message and message.reply_to_message.text or None
    try:
        lyrics_query = _core_handlers.parse_as_lyrics_query(query, additional_query)
    except AppError as exc:
        await message.answer(T.get_app_error_text_by_exception(exc), parse_mode="Markdown")
        return

    match query_type:
        case QueryType.CUSTOM_COVER:
            if not custom_cover_file_id:
                await message.answer(T.INVALID_LYRICS_QUERY_ERROR_TEXT, parse_mode="Markdown")
                return

            photo_buffer = BytesIO()
            await bot.download(file=custom_cover_file_id, destination=photo_buffer)
            photo_buffer.seek(0)
            handler_fn = _core_handlers.get_lyrics_on_song_cover(lyrics_query, CoverType.CUSTOM, photo_buffer.read())
        case QueryType.ARTIST_COVER:
            handler_fn = _core_handlers.get_lyrics_on_song_cover(lyrics_query, CoverType.ARTIST)
        case _:
            handler_fn = _core_handlers.get_lyrics_on_song_cover(lyrics_query, CoverType.SONG)

    try:
        image = await handler_fn
    except AppError as exc:
        error_text = T.get_app_error_text_by_exception(exc)
        logger.exception(exc)
    except Exception as exc:
        error_text = T.DEFAULT_ERROR_TEXT
        logger.exception(exc)
    else:
        photo = BufferedInputFile(file=image, filename="photo.png")
        await message.answer_photo(photo=photo)
        return

    await message.answer(error_text, parse_mode="Markdown")
