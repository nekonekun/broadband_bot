import datetime
import logging
import aioftp
from dataclasses import dataclass


@dataclass
class BackupFile:
    filename: str
    modify_time: datetime.datetime
    content: str


class FTPHelper:
    def __init__(self, host: str, username: str, password: str):
        self.host: str = host
        self.username: str = username
        self.password: str = password

    async def get_backup_file(self, ip: str) -> BackupFile | None:
        filename = f'{ip}.cfg'
        filepath = '/tftp/' + filename
        async with aioftp.Client.context(host=self.host,
                                         user=self.username,
                                         password=self.password,
                                         connection_timeout=5) as client:
            if await client.exists(filepath):
                ls = await client.list('/tftp/')
                ls = {file[0].name: file[1] for file in ls}
                modify_time = ls[filename]['modify']
                modify_time = datetime.datetime.strptime(modify_time,
                                                         '%Y%m%d%H%M%S')
                content = ''
                async with client.download_stream(filepath) as stream:
                    async for block in stream.iter_by_block():
                        content += block.decode('utf-8')
                return BackupFile(filename, modify_time, content)
            else:
                return None
