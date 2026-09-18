from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Command, Text
from bot.filters import UserFilter
from bot.keyboards.inline import community_keyboard
from bot.loader import dp
from common.constants import DefaultKeyboardButtons
from config import COMMUNITY_URL
from logics import UserLogics


@dp.message_handler(Command(["community", "channel"]), UserFilter(), state="*")
@dp.message_handler(
    Text([
        DefaultKeyboardButtons.Community.value,
        "💬 Our Channel",
        "Our Channel",
        "Channel"
    ], ignore_case=True),
    UserFilter(),
    state="*"
)
async def community(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()
    user = UserLogics.get_by_chat_id(message.from_user.id)
    country = UserLogics.get_safe_country(user)
    channel_url = (country.channel_url if country and country.channel_url else COMMUNITY_URL) or "https://t.me"

    await message.answer(
        "Results, promos, news, and more — all in our official channel!",
        reply_markup=community_keyboard(channel_url)
    )
