from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Command, Text
from bot.keyboards.default import main_menu_keyboard, manage_keyboard
from bot.keyboards.inline import select_country_keyboard
from bot.loader import dp
from bot.states import UpdateSiteID
from common.constants import CallbackQueryTypes, DefaultKeyboardButtons
from config import REGISTRATION_URL
from logics import UserLogics, CountryLogics


@dp.message_handler(Command("cancel"), state="*")
@dp.message_handler(Text([DefaultKeyboardButtons.Cancel.value, "⬅️ Cancel", "‍⬅️ Cancel", "Cancel", "Отмена"], ignore_case=True), state="*")
@dp.callback_query_handler(text=CallbackQueryTypes.Cancel.value, state='*')
async def cancel_from_callback(update: types.Message or types.CallbackQuery, state: FSMContext):
    user_id = update.from_user.id
    user = UserLogics.get_by_chat_id(user_id)

    if user and not user.is_manager:
        has_valid_country = bool(user.country and user.country.is_active and not user.country.is_removed)
        if not has_valid_country:
            active_countries = CountryLogics.get_list(is_active=True, is_removed=False)
            if active_countries:
                target = update.message if isinstance(update, types.CallbackQuery) else update
                await target.answer(
                    "👋 Please select your country to continue:",
                    reply_markup=select_country_keyboard(active_countries, is_change=False)
                )
                if isinstance(update, types.CallbackQuery):
                    await update.answer()
                return

        if not user.site_id:
            await UpdateSiteID.send_site_id.set()
            reg_link = f"\n\nDon't have an account yet? Register <a href='{REGISTRATION_URL}'>HERE</a>" if REGISTRATION_URL else ""
            target = update.message if isinstance(update, types.CallbackQuery) else update
            await target.answer(
                f"⚠️ <b>Site ID / Nickname is required to continue.</b>\n"
                f"Please enter your Site ID or Nickname 👉{reg_link}",
                parse_mode="HTML"
            )
            if isinstance(update, types.CallbackQuery):
                await update.answer()
            return

    if state:
        await state.finish()

    if isinstance(update, types.Message):
        message = update
        keyboard = manage_keyboard() if user and user.is_manager else main_menu_keyboard()
        await message.answer("Action canceled.", reply_markup=keyboard)
    elif isinstance(update, types.CallbackQuery):
        keyboard = manage_keyboard() if user and user.is_manager else main_menu_keyboard()
        await update.message.answer("Action canceled.", reply_markup=keyboard)
        await update.message.delete()
        await update.answer()
