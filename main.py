import logging

from aiohttp import web

from bot import LyricardsBot
from settings import (APP_NAME, LOGGING_LEVEL, WEBHOOK_APP_HOST,
                      WEBHOOK_APP_PORT)


def setup_logger() -> logging.Logger:
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(LOGGING_LEVEL)
    log_handler_stream = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s][%(asctime)s] %(message)s", "%m/%d/%Y-%H:%M:%S")
    log_handler_stream.setFormatter(formatter)
    logger.addHandler(log_handler_stream)
    return logger


def main() -> None:
    setup_logger()

    bot = LyricardsBot.create()
    bot.setup()

    web.run_app(bot.web_app, host=WEBHOOK_APP_HOST, port=WEBHOOK_APP_PORT)


if __name__ == "__main__":
    main()
