import aiohttp
import uuid

MAGIC_NO_AUTH_METHODS = ['user.login', 'apiinfo.version']


class ZabbixCategory:
    def __init__(self, category: str, api: 'ZabbixAPI'):
        self._api = api
        self._cat = category

    def __getattr__(self, action: str):
        async def method(**kwargs):
            return await self._api._request(
                method=f'{self._cat}.{action}',
                **kwargs)
        return method


class ZabbixAPI:
    def __init__(self, url: str, username: str, password: str):
        self._url = url
        self._username = username
        self._password = password
        self._in_use = 0
        self._session: aiohttp.ClientSession | None = None
        self._auth: str | None = None
        self._id: str | None = None

    def _make_request_body(self, method: str, params):
        body = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params or [],
            'id': self._id,
        }
        if method not in MAGIC_NO_AUTH_METHODS:
            body['auth'] = self._auth
        return body

    async def _request(self, method: str, **kwargs):
        async with self._session.post(
                url=self._url,
                json=self._make_request_body(method, kwargs)
        ) as response:
            content = await response.json()
        if 'error' in content:
            raise RuntimeError(
                content['error']['message'] + ' ' + content['error']['data']
            )
        return content['result']

    def __getattr__(self, item):
        return ZabbixCategory(item, self)

    async def __aenter__(self):
        if (self._in_use == 0) and (not self._session):
            headers = {
                'Content-Type': 'application/json-rpc'
            }
            self._session = aiohttp.ClientSession(headers=headers)
            self._id = str(uuid.uuid1())
            self._auth = await self.user.login(username=self._username,
                                               password=self._password)
        self._in_use += 1
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._in_use -= 1
        if (self._in_use == 0) and self._session:
            await self.user.logout()
            await self._session.close()
            self._session = None
            self._auth = None
