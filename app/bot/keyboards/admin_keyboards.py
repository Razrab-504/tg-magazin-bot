from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


admin_main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Админ Панель")],
    ],
    resize_keyboard=True
)


admin_comands = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📦 Список активных таоров")],
        [KeyboardButton(text="📦 Получить товар по id")],
        [KeyboardButton(text="📦 Создать товар")],
        [KeyboardButton(text="🔄 Обнавить статус заказа на товар")],
    ],
    resize_keyboard=True
)


def orders_inline_keyboard(orders):
    """
    orders: список объектов Order
    Возвращает InlineKeyboardMarkup, где каждая строка — кнопка "Подтвердить <order_id>"
    """
    buttons = []
    for o in orders:
        # текст кнопки: показать id и товар (можно любой формат)
        btn = InlineKeyboardButton(
            text=f"Подтвердить #{o.id}: {o.product.title}",
            callback_data=f"complete:{o.id}"
        )
        buttons.append([btn])  # каждая внутренняя группа — отдельный ряд
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
    
