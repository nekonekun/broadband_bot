import pytest
from stp_bot.services.zabbix import ZabbixAPI


def make_response(response_identifier: str):
    available_responses = {
        'user.login.success': {'jsonrpc': '2.0', 'result': '9e9471c27edf1830be27dc1c5d2c7c05', 'id': 'chaotic'},
        'user.login.fail': {'jsonrpc': '2.0', 'error': {'code': -32500, 'message': 'Application error.', 'data': 'Incorrect user name or password or account is temporarily blocked.'}, 'id': 'chaotic'},
        'user.logout': {'jsonrpc': '2.0', 'result': True, 'id': 'chaotic'},
        'incorrect.method': {'jsonrpc': '2.0', 'error': {'code': -32601, 'message': 'Method not found.', 'data': 'Incorrect API "incorrect".'}, 'id': 'chaotic'}
    }
    return available_responses[response_identifier]


class MockResponse:
    def __init__(self, j: dict):
        self._json = j

    async def json(self):
        return self._json

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self


@pytest.mark.asyncio
async def test_session_open_close(mocker):
    zbx = ZabbixAPI('http://127.0.0.1/jsonrpc_api.php', 'user', 'pass')
    mocker.patch(
        'aiohttp.ClientSession.post',
        return_value=MockResponse(make_response('user.login.success'))
    )
    assert zbx._session is None
    async with zbx:
        assert zbx._session is not None
        async with zbx:
            assert zbx._in_use == 2
            assert zbx._session is not None
        assert zbx._session is not None
        mocker.patch(
            'aiohttp.ClientSession.post',
            return_value=MockResponse(make_response('user.logout'))
        )
    assert zbx._session is None


@pytest.mark.asyncio
async def test_login_logout(mocker):
    zbx = ZabbixAPI('http://127.0.0.1/jsonrpc_api.php', 'user', 'pass')
    mocker.patch(
        'aiohttp.ClientSession.post',
        return_value=MockResponse(make_response('user.login.success'))
    )
    assert zbx._auth is None
    async with zbx:
        assert zbx._auth is not None
    assert zbx._auth is None


@pytest.mark.asyncio
async def test_login_fail(mocker):
    zbx = ZabbixAPI('http://127.0.0.1/jsonrpc_api.php', 'user', 'pass')
    mocker.patch(
        'aiohttp.ClientSession.post',
        return_value=MockResponse(make_response('user.login.fail'))
    )
    assert zbx._auth is None
    with pytest.raises(RuntimeError):
        await zbx.__aenter__()
    assert zbx._auth is None


@pytest.mark.asyncio
async def test_incorrect_api_endpoint(mocker):
    zbx = ZabbixAPI('http://127.0.0.1/jsonrpc_api.php', 'user', 'pass')
    mocker.patch(
        'aiohttp.ClientSession.post',
        return_value=MockResponse(make_response('user.login.success'))
    )
    async with zbx:
        mocker.patch(
            'aiohttp.ClientSession.post',
            return_value=MockResponse(make_response('incorrect.method'))
        )
        with pytest.raises(RuntimeError):
            await zbx.incorrect.method()
        assert zbx._session is not None
        assert zbx._auth is not None
        mocker.patch(
            'aiohttp.ClientSession.post',
            return_value=MockResponse(make_response('user.logout'))
        )
    assert zbx._session is None
    assert zbx._auth is None
