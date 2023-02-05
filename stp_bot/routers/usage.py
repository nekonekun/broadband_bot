from aiogram import Router, types
from aiogram.filters.command import CommandObject
from stp_bot.services.usage import UsageHelper
router = Router()


@router.message(commands=['usage'], state=None)
async def usage(message: types.Message,
                command: CommandObject,
                usage_helper: UsageHelper):
    ip = command.args
    text = f'Загрузка магистралей начиная с {ip}\n'
    answering_message = await message.answer(text)
    async for switch_info in usage_helper.get_usages(ip):
        text += f'\n{switch_info}\n'
        await answering_message.edit_text(text)
    text += 'Конец'
    await answering_message.edit_text(text)
