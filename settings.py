import os
from pathlib import Path

import orjson as json
from decouple import config

ROOT_DIR_PATH = Path(__file__).resolve().parent

APP_NAME = config("APP_NAME", default="lyricardsbot", cast=str)

DEBUG = config("DEBUG", default=False, cast=bool)

LOGGING_LEVEL = config("LOGGING_LEVEL", default=DEBUG and "DEBUG" or "INFO", cast=str)

TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN", cast=str)
TELEGRAM_BOT_USERNAME = config("TELEGRAM_BOT_USERNAME", cast=str)


## TG API server settings
_BOT_API_SERVER_SCHEME = config("LYRICARDSBOT_TG_API_SERVER_SCHEME", default="http")
_BOT_API_SERVER_HOST = config("LYRICARDSBOT_TG_API_SERVER_HOST")
_BOT_API_SERVER_PORT = config("LYRICARDSBOT_TG_API_SERVER_PORT", cast=int, default=8081)
BOT_API_SERVER_URI = f"{_BOT_API_SERVER_SCHEME}://{_BOT_API_SERVER_HOST}:{_BOT_API_SERVER_PORT}"

## Webhook App settings
_WEBHOOK_SCHEME = config("LYRICARDSBOT_WEBHOOK_SCHEME", default="http")
_WEBHOOK_HOST = config("LYRICARDSBOT_WEBHOOK_HOST")
_WEBHOOK_PORT = config("LYRICARDSBOT_WEBHOOK_PORT", cast=int)
WEBHOOK_URI = f"{_WEBHOOK_SCHEME}://{_WEBHOOK_HOST}:{_WEBHOOK_PORT}"

WEBHOOK_APP_HOST = config("LYRICARDSBOT_WEBHOOK_APP_HOST", default="0.0.0.0")
WEBHOOK_APP_PORT = config("LYRICARDSBOT_WEBHOOK_APP_PORT", cast=int, default=_WEBHOOK_PORT)

WEBHOOK_ENDPOINT = config("LYRICARDSBOT_WEBHOOK_ENDPOINT")
WEBHOOK_ENDPOINT_URL = f"{WEBHOOK_URI}{WEBHOOK_ENDPOINT}"
WEBHOOK_SECRET = config("LYRICARDSBOT_WEBHOOK_SECRET")


GENIUS_API_TOKEN = config("GENIUS_API_TOKEN", cast=str)


_GENIUS_HEADERS_DEFAULT = {
    "accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
    "referer": "https://genius.com/search/embed",
    "priority": "u=1, i",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "sec-ch-ua-mobile": "?0",
    "accept-language": "en-US,en;q=0.9,ru;q=0.8",
}

_GENIUS_HEADERS_CUSTOM: dict[str, str] = json.loads(config("GENIUS_HEADERS", cast=str, default="{}"))
GENIUS_HEADERS: dict[str, str] = {**_GENIUS_HEADERS_DEFAULT, **_GENIUS_HEADERS_CUSTOM}

DATA_DIR_PATH = config("DATA_DIR_PATH", default=str(ROOT_DIR_PATH.joinpath("appdata").resolve()), cast=str)

QUERIES_DIR_PATH = config("QUERIES_DIR_PATH", default=os.path.join(DATA_DIR_PATH, "queries"), cast=str)
LYRICS_DIR_PATH = config("LYRICS_DIR_PATH", default=os.path.join(DATA_DIR_PATH, "lyrics"), cast=str)
COVERS_DIR_PATH = config("COVERS_DIR_PATH", default=os.path.join(DATA_DIR_PATH, "covers"), cast=str)
FONTS_DIR_PATH = config(
    "FONTS_DIR_PATH",
    default=str(ROOT_DIR_PATH.joinpath("resources", "fonts").resolve()),
    cast=str,
)

QUERY_LENGTH_LIMIT = config("QUERY_LENGTH_LIMIT", default=100, cast=int)
