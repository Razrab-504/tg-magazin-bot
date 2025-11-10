from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

user_main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍 Shop")],
        [KeyboardButton(text="📦 My Purchases")],
        [KeyboardButton(text="❓ Help")],
    ],
    resize_keyboard=True
)

phone_button = KeyboardButton(text="📞 Поделиться номером", request_contact=True)

phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[[phone_button]],
    resize_keyboard=True,
    one_time_keyboard=True
)


def products_inline_keyboard(products: list) -> InlineKeyboardMarkup:

    buttons = [
        [InlineKeyboardButton(text=f"Заказать '{p.title}' 🛒", callback_data=f"order:{p.id}")]
        for p in products
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
