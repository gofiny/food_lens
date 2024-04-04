from aiogram import Router
from aiogram.methods import TelegramMethod
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types.keyboard_button import KeyboardButton
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.filters import Filter
from aiogram import F


main_router = Router(name=__name__)


class MFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return True


class CFilter(Filter):
    def __init__(self, data: str):
        self._data = data

    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data == self._data


@main_router.callback_query(CFilter("one"))
async def handle_button_one(callback: CallbackQuery):
    inline_keyboard = InlineKeyboardBuilder()
    inline_keyboard.button(text="new button", callback_data="new_button")

    await callback.message.edit_text(text="new_text", reply_markup=inline_keyboard.as_markup())


@main_router.callback_query(CFilter("two"))
async def handle_button_one(callback: CallbackQuery):
    inline_keyboard = InlineKeyboardBuilder()
    inline_keyboard.button(text="new two button", callback_data="new_button_2")

    await callback.message.edit_text(text="new_text", reply_markup=inline_keyboard.as_markup())


@main_router.callback_query(CFilter("new_button"))
@main_router.callback_query(CFilter("new_button_2"))
async def handle_button_one(callback: CallbackQuery):
    inline_keyboard = InlineKeyboardBuilder()
    inline_keyboard.button(text="button one", callback_data="one")
    inline_keyboard.button(text="button two", callback_data="two")

    await callback.message.edit_text(text="new_text", reply_markup=inline_keyboard.as_markup())


@main_router.message()
async def no_answer(message: Message) -> TelegramMethod[Message]:
    inline_keyboard = InlineKeyboardBuilder()
    inline_keyboard.button(text="button one", callback_data="one")
    inline_keyboard.button(text="button two", callback_data="two")

    return message.answer("Some text", reply_markup=inline_keyboard.as_markup())
