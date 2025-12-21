from decouple import config


APP_NAME = config("APP_NAME", default="lyricardsbot", cast=str)

LOGGING_LEVEL = config("LOGGING_LEVEL", default="INFO", cast=str)

TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN", cast=str)
GENIUS_API_TOKEN = config("GENIUS_API_TOKEN", cast=str)