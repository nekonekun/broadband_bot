from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
from configargparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import logging
import os
from setproctitle import setproctitle
import sys


from .middlewares.access import AccessMiddleware
from .middlewares.chat_action import ChatActionMiddleware
from .middlewares.log import LoggingMiddleware
from .services.ftp import FTPHelper
from .services.userside import UsersideAPI
from .services.alive import AliveHelper
from .services.zabbix import ZabbixAPI
from .services.usage import UsageHelper
from .routers.alive import router as alive_router
from .routers.ftp import router as ftp_router
from .routers.usage import router as usage_router

logging.basicConfig(level=logging.INFO)


ENV_VAR_PREFIX = 'STPBOT_'


parser = ArgumentParser(
    auto_env_var_prefix=ENV_VAR_PREFIX, allow_abbrev=False,
    formatter_class=ArgumentDefaultsHelpFormatter,
    add_help=True,
)

group = parser.add_argument_group('Bot')
group.add_argument('--token', '-t', help='Bot token', required=True)
group.add_argument('--allowed-chats',
                   help='If specified: only messages from specified chat '
                        'participants will be processed. Comma-separated',
                   required=False)

group = parser.add_argument_group('FTP')
group.add_argument('--ftp-host', help='FTP host', required=True)
group.add_argument('--ftp-username', help='FTP username', required=True)
group.add_argument('--ftp-password', help='FTP password', required=True)
group.add_argument('--ftp-folder', help='FTP folder', required=True)

group = parser.add_argument_group('Userside')
group.add_argument('--userside-url',
                   help='Userside API URL (including api.php)', required=True)
group.add_argument('--userside-key', help='Userside API key', required=True)

group = parser.add_argument_group('Zabbix')
group.add_argument('--zabbix-url',
                   help='Zabbix API URL (including api_jsonrpc.php)',
                   required=True)
group.add_argument('--zabbix-username',
                   help='Zabbix API username', required=True)
group.add_argument('--zabbix-password',
                   help='Zabbix API password', required=True)


def main():
    args = parser.parse_args()
    token = args.token
    ftp_host = args.ftp_host
    ftp_username = args.ftp_username
    ftp_password = args.ftp_password
    ftp_folder = args.ftp_folder
    ftp_helper = FTPHelper(ftp_host, ftp_username, ftp_password, ftp_folder)
    userside_url = args.userside_url
    userside_key = args.userside_key
    userside_api = UsersideAPI(userside_url, userside_key)
    alive_helper = AliveHelper(userside_api)
    zabbix_url = args.zabbix_url
    zabbix_username = args.zabbix_username
    zabbix_password = args.zabbix_password
    zabbix_api = ZabbixAPI(zabbix_url, zabbix_username, zabbix_password)
    usage_helper = UsageHelper(userside_api, zabbix_api)
    allowed_chats = args.allowed_chats
    if allowed_chats:
        allowed_chats = allowed_chats.split(',')
    setproctitle(os.path.basename(sys.argv[0]))
    asyncio.run(bot_main(token=token,
                         ftp_helper=ftp_helper,
                         alive_helper=alive_helper,
                         usage_helper=usage_helper,
                         allowed_chats=allowed_chats))


async def bot_main(token: str,
                   ftp_helper: FTPHelper,
                   alive_helper: AliveHelper,
                   usage_helper: UsageHelper,
                   allowed_chats: list | None):
    bot = Bot(token=token, parse_mode='html')
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(ftp_router)
    dp.include_router(alive_router)
    dp.include_router(usage_router)

    dp.message.middleware(ChatActionMiddleware())
    dp.message.middleware(LoggingMiddleware())
    if allowed_chats:
        dp.message.outer_middleware(AccessMiddleware())

    await dp.start_polling(bot,
                           ftp_helper=ftp_helper,
                           alive_helper=alive_helper,
                           usage_helper=usage_helper,
                           allowed_chats=allowed_chats)
