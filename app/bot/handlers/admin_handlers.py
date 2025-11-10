from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from datetime import datetime
from aiogram.exceptions import TelegramBadRequest

from app.bot.keyboards.admin_keyboards import admin_main_menu, admin_comands, orders_inline_keyboard
from app.bot.filters.admin_filter import IsAdmin

from app.db.deps import get_db
from app.db import crud

from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())


class AdminStates(StatesGroup):
    waiting_for_product_id = State()
    
class CreateProduct(StatesGroup):
    title = State()
    description = State()
    price = State()
    file_id = State()
    active = State()
    bank_card = State()
    


admin_router = Router()
admin_router.message.filter(IsAdmin())


@admin_router.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer("👋 Привет Админ", reply_markup=admin_main_menu)
    

@admin_router.message(F.text=="Админ Панель")
async def admin_cmd(message: Message):
    await message.answer("Выберите что вас интересует:", reply_markup=admin_comands)
    

@admin_router.message(F.text=="📦 Список активных таоров")
async def products_list_cmd(message: Message):
    
    db = next(get_db())
    products = crud.list_active_products(db)
    
    if not products:
        await message.answer("Вы еще не создали товары")
    
    for p in products:
        caption = f"{p.id}: {p.title} - {p.price}₼\n{p.description or ''}\nБанковская карта:{p.bank_card}"
        if p.file_id:
            await message.answer_photo(photo=p.file_id, caption=caption)
        else:
            await message.answer(f"{caption}\n{os.getenv("NUMBER")}")
        
    
@admin_router.message(F.text=="📦 Получить товар по id")
async def product_by_id_cmd(message: Message, state: FSMContext):
    await message.answer("Отправьте id товара")
    await state.set_state(AdminStates.waiting_for_product_id)


@admin_router.message(AdminStates.waiting_for_product_id)
async def process_product_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, отправьте корректный числовой id.")
        return
    
    
    db = next(get_db())
    product_id = int(message.text)
    product = crud.get_product(db, product_id)
    
    if not product:
        await message.answer(f"Товара с id {product_id} не найдено.")
        return
    
    else:
        await message.answer(f"{product.id}: {product.title} - {product.price}₼\n{product.description}")
        
    
    await state.clear()
    
    

@admin_router.message(F.text=="📦 Создать товар")
async def create_product_cmd(message: Message, state: FSMContext):
    await message.answer("Отправьте название товара (title):")
    await state.set_state(CreateProduct.title)
    

@admin_router.message(CreateProduct.title)
async def product_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Отправьте описание товара или чтобы пропустить напишите /skip (description):")
    await state.set_state(CreateProduct.description)
    

@admin_router.message(CreateProduct.description)
async def product_description(message: Message, state: FSMContext):
    text = message.text
    if text.lower() == "/skip":
        await state.update_data(description=None)
    else:
        await state.update_data(description=text)
    
    await message.answer("Отправьте цену товара (price):")
    await state.set_state(CreateProduct.price)
    

@admin_router.message(CreateProduct.price)
async def product_price(message: Message, state: FSMContext):
    try:
        price = int(message.text)
    except ValueError:
        await message.answer("Введите число для цены!")
        return
    
    await state.update_data(price=price)
    await message.answer("Отправиьте фото товара или чтобы пропустить напишите /skip (file_id):")
    await state.set_state(CreateProduct.file_id)
    

@admin_router.message(CreateProduct.file_id)
async def product_photo(message: Message, state: FSMContext):
    if message.content_type == "photo":
        photo_file_id = message.photo[-1].file_id
        await state.update_data(file_id=photo_file_id)
    elif message.text.lower() == "/skip":
        await state.update_data(file_id=None)
    else:
        await message.answer("Отправьте фото или /skip, чтобы пропустить.")
        return

    await message.answer("Товар активен? (да/нет)")
    await state.set_state(CreateProduct.active)
    

@admin_router.message(CreateProduct.active)
async def product_active(message: Message, state: FSMContext):
    text = message.text.lower()
    
    if text in ["да", "yes"]:
        active = True  
    elif text in ["нет", "no"]:
        active = False
    else:
        await message.answer("Введите 'да' или 'нет'.")
        return
    
    await state.update_data(active=active)    
    await message.answer("Банковскую курту (bank card):")
    await state.set_state(CreateProduct.bank_card)


@admin_router.message(CreateProduct.bank_card)
async def product_bank_card(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите корректный номер банковской карты (только цифры)")
        return

    bank_card = message.text
    await state.update_data(bank_card=bank_card)
    
    db = next(get_db())
    data = await state.get_data()
    
    product = crud.create_product(
        db,
        title=data['title'],
        description=data['description'],
        price=data['price'],
        file_id=data['file_id'],
        active=data['active'],
        bank_card=data['bank_card']
    )

    report_text = (
        f"✅ Новый товар создан!\n\n"
        f"Название: {product.title}\n"
        f"Описание: {product.description or 'Нет описания'}\n"
        f"Цена: {product.price}₼\n"
        f"Банковская карта: {product.bank_card}\n"
        f"Активен: {'Да' if product.active else 'Нет'}"
    )

    await message.answer(report_text)
    await state.clear()


@admin_router.message(F.text=="🔄 Обнавить статус заказа на товар")
async def show_pending_orders(message: Message):
    db = next(get_db())
    
    pending_orders = crud.list_pending_orders(db)
    
    if not pending_orders:
        await message.answer("Нет заказов для обновления статуса.")
        return
    
    keyboard = orders_inline_keyboard(pending_orders)
    await message.answer("Выберите заказ, чтобы отметить его как выполненный:", reply_markup=keyboard)
    

@admin_router.callback_query(F.data.startswith("complete:"))
async def complete_order_callback(callback: CallbackQuery):
    try:
        order_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Неверный формат данных.", show_alert=True)
        return

    db = next(get_db())
    order = crud.get_order(db, order_id)
    if not order:
        await callback.message.answer(f"Заказ с ID {order_id} не найден.")
        await callback.answer()
        return

    order.status = "completed"
    db.commit()
    db.refresh(order)

    user_tg_id = getattr(order.user, "tg_id", None)
    if user_tg_id:
        try:
            await callback.bot.send_message(user_tg_id,
                f"✅ Ваш заказ #{order.id} на «{order.product.title}» подтверждён и завершён.")
        except TelegramBadRequest as e:
            await callback.message.answer(
                f"Не удалось уведомить пользователя (tg_id={user_tg_id}): {e}. "
                "Проверьте tg_id в базе или свяжитесь с пользователем вручную."
            )
        except Exception as e:
            await callback.message.answer(f"Ошибка при отправке уведомления пользователю: {e}")
    else:
        await callback.message.answer("У пользователя нет tg_id в базе — не удалось отправить уведомление.")

    order.product.active = False
    db.commit()
    await callback.message.answer(f"✅ Статус заказа #{order.id} обновлён на 'completed'.")
    await callback.answer()
    

