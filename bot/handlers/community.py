from aiogram import types
from aiogram.dispatcher.filters import Text
from bot.keyboards.inline import community_keyboard
from bot.loader import dp
from common.constants import DefaultKeyboardButtons
from config import COMMUNITY_URL
from logics import UserLogics


@dp.message_handler(Text(DefaultKeyboardButtons.Community.value))
async def community(message: types.Message):
    user = UserLogics.get_by_chat_id(message.from_user.id)
    channel_url = (user.country.channel_url if user and user.country and user.country.channel_url else COMMUNITY_URL) or "https://t.me"

    await message.answer(
        "Results, promos, news, and more — all in our official channel!",
        reply_markup=community_keyboard(channel_url)
    )
