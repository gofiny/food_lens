from aiogram import Router
from aiogram.methods import TelegramMethod
from aiogram.types import Message

main_router = Router(name=__name__)


@main_router.message()
async def no_answer(message: Message) -> TelegramMethod[Message]:
    return message.answer("Test")
