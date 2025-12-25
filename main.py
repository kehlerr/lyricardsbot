import logging

from bot import LyricardsBot
from settings import APP_NAME, LOGGING_LEVEL


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
    bot.start()


if __name__ == "__main__":
    main()
