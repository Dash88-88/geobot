from aiogram import Dispatcher
from aiogram.utils.exceptions import ChatNotFound, BotBlocked, UserDeactivated
from config import BOT_ADMINS


async def send_message_to_admins(dp: Dispatcher, text: str):
    for chat_id in BOT_ADMINS:
        try:
            await dp.bot.send_message(chat_id, text)
        except (BotBlocked, ChatNotFound, UserDeactivated):
            pass


async def on_startup_notify(dp: Dispatcher):
    try:
        await send_message_to_admins(dp, 'Hello manager! The bot is enabled and it must be /START')
    except Exception as e:
        print(f"[WARNING] Can't notify admins: {e}")
