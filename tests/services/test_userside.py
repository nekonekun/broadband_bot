import pytest
from stp_bot.services.userside import UsersideAPI
import json

responses = {
    'wrong key': (403, '{"error":"API Key Error Or IP Forbidden. Your Ip: 127.0.0.1"}'),
    'missing': (400, '{"error":"Unknown Arguments\/ObjectId"}'),
    'empty response': (200, ''),
    'device get_device_id': (200, '{"result":"OK","id":1107}'),
    'task get_list': (200, '{"list":"438277,438298,438429,438718,438792","count":5,"result":"OK"}'),
    'device get_data': (200, '{"result":"OK","data":{"1107":{"id":1107,"type_id":3,"name":"D-Link DES-3552","entrance":1,"ip":"2887129113","host":"172.22.24.25","mac":"001122998877","comment":"","inventory_id":1108,"location":"Санкт-Петербург, Центральный р-н, Дворцовая п-дь, 1 п.1 (100 этаж)(Бокс),0001","uplink_iface":"49","dnlink_iface":"","node_id":788,"customer_id":null,"interfaces":52,"podezd":1,"activity_time":"2022-02-10 12:40:04","uplink_iface_array":{"49":"49"},"dnlink_iface_array":[],"is_online":0,"snmp_proto":2,"snmp_community_ro":"public","snmp_community_rw":"private","snmp_port":161,"telnet_login":"login","telnet_pass":"pass"}}}'),
    'additional_data get_list': (200, '{"result":"OK"}')
}


class MockResponse:
    def __init__(self, status_code: int, content: str):
        self._status_code = status_code
        self._content = content

    async def json(self):
        return json.loads(self._content)

    @property
    def ok(self):
        return 200 <= self._status_code < 300

    @property
    def content(self):
        return self._content

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self


@pytest.mark.asyncio
async def test_session_open_close():
    us = UsersideAPI('http://127.0.0.1/api.php', 'key')
    async with us:
        assert us._session is not None
        async with us:
            assert us._in_use == 2
        assert us._session is not None
    assert us._session is None
    with pytest.raises(AttributeError):
        await us.category.action()


@pytest.mark.asyncio
async def test_wrong_api_key(mocker):
    mocker.patch('aiohttp.ClientSession.get',
                 return_value=MockResponse(*responses['wrong key']))
    us = UsersideAPI('http://127.0.0.1/api.php', 'wrong_key')
    async with us:
        with pytest.raises(RuntimeError):
            await us.category.action()


@pytest.mark.asyncio
async def test_empty_response(mocker):
    mocker.patch('aiohttp.ClientSession.get',
                 return_value=MockResponse(*responses['wrong key']))
    us = UsersideAPI('http://127.0.0.1/api.php', 'key')
    async with us:
        with pytest.raises(RuntimeError):
            await us.category.action()


@pytest.mark.asyncio
async def test_request_not_found(mocker):
    us = UsersideAPI('http://127.0.0.1/api.php', 'key')
    mocker.patch('aiohttp.ClientSession.get',
                 return_value=MockResponse(*responses['missing']))
    async with us:
        with pytest.raises(RuntimeError):
            await us.device.get_device_id()


@pytest.mark.asyncio
async def test_request_with_id_output(mocker):
    us = UsersideAPI('http://127.0.0.1/api.php', 'key')
    mocker.patch('aiohttp.ClientSession.get',
                 return_value=MockResponse(
                     *responses['device get_device_id']))
    async with us:
        existing_id = await us.device.get_device_id()
        assert isinstance(existing_id, int)
        assert existing_id == 1107


@pytest.mark.asyncio
async def test_request_with_data_output(mocker):
    us = UsersideAPI('http://127.0.0.1/api.php', 'key')
    mocker.patch('aiohttp.ClientSession.get',
                 return_value=MockResponse(*responses['device get_data']))
    async with us:
        response = await us.device.get_data(object_type='switch',
                                            object_id=1107)
        assert isinstance(response, dict)
        assert str(1107) in response


@pytest.mark.asyncio
async def test_request_with_list_output(mocker):
    us = UsersideAPI('http://127.0.0.1/api.php', 'key')
    mocker.patch('aiohttp.ClientSession.get',
                 return_value=MockResponse(*responses['task get_list']))
    async with us:
        response = await us.task.get_list(type_id=185)
        assert response is not None
        assert isinstance(response, list)


@pytest.mark.asyncio
async def test_request_with_other_output(mocker):
    us = UsersideAPI('http://127.0.0.1/api.php', 'key')
    mocker.patch('aiohttp.ClientSession.get',
                 return_value=MockResponse(*responses['additional_data get_list']))
    async with us:
        response = await us.additional_data.get_list(section=8)
        assert 'id' not in response
        assert 'data' not in response
        assert 'list' not in response
        assert isinstance(response, dict)
