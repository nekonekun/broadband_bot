from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re

from .userside import UsersideAPI
from .zabbix import ZabbixAPI


@dataclass
class InterfaceInfo:
    interface_number: int
    interface_speed: str | None = None
    interface_max_in: str | None = None
    interface_max_out: str | None = None


def humanize(speed: float, base: int = 1024) -> str:
    speeds = {
        0: 'bps',
        1: 'Kbps',
        2: 'Mbps',
        3: 'Gbps',
        4: 'Tbps'
    }

    def step(step_speed: float,
             step_base: int = 1024,
             step_power: int = 0) -> tuple[float, int, int]:
        if step_power == 4:
            return step_speed, step_base, step_power
        if step_speed < step_base:
            return step_speed, step_base, step_power
        return step(round(step_speed / step_base, 3), step_base, step_power + 1)

    result = step(speed, base, 0)
    return f"{result[0]} {speeds[result[2]]}"


@dataclass(init=True, repr=True)
class SwitchInfo:
    ip: str
    interfaces: list[InterfaceInfo] | None = field(default_factory=lambda: [])

    def __str__(self):
        text = self.ip
        if not self.interfaces:
            return text
        text += ' : '
        text += ','.join(str(interface.interface_number)
                         for interface in self.interfaces)
        text += '\n'
        if len(self.interfaces) == 0:
            return text
        for interface in self.interfaces:
            if len(self.interfaces) != 1:
                text += f'Interface {interface.interface_number}\n'
            if interface.interface_speed.isdigit():
                interface_speed = humanize(int(interface.interface_speed), 1000)
            else:
                interface_speed = interface.interface_speed
            text += f'Interface speed {interface_speed}\n'
            if interface.interface_max_in.isdigit():
                max_in = humanize(int(interface.interface_max_in))
            else:
                max_in = interface.interface_max_in
            if interface.interface_max_out.isdigit():
                max_out = humanize(int(interface.interface_max_out))
            else:
                max_out = interface.interface_max_out
            text += f'in {max_in} / ' \
                    f'out {max_out}\n'
        return text


class UsageHelper:
    def __init__(self, userside_api: UsersideAPI, zabbix_api: ZabbixAPI):
        self.userside_api = userside_api
        self.zabbix_api = zabbix_api

    async def get_usages(self, ip: str):
        while ip:
            switch_info = await self.get_switch_info(ip)
            yield switch_info
            if not switch_info.interfaces:
                return
            async with self.userside_api:
                device_id = await self.userside_api.device.get_device_id(
                    object_type='switch',
                    data_typer='ip',
                    data_value=ip,
                )
                commutation = await self.userside_api.commutation.get_data(
                    object_type='switch',
                    object_id=device_id,
                    is_finish_data='1'
                )
            neighbors = []
            for interface in switch_info.interfaces:
                number = str(interface.interface_number)
                if number not in commutation:
                    continue
                neighbor = commutation[number]['finish']
                if neighbor['object_type'] != 'switch':
                    continue
                neighbors.append(neighbor['object_id'])
            if neighbors:
                neighbors = set(neighbors)
                if len(neighbors) > 1:
                    return
                async with self.userside_api:
                    neighbor_id = str(neighbors.pop())
                    neighbor_data = await self.userside_api.device.get_data(
                        object_type='switch',
                        object_id=neighbor_id,
                        is_hide_ifaces_data=1,
                    )
                neighbor_data = neighbor_data[neighbor_id]
                ip = neighbor_data['host']
            else:
                neighbors = []
                async with self.userside_api:
                    ifaces_info = await self.userside_api.device.get_iface_info(
                        id=device_id
                    )
                ifaces_info = ifaces_info['iface']
                ifaces_info = {
                    element['count']: element
                    for element in ifaces_info
                }
                for interface in switch_info.interfaces:
                    possible_uplink_iface_info = ifaces_info.get(
                        interface.interface_number)
                    ip_reg = re.search(
                        r'mag_(.+)_up',
                        possible_uplink_iface_info.get('ifAlias', ''))
                    if not ip_reg:
                        continue
                    neighbors.append(ip_reg.group(1))
                neighbors = list(set(neighbors))
                if len(neighbors) != 1:
                    return
                ip = neighbors[0]

    async def get_switch_info(self, ip: str):
        async with self.userside_api:
            device_id = await self.userside_api.device.get_device_id(
                object_type='switch',
                data_typer='ip',
                data_value=ip,
            )
            ifaces_info = await self.userside_api.device.get_iface_info(
                id=device_id
            )
            ifaces_info = ifaces_info['iface']
            ifaces_info = {
                element['count']: element
                for element in ifaces_info
            }
            device_data = await self.userside_api.device.get_data(
                object_type='switch',
                object_id=device_id,
                is_hide_ifaces_data=1
            )
        device_data = device_data[str(device_id)]

        uplink_iface = device_data['uplink_iface']
        if uplink_iface:
            uplinks_commutation = uplink_iface.split(',')
        else:
            uplinks_commutation = []

        uplinks_aliases = list(filter(
            lambda x: re.search(r'mag_\d+\.\d+\.\d+\.\d+_up',
                                x.get('ifAlias', '')),
            ifaces_info.values()
        ))
        uplinks_aliases = [interface['count'] for interface in uplinks_aliases]

        uplinks_commutation = set(map(int, uplinks_commutation))
        uplinks_aliases = set(map(int, uplinks_aliases))

        uplinks = uplinks_commutation | uplinks_aliases

        if not uplinks:
            return SwitchInfo(ip=ip)
        switch_info = SwitchInfo(ip=ip)
        async with self.zabbix_api:
            for interface_number in uplinks:
                index = str(ifaces_info[interface_number]['ifIndex'])
                response = await self.zabbix_api.host.get(
                    filter={'host': ip},
                    output=['hostid'])
                device_id = response[0]['hostid']
                try:
                    items_interface_speed = await self.zabbix_api.item.get(
                        hostids=device_id,
                        filter={'snmp_oid': '1.3.6.1.2.1.31.1.1.1.15.' + index},
                        output=['name', 'snmp_oid', 'key_', 'lastvalue']
                    )
                    interface_speed = items_interface_speed[0]['lastvalue']
                except (IndexError, KeyError):
                    interface_speed = '?'
                today_midnight = datetime.now().replace(hour=0,
                                                        minute=0,
                                                        second=0,
                                                        microsecond=0)
                time_from = today_midnight - timedelta(days=30)
                time_from = time_from.timestamp()
                time_till = today_midnight
                time_till = time_till.timestamp()
                try:
                    items_in_traffic = await self.zabbix_api.item.get(
                        hostids=device_id,
                        filter={'snmp_oid': 'IF-MIB::ifHCInOctets.' + index},
                        output=['name', 'snmp_oid', 'key_', 'lastvalue']
                    )
                    item_id = items_in_traffic[0]['itemid']
                    trends = await self.zabbix_api.trend.get(
                        itemids=item_id,
                        time_from=int(time_from),
                        time_till=int(time_till),
                        output=['clock', 'value_max']
                    )
                    interface_max_in = max(int(x['value_max']) for x in trends)
                except (IndexError, KeyError):
                    interface_max_in = '?'
                try:
                    items_out_traffic = await self.zabbix_api.item.get(
                        hostids=device_id,
                        filter={'snmp_oid': 'IF-MIB::ifHCOutOctets.' + index},
                        output=['name', 'snmp_oid', 'key_', 'lastvalue']
                    )
                    item_id = items_out_traffic[0]['itemid']
                    trends = await self.zabbix_api.trend.get(
                        itemids=item_id,
                        time_from=int(time_from),
                        time_till=int(time_till),
                        output=['clock', 'value_max']
                    )
                    interface_max_out = max(int(x['value_max']) for x in trends)
                except (IndexError, KeyError):
                    interface_max_out = '?'
                new_interface = InterfaceInfo(interface_number,
                                              interface_speed,
                                              str(interface_max_in),
                                              str(interface_max_out))
                switch_info.interfaces.append(new_interface)
        return switch_info
