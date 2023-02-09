import datetime
import pytest
from stp_bot.services.ftp import FTPHelper


@pytest.mark.asyncio
async def test_existing_file(ftpserver):
    helper = FTPHelper('127.0.0.1', 'user', 'pass', 'tftp', 31175)
    backup_file = await helper.get_backup_file('10.0.1.2')
    assert backup_file is not None
    assert backup_file.content == 'Fake backup file'
    assert backup_file.filename == '10.0.1.2.cfg'
    assert isinstance(backup_file.modify_time, datetime.datetime)


@pytest.mark.asyncio
async def test_non_existing_file(ftpserver):
    helper = FTPHelper('127.0.0.1', 'user', 'pass', 'tftp', 31175)
    backup_file = await helper.get_backup_file('10.0.1.3')
    assert backup_file is None

