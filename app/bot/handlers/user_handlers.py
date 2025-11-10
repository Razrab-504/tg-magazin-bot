from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from dotenv import find_dotenv, load_dotenv
import os

load_dotenv(find_dotenv())

from app.db.deps import get_db
from app.db import crud

from app.bot.keyboards.user_keyboards import user_main_menu, phone_keyboard, products_inline_keyboard
from app.bot.keyboards.admin_keyboards import admin_main_menu

from app.bot.filters.user_filter import IsUser


class OrderStates(StatesGroup):
    waiting_for_product_id = State()
    waiting_for_proof = State()


user_router = Router()
user_router.message.filter(IsUser())

ADMIN_ID = int(os.getenv("ADMIN_ID"))

@user_router.message(CommandStart())
async def start_cmd(message: Message):
    db = next(get_db())
    
    user = crud.get_or_create_user(
        db,
        tg_id=message.from_user.id,
        name=message.from_user.full_name,
    )
    
    if not user.phone:
        await message.answer("👋 Привет! Пожалуйста, поделитесь своим номером телефона.",
                    reply_markup=phone_keyboard)
    else:
        await message.answer("👋 Привет", reply_markup=user_main_menu)    


@user_router.message(F.content_type == "contact")
async def phone(message: Message):
    if not message.contact or message.contact.user_id != message.from_user.id:
        await message.answer("Пожалуйста, отправьте свой собственный контакт.")
        return
    
    db = next(get_db())
    user = crud.get_or_create_user(
        db,
        tg_id=message.from_user.id,
        name=message.from_user.full_name,
        phone=message.contact.phone_number
    )
    
    
    await message.answer("Спасибо! Ваш номер сохранен ✅", reply_markup=user_main_menu)


@user_router.message(F.text=="🛍 Shop")
async def product_cmd(message: Message, state: FSMContext):
    
    db = next(get_db())
    
    products = crud.list_active_products(db)
    if not products:
        await message.answer("В данный момент нет товаров.")
        return
        
    for p in products:
        caption = f"🆔 ID: {p.id}\n{p.title} - {p.price}₼\n{p.description or ''}\nБанковская карта:{p.bank_card}"
        keyboard = products_inline_keyboard([p])
        
        if p.file_id:
            await message.answer_photo(photo=p.file_id, caption=caption, reply_markup=keyboard)
        else:
            await message.answer(caption, reply_markup=keyboard)



@user_router.callback_query(F.data.startswith("order:"))
async def order_button_handler(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[1])

    db = next(get_db())
    product = crud.get_product(db, product_id)
    
    if not product or not product.active:
        await callback.message.answer(f"Товар с ID {product_id} не существует или не активен.")
        return

    await state.set_state(OrderStates.waiting_for_proof)
    await state.update_data(product_id=product_id)

    await callback.message.answer(
        f"Вы выбрали товар: {product.title}\n"
        f"Отправьте скрин оплаты (фото) для подтверждения заказа:"
    )

    await callback.answer()


@user_router.message(OrderStates.waiting_for_proof)
async def proof_order(message: Message, state: FSMContext):
    if message.content_type != "photo":
        await message.answer("Пожалуйста, отправьте фото скрина оплаты.")
        return

    photo_file_id = message.photo[-1].file_id
    data = await state.get_data()
    product_id = data.get('product_id')
    if not product_id:
        await message.answer("Товар не выбран. Попробуйте ещё раз.")
        await state.clear()
        return

    db = next(get_db())

    user = crud.get_or_create_user(
        db,
        tg_id=message.from_user.id,
        name=message.from_user.full_name
    )

    order = crud.create_order(db, user_id=user.id, product_id=product_id, proof=photo_file_id)

    await message.answer(f"✅ Заказ оформлен: {order.product.title}\nСтатус: {order.status}")
    await state.clear()


@user_router.message(F.text=="📦 My Purchases")
async def purchases_cmd(message: Message):

    db = next(get_db())
    
    purchases = crud.get_user_orders_by_tg(db, message.from_user.id)
    if message.text == "📦 My Purchases":
        if not purchases:
            await message.answer("Вы ничего не заказывали.")
            return

        else:
            text = "\n".join([f"{o.id}: {o.product.title} - {o.status}" for o in purchases])
            await message.answer(f"Вот ваши заказы:\n{text}")


@user_router.message(F.text=="❓ Help")
async def help_cmd(message: Message):
    await message.answer("Это интернет магазин где вы можете заказать/купить то что выставил админ")
    


