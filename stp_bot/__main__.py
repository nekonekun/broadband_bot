from configargparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from setproctitle import setproctitle
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import logging
import asyncio

import stp_bot.routers as routers
from stp_bot.services.ftp import FTPHelper

logging.basicConfig(level=logging.INFO)


ENV_VAR_PREFIX = 'STPBOT_'


parser = ArgumentParser(
    auto_env_var_prefix=ENV_VAR_PREFIX, allow_abbrev=False,
    formatter_class=ArgumentDefaultsHelpFormatter,
    add_help=True,
)

group = parser.add_argument_group('Bot')
group.add_argument('--token', '-t', help='Bot token', required=True)

group = parser.add_argument_group('FTP')
group.add_argument('--ftp-host', help='FTP host', required=True)
group.add_argument('--ftp-username', help='FTP username', required=True)
group.add_argument('--ftp-password', help='FTP password', required=True)
group.add_argument('--ftp-folder', help='FTP folder', required=True)


def main():
    args = parser.parse_args()
    token = args.token
    ftp_host = args.ftp_host
    ftp_username = args.ftp_username
    ftp_password = args.ftp_password
    ftp_folder = args.ftp_folder
    ftp_helper = FTPHelper(ftp_host, ftp_username, ftp_password, ftp_folder)
    setproctitle(os.path.basename(sys.argv[0]))
    asyncio.run(bot_main(token=token, ftp_helper=ftp_helper))


async def bot_main(token: str, ftp_helper: FTPHelper):
    bot = Bot(token=token, parse_mode='html')
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(routers.ftp_router)

    await dp.start_polling(bot, ftp_helper=ftp_helper)
