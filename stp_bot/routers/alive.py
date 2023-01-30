from aiogram import Router, types

router = Router()


@router.message(commands=['alive'], state=None)
async def ftp(message: types.Message):
    await message.answer(text='Will be implemented soon')
