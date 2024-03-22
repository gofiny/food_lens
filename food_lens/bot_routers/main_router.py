from aiogram import Router
from aiogram.methods import TelegramMethod
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types.keyboard_button import KeyboardButton
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.filters import Filter
from aiogram import F


main_router = Router(name=__name__)


class MFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return True

@main_router.message(MFilter())
async def handle_button_one(message: Message):
    await message.edit_text(text="new_text")


@main_router.message(F.text == "button two")
async def handle_button_one(message: Message):
    pass


@main_router.message()
async def no_answer(message: Message) -> TelegramMethod[Message]:
    inline_keyboard = InlineKeyboardBuilder()
    inline_keyboard.button(text="button one", callback_data="test")
    inline_keyboard.button(text="button two", callback_data="test")

    return message.answer("Some text", reply_markup=inline_keyboard.as_markup())
