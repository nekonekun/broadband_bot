from aiogram import BaseMiddleware, Bot
import aiogram.exceptions
from aiogram.types import Message
import logging
from typing import Callable, Awaitable, Any


class AccessMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: dict[str, Any]
    ) -> Any:
        bot = Bot.get_current()
        allowed_chats = data['allowed_chats']
        logger = logging.getLogger('aiogram.middlewares')
        for chat_id in allowed_chats:
            try:
                membership = await bot.get_chat_member(chat_id,
                                                       event.from_user.id)
            except aiogram.exceptions.TelegramBadRequest:
                logger.error(f'Bot is not member of chat {chat_id}')
                continue
            if membership.status in ['member', 'creator', 'administrator']:
                return await handler(event, data)
        username = event.from_user.username
        full_name = event.from_user.full_name
        user_id = event.from_user.id
        chat_id = event.chat.id
        logger.error(f'Attempt of unauthorized access '
                     f'from user @{username} '
                     f'({full_name}, {user_id}) '
                     f'in chat {chat_id}')
