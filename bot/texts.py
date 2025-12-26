from app.exceptions import (
    TooLongQueryError,
    InvalidLyricsQueryError,
    CoverDownloadError,
    InvalidLyricsError,
    LyricsFetchError,
    SongNotFoundError,
    AppError,
)


WELCOME_TEXT = """
🎵 **Добро пожаловать в LyriCards Bot!**

Здесь ты можешь создать красивую карточку с текстом из песни на фоне обложки.

**Возможности:**
• Поиск текста песен на Genius
• Умный подбор наиболее подходящих строк
• Создание карточек песни с текстом на фоне обложки альбома/сингла/артиста

/help - Справка по использованию
"""

HELP_TEXT = """
🎵 **О LyriCards Bot**

🎨 **Как создать карточку с текстом из песни:**
• Просто напиши фрагмент из песни — точную строчку или как ты её помнишь
• Я найду песню и самую подходящую строку
• Создам стильное изображение с текстом и обложкой трека 🖼️

👤 **Как создать карточку с обложкой артиста?**
• Введи запрос с командой `/artist`:
`/artist <слова из песни>`

🖼️ **Как создать карточку с любым фото?**
• Прикрепи фото вместе со словами песни — карточка сгенерируется на основе твоего изображения

📄 **Как создать карточку с несколькими строками?**
• В конце или начале запроса укажи `+N` или `-M` (N,M = 1–9), чтобы добавить соседние строки:
`<слова песни> +3`, `<слова песни> -2`
• `+N` — добавляет N строк после найденной, `-M` — M строк до неё
• Можно указать оба числа сразу:
`<слова песни> -1 +6`

❓ **Что, если песня не нашлась или создаётся карточка с другой песней?**
• Попробуй уточнить запрос:
• напиши более точную строку
• убери слова «Припев», «Бридж», «Куплет»
• удали спецсимволы: кавычки, скобки и т.д.
• если есть число — попробуй написать его словами
"""

TOO_LONG_QUERY_ERROR_TEXT = """
Слишком длинный запрос 🌭
"""

INVALID_LYRICS_QUERY_ERROR_TEXT = """
😔 Неправильный запрос.
"""

COVER_DOWNLOAD_ERROR_TEXT = """
😔 При загрузке обложки произошла ошибка. Попробуйте позже.
"""

LYRICS_FETCH_ERROR_TEXT = """
😔 При получении текста песни произошла ошибка. Попробуйте составить другой запрос.
"""

INVALID_LYRICS_ERROR_TEXT = """
😔 Не удалось найти нужную строчку в тексте песни. Попробуйте другой запрос.
"""

SONG_NOT_FOUND_ERROR_TEXT = """
😔 Песня не найдена. Попробуйте составить другой запрос.
"""

APP_ERROR_TEXT = """
😔 Произошла какая-то ошибка... Попробуйте позже.
"""

DEFAULT_ERROR_TEXT = """
Произошла неизвестная ошибка...( Попробуйте позже.
"""

_TEXT_BY_EXCEPTION = {
    InvalidLyricsQueryError: INVALID_LYRICS_QUERY_ERROR_TEXT,
    TooLongQueryError: TOO_LONG_QUERY_ERROR_TEXT,
    CoverDownloadError: COVER_DOWNLOAD_ERROR_TEXT,
    LyricsFetchError: LYRICS_FETCH_ERROR_TEXT,
    InvalidLyricsError: INVALID_LYRICS_ERROR_TEXT,
    SongNotFoundError: SONG_NOT_FOUND_ERROR_TEXT,
    AppError: APP_ERROR_TEXT,
}


def get_app_error_text_by_exception(exc: AppError) -> str:
    return _TEXT_BY_EXCEPTION.get(type(exc), APP_ERROR_TEXT)