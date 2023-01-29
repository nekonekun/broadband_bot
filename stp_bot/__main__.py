from configargparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from setproctitle import setproctitle
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import logging
import asyncio

logging.basicConfig(level=logging.INFO)


ENV_VAR_PREFIX = 'STPBOT_'


parser = ArgumentParser(
    auto_env_var_prefix=ENV_VAR_PREFIX, allow_abbrev=False,
    formatter_class=ArgumentDefaultsHelpFormatter,
    add_help=True,
)

group = parser.add_argument_group('Bot')
group.add_argument('--token', '-t', help='Bot token', required=True)


def main():
    args = parser.parse_args()
    token = args.token
    setproctitle(os.path.basename(sys.argv[0]))
    asyncio.run(bot_main(token=token))


async def bot_main(token: str):
    bot = Bot(token=token, parse_mode='html')
    dp = Dispatcher(storage=MemoryStorage())

    await dp.start_polling(bot)
