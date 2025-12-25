import asyncio
import logging
from typing import Self

from aiogram import Bot as AiogramBot
from aiogram import Dispatcher, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiohttp import web

from settings import (
    APP_NAME,
    BOT_API_SERVER_URI,
    DEBUG,
    TELEGRAM_BOT_TOKEN,
    WEBHOOK_APP_HOST,
    WEBHOOK_APP_PORT,
    WEBHOOK_ENDPOINT_URL,
    WEBHOOK_SECRET,
)

from .handlers import router
from .middleware import CheckQueryMiddleware
from .server import create_webhook_server

logger = logging.getLogger(APP_NAME)


class LyricardsBot(AiogramBot):
    _dp: Dispatcher | None

    @classmethod
    def create(cls) -> Self:
        if DEBUG:
            return cls(token=TELEGRAM_BOT_TOKEN)

        logger.info("Creating local server...")
        api_server = TelegramAPIServer.from_base(BOT_API_SERVER_URI, is_local=True)

        logger.info("Creating session for local server...")
        session = AiohttpSession(api=api_server)

        logger.info("Starting bot...")
        return cls(token=TELEGRAM_BOT_TOKEN, session=session)

    def setup(self) -> None:
        router = self._create_router()
        self._dp = self._create_dispatcher(router)
        self.web_app = create_webhook_server(self, self._dp)

    def _create_router(self) -> Router:
        main_router = Router()
        main_router.message.middleware(CheckQueryMiddleware())
        main_router.include_router(router)
        return main_router

    def _create_dispatcher(self, main_router: Router) -> Dispatcher:
        dispatcher = Dispatcher()
        dispatcher.include_router(main_router)

        # Register startup hook to initialize webhook
        dispatcher.startup.register(self.on_startup)

        return dispatcher

    async def on_startup(self) -> None:
        if not DEBUG:
            await self.delete_webhook()
            await self.set_webhook(WEBHOOK_ENDPOINT_URL, secret_token=WEBHOOK_SECRET)

        logger.info("Bot started!")

    def start(self) -> None:
        if DEBUG:
            asyncio.run(self._start_polling())
        else:
            self._start_server()

    async def _start_polling(self) -> None:

        if not self._dp:
            raise RuntimeError("Dispatcher not initialized. Call setup() first.")

        logger.info("Starting polling...")
        try:
            await self._dp.start_polling(self)
        except Exception as e:
            logger.error(f"Error occured on start polling: {e}")
        finally:
            await self.session.close()

    def _start_server(self) -> None:
        logger.info("Starting webhook server...")
        web.run_app(self.web_app, host=WEBHOOK_APP_HOST, port=WEBHOOK_APP_PORT)

    async def logout(self) -> None:
        """Run this func before starting local server at first time."""
        result = await self.log_out()
        if result:
            exit(0)
