from aiogram import Router, types
from aiogram.filters.command import CommandObject

from ..services.alive import AliveHelper

router = Router()


@router.message(commands=['aliveplus'],
                state=None,
                flags={'long_operation': 'typing'})
async def alive_plus(message: types.Message,
                     command: CommandObject,
                     alive_helper: AliveHelper):
    ip = command.args
    alive_ports = await alive_helper.get_alive_ports(ip)
    if not alive_ports:
        await message.answer(text='Kinda strange, '
                                  'but no alive ports on this switch')
        return
    ports_str = [
        port.number if not port.is_magistral else f'[{port.number}]'
        for port in alive_ports
    ]
    header = ', '.join(ports_str)
    body = ''
    for port in alive_ports:
        status = 'up' if port.is_up else 'down'
        if port.is_magistral:
            line = f'[{port.number}] <b>{status}</b> <i>{port.alias}</i>'
        elif port.latest_mac:
            mac_date = str(port.latest_mac_date.date())
            line = f'{port.number} <b>{status}</b> <i>{port.alias}</i>, ' \
                   f'<code>{port.latest_mac} {mac_date}</code>'
        else:
            line = f'{port.number} <b>{status}</b> <i>{port.alias}</i>'
        body += line
        body += '\n'
    await message.answer(text=ip + '\n' + header + '\n' + body)


@router.message(commands=['alive'],
                state=None,
                flags={'long_operation': 'typing'})
async def alive(message: types.Message,
                command: CommandObject,
                alive_helper: AliveHelper):
    ip = command.args
    alive_ports = await alive_helper.get_alive_ports(ip)
    if not alive_ports:
        await message.answer(text='Kinda strange, '
                                  'but no alive ports on this switch')
        return
    ports_str = [
        port.number if not port.is_magistral else f'[{port.number}]'
        for port in alive_ports
    ]
    text = ip
    text += '\n'
    text += ', '.join(ports_str)
    await message.answer(text=text)
