from asyncio import sleep
from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.types import ChatActions, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from bot.loader import dp, bot
from bot.keyboards.default import main_menu_keyboard
from bot.keyboards.inline import message_inline_button_keyboard, select_country_keyboard
from common.constants import BuiltInReferralSources, DefaultInlineButtons
from config import BOT_ADMINS, BONUS_TRANSFER_URL
from logics import UserLogics, CountryLogics


@dp.message_handler(CommandStart())
async def process_start(message: types.Message):
    user = UserLogics.get_by_chat_id(message.from_user.id)
    if not user:
        referral_source = referral_user_id = None
        if arg := message.get_args():
            referral = UserLogics.get_by_id(arg.strip())
            if referral:
                referral_source = BuiltInReferralSources.User.value
                referral_user_id = referral.id
            else:
                referral_source = arg

        user = UserLogics.create(
            chat_id=message.from_user.id,
            username=message.from_user.username,
            nickname=message.from_user.username or message.from_user.first_name or str(message.from_user.id),
            site_id='',
            referral_source=referral_source,
            referral_user_id=referral_user_id,
            is_manager=bool(message.from_user.id in BOT_ADMINS)
        )

    # Check country requirement
    has_valid_country = bool(user.country and user.country.is_active and not user.country.is_removed)

    if not has_valid_country:
        active_countries = CountryLogics.get_list(is_active=True, is_removed=False)
        if active_countries:
            await message.answer(
                "👋 <b>Welcome!</b>\n\nPlease select your country to continue:",
                reply_markup=select_country_keyboard(active_countries, is_change=False),
                parse_mode="HTML"
            )
            return
        else:
            if user.is_manager:
                await message.answer(
                    "⚠️ <b>No countries created yet.</b>\n"
                    "Please use /m and go to <b>🌍 Countries</b> to create the first country.",
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    "👋 <b>Welcome!</b>\n\nSystem setup is in progress. Please check back shortly.",
                    parse_mode="HTML"
                )
            return

    # User already has valid country
    reply_markup = None
    if BONUS_TRANSFER_URL:
        reply_markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton(
                text=DefaultInlineButtons.LearMore.value,
                web_app=WebAppInfo(url=BONUS_TRANSFER_URL)
            )
        )

    await message.answer_photo(
        photo='https://i.pinimg.com/736x/f9/32/f2/f932f20f8e4f42ccef38af270f323b08.jpg',
        caption="Start smart. Feel the edge from the very first move.\n\n",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

    await message.answer(
        text=f"Welcome back, {user.nickname or 'friend'} 👋!\n🌍 Country: <b>{user.country.name}</b>",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )

    await message.answer_chat_action(ChatActions.TYPING)
    await sleep(0.2)
