import logging
from typing import Any, Awaitable, Callable, cast

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from settings import APP_NAME, TELEGRAM_BOT_USERNAME

logger = logging.getLogger(APP_NAME)


class CheckQueryMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        message: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        msg = cast(Message, message)
        message_text = (msg.text or msg.caption or "").strip()
        if not message_text:
            return

        logger.debug("Got message text: %s", message_text)

        if msg.chat.type == "private" or message_text.startswith("/") or TELEGRAM_BOT_USERNAME in message_text:
            return await handler(cast(Message, message), data)
