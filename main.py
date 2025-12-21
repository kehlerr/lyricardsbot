import asyncio
import logging
import os

from settings import APP_NAME, LOGGING_LEVEL

from bot import LyricardsBot


def setup_logger() -> logging.Logger:
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(LOGGING_LEVEL)
    log_handler_stream = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(levelname)s][%(asctime)s] %(message)s", "%m/%d/%Y-%H:%M:%S"
    )
    log_handler_stream.setFormatter(formatter)
    logger.addHandler(log_handler_stream)
    return logger


def main() -> None:
    logger = logging.getLogger(APP_NAME)

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.critical("TELEGRAM_BOT_TOKEN is not set")
        exit(-1)

    bot = LyricardsBot()
    bot.setup_bot(bot_token)

    asyncio.run(bot.start_polling())


if __name__ == "__main__":
    setup_logger()
    main()
