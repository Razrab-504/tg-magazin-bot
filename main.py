import asyncio
from aiogram import Bot, Dispatcher
from dotenv import find_dotenv, load_dotenv
import os

from app.bot.handlers.user_handlers import user_router
from app.bot.handlers.admin_handlers import admin_router

load_dotenv(find_dotenv())

bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher()


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    dp.include_routers(user_router, admin_router)
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot Stoped!")
        
