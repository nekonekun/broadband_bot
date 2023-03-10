from aiogram import BaseMiddleware
from aiogram.types import Message
import logging
from typing import Callable, Awaitable, Any


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: dict[str, Any]
    ) -> Any:
        logger = logging.getLogger('aiogram.middlewares')
        username = event.from_user.username
        full_name = event.from_user.full_name
        user_id = event.from_user.id
        chat_id = event.chat.id
        logger.info(f'New message from user @{username} '
                    f'({full_name}, {user_id}) '
                    f'in chat {chat_id}')
        return await handler(event, data)
