import aioftp
from dataclasses import dataclass
import datetime


@dataclass
class BackupFile:
    filename: str
    modify_time: datetime.datetime
    content: str


class FTPHelper:
    def __init__(self,
                 host: str,
                 username: str,
                 password: str,
                 folder: str = ''):
        self.host: str = host
        self.username: str = username
        self.password: str = password
        if folder:
            if not folder.startswith('/'):
                folder = '/' + folder
            if not folder.endswith('/'):
                folder = folder + '/'
        self.folder = folder

    async def get_backup_file(self, ip: str) -> BackupFile | None:
        filename = f'{ip}.cfg'
        async with aioftp.Client.context(host=self.host,
                                         user=self.username,
                                         password=self.password,
                                         connection_timeout=5) as client:
            if self.folder:
                await client.change_directory(self.folder)
            file_info = await client.list(filename)
            if not file_info:
                return None
            path, info = file_info[0]
            modify_time = datetime.datetime.strptime(info['modify'],
                                                     '%Y%m%d%H%M%S')
            content = ''
            async with client.download_stream(filename) as stream:
                async for block in stream.iter_by_block():
                    content += block.decode('utf-8')
            return BackupFile(filename, modify_time, content)
