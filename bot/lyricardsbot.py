import logging
from typing import Self

from aiogram import Bot as AiogramBot
from aiogram import Dispatcher, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from settings import APP_NAME, BOT_API_SERVER_URI, TELEGRAM_BOT_TOKEN, WEBHOOK_ENDPOINT_URL, WEBHOOK_SECRET

from .handlers import router
from .middleware import CheckQueryMiddleware
from .server import create_webhook_server

logger = logging.getLogger(APP_NAME)


class LyricardsBot(AiogramBot):
    @classmethod
    def create(cls) -> Self:
        logger.info("Creating local server...")
        api_server = TelegramAPIServer.from_base(BOT_API_SERVER_URI, is_local=True)

        logger.info("Creating session for local server...")
        session = AiohttpSession(api=api_server)

        logger.info("Starting bot...")
        return cls(token=TELEGRAM_BOT_TOKEN, session=session)

    def setup(self) -> None:
        router = self.create_router()
        dispatcher = self.create_dispatcher(router)
        self.web_app = create_webhook_server(self, dispatcher)

    def create_router(self) -> Router:
        main_router = Router()
        main_router.message.middleware(CheckQueryMiddleware())
        main_router.include_router(router)
        return main_router

    def create_dispatcher(self, main_router: Router) -> Dispatcher:
        dispatcher = Dispatcher()
        dispatcher.include_router(main_router)

        # Register startup hook to initialize webhook
        dispatcher.startup.register(self.on_startup)

        return dispatcher

    async def on_startup(self) -> None:
        await self.delete_webhook()
        await self.set_webhook(WEBHOOK_ENDPOINT_URL, secret_token=WEBHOOK_SECRET)

    async def logout(self) -> None:
        """Run this func before starting local server at first time."""
        result = await self.log_out()
        if result:
            exit(0)
