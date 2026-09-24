import logging
from asyncio import sleep
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.types import ChatActions, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from bot.loader import dp, bot
from bot.keyboards.default import main_menu_keyboard, manage_keyboard
from bot.keyboards.inline import message_inline_button_keyboard, select_country_keyboard
from bot.states import UpdateSiteID
from common.constants import BuiltInReferralSources, DefaultInlineButtons
from config import BOT_ADMINS, BONUS_TRANSFER_URL, REGISTRATION_URL
from logics import UserLogics, CountryLogics
from html import escape as html_escape


@dp.message_handler(CommandStart(), state="*")
async def process_start(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()

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
    country = UserLogics.get_safe_country(user)
    has_valid_country = bool(country and country.is_active and not country.is_removed)

    if not has_valid_country:
        active_countries = CountryLogics.get_list(is_active=True, is_removed=False)
        if active_countries:
            await message.answer(
                "👋 <b>Welcome!</b>\n\nPlease select your currency to continue:",
                reply_markup=select_country_keyboard(active_countries, is_change=False),
                parse_mode="HTML"
            )
            return
        else:
            if user.is_manager:
                await message.answer(
                    "⚠️ <b>No currencies created yet.</b>\n"
                    "Please use /m and go to <b>💱 Currencies</b> to create the first currency.",
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    "👋 <b>Welcome!</b>\n\nSystem setup is in progress. Please check back shortly.",
                    parse_mode="HTML"
                )
            return

    # Check site_id requirement for non-managers
    if not user.site_id and not user.is_manager:
        await UpdateSiteID.send_site_id.set()
        reg_link = f"\n\nDon't have an account yet? Register <a href='{REGISTRATION_URL}'>HERE</a>" if REGISTRATION_URL else ""
        await message.answer(
            f"💱 Currency: <b>{country.name}</b>\n\n"
            f"🃏 <b>Please enter your Site ID / Nickname:</b>\n"
            f"<i>Without Site ID / Nickname, you will not be able to use the bot and request bonuses.</i>"
            f"{reg_link}",
            parse_mode="HTML"
        )
        return

    # User already has valid country and site_id
    reply_markup = None
    if BONUS_TRANSFER_URL:
        reply_markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton(
                text=DefaultInlineButtons.LearMore.value,
                web_app=WebAppInfo(url=BONUS_TRANSFER_URL)
            )
        )

    try:
        await message.answer_photo(
            photo='https://broomfieldcafeandbar.co.uk/assets/images/hero-c1cd07c4e9e1.webp',
            caption="🔥 Get Started for Just £20!\n\n🔥Make your 1st Deposit starting at £20 to unlock:\n\n🎁 150% Bonus up to £750\n🎰 100 Free Spins\n\nEnjoy your rewards instantly on your first £20 deposit!\n\n",
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.warning(f"Could not send start photo: {e}")

    welcome_name = html_escape(user.nickname or user.username or 'friend')
    await message.answer(
        text=f"Welcome back, {welcome_name} 👋!\n🌍 Country: <b>{country.name}</b>",
        reply_markup=main_menu_keyboard(is_manager=bool(user and user.is_manager)),
        parse_mode="HTML"
    )

    await message.answer_chat_action(ChatActions.TYPING)
    await sleep(0.2)
