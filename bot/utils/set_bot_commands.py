from aiogram import types, Dispatcher
from aiogram.types import MenuButtonWebApp, WebAppInfo
from config import WEBAPP_URL


async def set_default_commands(dp: Dispatcher):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "START BOT"),
        types.BotCommand("m", "MANAGE")
    ])

    await dp.bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="🎮 PLAY",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )