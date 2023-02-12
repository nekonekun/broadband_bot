from datetime import datetime, timedelta
from dataclasses import dataclass

from .userside import UsersideAPI


@dataclass
class AlivePort:
    number: str
    alias: str
    is_up: bool
    is_magistral: bool
    latest_mac: str | None = None
    latest_mac_date: datetime | None = None
    latest_mac_vlan: int | None = None


class AliveHelper:
    def __init__(self, userside_api: UsersideAPI):
        self.api = userside_api

    async def get_alive_ports(self, ip: str) -> list[AlivePort]:
        result = []
        async with self.api as instance:
            device_id = await instance.device.get_device_id(
                object_type='switch',
                data_typer='ip',
                data_value=ip,
            )
            device_id = str(device_id)
            device_data = await instance.device.get_data(object_type='switch',
                                                         object_id=device_id)
            device_data = device_data[device_id]
            uplinks = device_data['uplink_iface'].split(',')
            dnlinks = device_data['dnlink_iface'].split(',')
            magistrals = uplinks + dnlinks
            mac_list = await instance.device.get_mac_list(object_type='switch',
                                                          object_id=device_id)
            is_online = device_data['is_online']
            if is_online:
                real_iface_info = await instance.device.get_iface_info(
                    id=device_id)
                real_iface_info = real_iface_info['iface']
                real_iface_info = {
                    interface['ifNumber']: interface
                    for interface in real_iface_info
                }
        iface_info = list(device_data['ifaces'].values())
        for interface in iface_info:
            number = interface['ifNumber']
            if is_online:
                alias = real_iface_info[number].get('ifAlias', '')
                if real_iface_info[number].get('ifOperStatus', 0) == 1:
                    is_up = True
                else:
                    is_up = False
            else:
                alias = ''
                is_up = False
            number = str(number)
            if number in magistrals:
                is_magistral = True
            elif 'mag_' in alias:
                is_magistral = True
            else:
                is_magistral = False
            macs_on_port = list(filter(
                lambda mac: mac['port'] == interface['ifName'],
                mac_list))
            if macs_on_port:
                latest_mac_entry = max(
                    macs_on_port,
                    key=lambda x: datetime.fromisoformat(x['date_last'])
                )
                latest_mac = latest_mac_entry['mac']
                latest_mac_date = datetime.fromisoformat(
                    latest_mac_entry['date_last'])
                latest_mac_vlan = latest_mac_entry['vlan_id']
            else:
                latest_mac = None
                latest_mac_date = None
                latest_mac_vlan = None
            lowest_date = datetime.now() - timedelta(days=184)
            if not latest_mac:
                is_recent = False
            elif latest_mac_date < lowest_date:
                is_recent = False
            else:
                is_recent = True
            if is_up or is_recent or is_magistral:
                new_alive_port = AlivePort(
                    number, alias, is_up, is_magistral,
                    latest_mac, latest_mac_date, latest_mac_vlan
                )
                result.append(new_alive_port)
        return result
