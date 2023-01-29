from aiogram import Router, types
from aiogram.filters.command import CommandObject
from aiogram.types import BufferedInputFile
from asyncio.exceptions import TimeoutError
from stp_bot.services.ftp import FTPHelper

router = Router()


@router.message(commands=['ftp'], state=None)
async def ftp(message: types.Message,
              command: CommandObject,
              ftp_helper: FTPHelper):
    ip = command.args
    try:
        backup_file = await ftp_helper.get_backup_file(ip)
    except TimeoutError as e:
        await message.answer(text='FTP server is not responding')
        return None
    if not backup_file:
        await message.answer(text='Backup file was not found on FTP server')
        return None
    document = BufferedInputFile(backup_file.content.encode('utf-8'),
                                 filename=backup_file.filename)
    modify_time = str(backup_file.modify_time)
    modify_time = 'Modified at ' + modify_time
    await message.answer_document(document=document, caption=modify_time)
