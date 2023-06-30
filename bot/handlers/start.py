from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command(commands="start"))
async def start(message: Message):
    await message.answer("Hello")
