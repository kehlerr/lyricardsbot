import logging

from settings import APP_NAME


logger = logging.getLogger(APP_NAME)


class LyricardsBot:
    def __init__(self) -> None:
        ...

    def setup_bot(self, bot_token: str) -> None:
        ...

    async def start_polling(self) -> None:
        ...
