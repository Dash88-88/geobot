import logging
from asyncio import sleep
from html import escape as html_escape
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Command, Text
from aiogram.types import ContentType

from bot.filters import UserFilter
from bot.keyboards.callback_datas import (
    select_country_callback,
    manage_country_callback,
    toggle_country_callback,
    delete_country_callback,
    delete_country_approve_callback,
    delete_country_cancel_callback,
    change_user_country_callback,
    change_user_country_cancel_callback,
    set_user_country_callback,
    change_bonus_country_callback,
    change_bonus_country_cancel_callback,
    set_bonus_country_callback,
    update_country_name_callback,
    update_country_code_callback,
    update_country_channel_id_callback,
    update_country_channel_url_callback,
)
from bot.keyboards.default import main_menu_keyboard, manage_keyboard, cancel_keyboard
from bot.keyboards.inline import (
    select_country_keyboard,
    countries_admin_list_keyboard,
    country_admin_detail_keyboard,
    delete_country_confirmation_keyboard,
    change_user_country_keyboard,
    change_bonus_country_keyboard,
    message_inline_button_keyboard,
)
from bot.loader import dp, bot
from bot.states import (
    CreateNewCountry,
    UpdateCountryName,
    UpdateCountryCode,
    UpdateCountryChannelId,
    UpdateCountryChannelUrl,
    UpdateSiteID,
)
from common.constants import (
    DefaultKeyboardButtons,
    CallbackQueryTypes,
    DefaultInlineButtons,
)
from common.exceptions import (
    CountryAlreadyEnabledError,
    CountryAlreadyDisabledError,
    CountryAlreadyRemovedError,
)
from config import BONUS_TRANSFER_URL, REGISTRATION_URL
from logics import UserLogics, CountryLogics, BonusLogics
from models import Country


# ==================== USER COUNTRY SELECTION ====================

@dp.callback_query_handler(select_country_callback.filter())
async def process_select_country(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    country_id = callback_data.get("country_id")
    is_change = bool(int(callback_data.get("is_change", "0")))

    country = CountryLogics.get_by_id(country_id)
    if not country or not country.is_active or country.is_removed:
        await call.answer("This currency is no longer available. Please choose another one.", show_alert=True)
        active_countries = CountryLogics.get_list(is_active=True, is_removed=False)
        if active_countries:
            await call.message.edit_reply_markup(reply_markup=select_country_keyboard(active_countries, is_change=is_change))
        return

    user = UserLogics.get_by_chat_id(call.from_user.id)
    if not user:
        # Create user if not created yet
        from config import BOT_ADMINS
        user = UserLogics.create(
            chat_id=call.from_user.id,
            username=call.from_user.username,
            nickname=call.from_user.username or call.from_user.first_name or str(call.from_user.id),
            site_id='',
            is_manager=bool(call.from_user.id in BOT_ADMINS),
            country=country
        )
    else:
        UserLogics.set_country(user, country)

    await call.answer(f"Currency selected: {country.name} ✅")
    await call.message.delete()

    if is_change and user.site_id:
        await call.message.answer(
            f"💱 Your currency has been updated to <b>{country.name}</b>!",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    elif not user.site_id and not user.is_manager:
        await UpdateSiteID.send_site_id.set()
        reg_link = f"\n\nDon't have an account yet? Register <a href='{REGISTRATION_URL}'>HERE</a>" if REGISTRATION_URL else ""
        await call.message.answer(
            f"💱 Currency selected: <b>{country.name}</b>\n\n"
            f"🃏 <b>Please enter your Site ID / Nickname:</b>\n"
            f"<i>Without Site ID / Nickname, you will not be able to use the bot and request bonuses.</i>"
            f"{reg_link}",
            parse_mode="HTML"
        )
    else:
        # First start onboarding completion
        try:
            await call.message.answer_photo(
                photo='https://i.pinimg.com/736x/f9/32/f2/f932f20f8e4f42ccef38af270f323b08.jpg',
                caption="Start smart. Feel the edge from the very first move.\n\n",
                parse_mode="HTML",
                reply_markup=message_inline_button_keyboard(BONUS_TRANSFER_URL) if BONUS_TRANSFER_URL else None
            )
        except Exception as e:
            logging.warning(f"Could not send onboarding photo: {e}")

        await call.message.answer(
            f"Welcome, {call.from_user.first_name or 'friend'} 👋!\n"
            f"💱 Currency: <b>{country.name}</b>",
            reply_markup=main_menu_keyboard() if not user.is_manager else manage_keyboard(),
            parse_mode="HTML"
        )


@dp.callback_query_handler(text=CallbackQueryTypes.ChangeCountry.value, state="*")
async def process_user_request_change_country(call: types.CallbackQuery, state: FSMContext):
    if state:
        await state.finish()
    active_countries = CountryLogics.get_list(is_active=True, is_removed=False)
    if not active_countries:
        await call.answer("No active currencies available at the moment.", show_alert=True)
        return

    await call.message.answer(
        "💱 <b>Select your new currency:</b>",
        reply_markup=select_country_keyboard(active_countries, is_change=True),
        parse_mode="HTML"
    )
    await call.answer()


# ==================== ADMIN COUNTRY MANAGEMENT ====================

async def _send_country_card(chat_id: int, country_id: str):
    country = CountryLogics.get_by_id(country_id)
    if not country or country.is_removed:
        return

    user_count = UserLogics.count(country_id=country.id, is_active=True)
    status_text = "🟢 Active" if country.is_active else "🔴 Hidden / Inactive"

    safe_name = html_escape(country.name)
    safe_code = html_escape(country.code)
    safe_cid = html_escape(country.channel_id or 'Not configured')
    safe_url = html_escape(country.channel_url or 'Not configured')

    card_text = (
        f"💱 <b>Currency:</b> {safe_name}\n"
        f"🔤 <b>Code:</b> <code>{safe_code}</code>\n"
        f"📊 <b>Status:</b> {status_text}\n"
        f"👥 <b>Active Users:</b> {user_count}\n"
        f"📢 <b>Channel ID:</b> <code>{safe_cid}</code>\n"
        f"🔗 <b>Channel URL:</b> {safe_url}"
    )

    await bot.send_message(
        chat_id=chat_id,
        text=card_text,
        reply_markup=country_admin_detail_keyboard(country_id=country.id, is_active=country.is_active),
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@dp.message_handler(UserFilter(only_managers=True), Command(["currencies", "countries"]), state="*")
@dp.message_handler(UserFilter(only_managers=True), Text([DefaultKeyboardButtons.Countries.value, "💱 Currencies", "🌍 Countries"], ignore_case=True), state="*")
@dp.callback_query_handler(UserFilter(only_managers=True), text=CallbackQueryTypes.ManageCountries.value, state="*")
async def process_admin_countries_list(update: types.Message or types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.finish()

    countries = CountryLogics.get_list(is_removed=False)
    message = update.message if isinstance(update, types.CallbackQuery) else update

    if isinstance(update, types.CallbackQuery):
        await update.answer()

    if not countries:
        await message.answer(
            "💱 <b>Currencies Management</b>\n\nNo currencies found. Click below to add the first currency.",
            reply_markup=countries_admin_list_keyboard(countries),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"💱 <b>Currencies Management</b> (Total: {len(countries)}):\nSelect a currency to view/edit details or add a new one:",
            reply_markup=countries_admin_list_keyboard(countries),
            parse_mode="HTML"
        )


@dp.callback_query_handler(manage_country_callback.filter(), UserFilter(only_managers=True))
async def process_admin_view_country(call: types.CallbackQuery, callback_data: dict):
    country_id = callback_data.get("country_id")
    await call.answer()
    await _send_country_card(call.from_user.id, country_id)


@dp.callback_query_handler(toggle_country_callback.filter(), UserFilter(only_managers=True))
async def process_admin_toggle_country(call: types.CallbackQuery, callback_data: dict):
    country_id = callback_data.get("country_id")
    action = callback_data.get("action")
    country = CountryLogics.get_by_id(country_id)
    if not country:
        await call.answer("Currency not found.", show_alert=True)
        return

    try:
        if action == "enable":
            CountryLogics.enable(country)
            await call.answer("Currency enabled! 🟢", show_alert=True)
        else:
            CountryLogics.disable(country)
            await call.answer("Currency disabled! 🔴", show_alert=True)
    except (CountryAlreadyEnabledError, CountryAlreadyDisabledError):
        await call.answer("Status already set.", show_alert=True)

    await call.message.delete()
    await _send_country_card(call.from_user.id, country_id)


@dp.callback_query_handler(delete_country_callback.filter(), UserFilter(only_managers=True))
async def process_admin_delete_country_prompt(call: types.CallbackQuery, callback_data: dict):
    country_id = callback_data.get("country_id")
    country = CountryLogics.get_by_id(country_id)
    if not country:
        await call.answer("Currency not found.", show_alert=True)
        return

    await call.message.answer(
        f"⚠️ Are you sure you want to delete <b>{country.name}</b>?\n"
        f"Users with this currency will be prompted to choose a new currency on their next action.",
        reply_markup=delete_country_confirmation_keyboard(country_id=country_id),
        parse_mode="HTML"
    )
    await call.message.delete()


@dp.callback_query_handler(delete_country_cancel_callback.filter(), UserFilter(only_managers=True))
async def process_admin_delete_country_cancel(call: types.CallbackQuery, callback_data: dict):
    country_id = callback_data.get("country_id")
    await call.message.delete()
    await _send_country_card(call.from_user.id, country_id)


@dp.callback_query_handler(delete_country_approve_callback.filter(), UserFilter(only_managers=True))
async def process_admin_delete_country_approve(call: types.CallbackQuery, callback_data: dict):
    country_id = callback_data.get("country_id")
    country = CountryLogics.get_by_id(country_id)
    if country:
        try:
            CountryLogics.set_removed(country)
            await call.answer("Currency successfully deleted! 🗑️", show_alert=True)
        except CountryAlreadyRemovedError:
            pass

    await call.message.delete()
    # Return to countries list
    countries = CountryLogics.get_list(is_removed=False)
    await call.message.answer(
        f"💱 <b>Currencies Management</b> (Total: {len(countries)}):",
        reply_markup=countries_admin_list_keyboard(countries),
        parse_mode="HTML"
    )


# ==================== UPDATE COUNTRY FSM ====================

@dp.callback_query_handler(update_country_name_callback.filter(), UserFilter(only_managers=True))
async def process_admin_update_country_name_prompt(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    country_id = callback_data.get("country_id")
    country = CountryLogics.get_by_id(country_id)
    if not country or country.is_removed:
        await call.answer("Currency not found.", show_alert=True)
        return

    await state.update_data(country_id=country_id)
    await UpdateCountryName.send_country_name.set()
    await call.message.answer(
        f"✏️ <b>Update Currency Name</b>\n\n"
        f"Current name: <b>{country.name}</b>\n\n"
        f"Enter new currency name and emoji (e.g. <i>US Dollar 💵</i>):",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await call.message.delete()
    await call.answer()


@dp.message_handler(UserFilter(only_managers=True), state=UpdateCountryName.send_country_name, content_types=(ContentType.TEXT,))
async def process_admin_update_country_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 64:
        await message.answer("Currency name must be between 2 and 64 characters. Please try again:")
        return

    data = await state.get_data()
    country_id = data.get("country_id")
    await state.finish()

    country = CountryLogics.get_by_id(country_id)
    if not country or country.is_removed:
        await message.answer("Currency not found.", reply_markup=manage_keyboard())
        return

    CountryLogics.update(country, name=name)
    await message.answer(
        f"✅ Currency name successfully updated to <b>{country.name}</b>!",
        reply_markup=manage_keyboard(),
        parse_mode="HTML"
    )
    await sleep(0.5)
    await _send_country_card(message.from_user.id, country.id)


@dp.callback_query_handler(update_country_code_callback.filter(), UserFilter(only_managers=True))
async def process_admin_update_country_code_prompt(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    country_id = callback_data.get("country_id")
    country = CountryLogics.get_by_id(country_id)
    if not country or country.is_removed:
        await call.answer("Currency not found.", show_alert=True)
        return

    await state.update_data(country_id=country_id)
    await UpdateCountryCode.send_country_code.set()
    await call.message.answer(
        f"🔤 <b>Update Currency Code</b>\n\n"
        f"Current code: <code>{country.code}</code>\n\n"
        f"Enter new 2-8 letter currency code (e.g. <i>USD, EUR</i>):",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await call.message.delete()
    await call.answer()


@dp.message_handler(UserFilter(only_managers=True), state=UpdateCountryCode.send_country_code, content_types=(ContentType.TEXT,))
async def process_admin_update_country_code(message: types.Message, state: FSMContext):
    code = message.text.strip().upper()
    if len(code) < 2 or len(code) > 8:
        await message.answer("Currency code must be between 2 and 8 characters (e.g. USD, EUR). Try again:")
        return

    data = await state.get_data()
    country_id = data.get("country_id")

    country = CountryLogics.get_by_id(country_id)
    if not country or country.is_removed:
        await state.finish()
        await message.answer("Currency not found.", reply_markup=manage_keyboard())
        return

    existing = CountryLogics.get_by_code(code)
    if existing and str(existing.id) != str(country.id) and not existing.is_removed:
        await message.answer(f"A currency with code <b>{code}</b> already exists! Enter a different code:", parse_mode="HTML")
        return

    await state.finish()
    CountryLogics.update(country, code=code)
    await message.answer(
        f"✅ Currency code successfully updated to <code>{country.code}</code>!",
        reply_markup=manage_keyboard(),
        parse_mode="HTML"
    )
    await sleep(0.5)
    await _send_country_card(message.from_user.id, country.id)


@dp.callback_query_handler(update_country_channel_id_callback.filter(), UserFilter(only_managers=True))
async def process_admin_update_country_channel_id_prompt(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    country_id = callback_data.get("country_id")
    country = CountryLogics.get_by_id(country_id)
    if not country or country.is_removed:
        await call.answer("Currency not found.", show_alert=True)
        return

    await state.update_data(country_id=country_id)
    await UpdateCountryChannelId.send_channel_id.set()
    await call.message.answer(
        f"📢 <b>Update Channel ID</b>\n\n"
        f"Current Channel ID: <code>{country.channel_id or 'Not configured'}</code>\n\n"
        f"Enter new Telegram Channel ID or Username (e.g. <i>-1001234567890</i> or <i>@my_channel</i>):\n"
        f"<i>Send - to clear</i>\n\n"
        f"⚠️ <i>Ensure the bot is added as an administrator in this channel!</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await call.message.delete()
    await call.answer()


@dp.message_handler(UserFilter(only_managers=True), state=UpdateCountryChannelId.send_channel_id, content_types=(ContentType.TEXT,))
async def process_admin_update_country_channel_id(message: types.Message, state: FSMContext):
    channel_id = message.text.strip()
    if channel_id == "-":
        channel_id = ""

    data = await state.get_data()
    country_id = data.get("country_id")
    await state.finish()

    country = CountryLogics.get_by_id(country_id)
    if not country or country.is_removed:
        await message.answer("Currency not found.", reply_markup=manage_keyboard())
        return

    CountryLogics.update(country, channel_id=channel_id)
    await message.answer(
        f"✅ Channel ID successfully updated to <code>{country.channel_id or 'Not configured'}</code>!",
        reply_markup=manage_keyboard(),
        parse_mode="HTML"
    )
    await sleep(0.5)
    await _send_country_card(message.from_user.id, country.id)


@dp.callback_query_handler(update_country_channel_url_callback.filter(), UserFilter(only_managers=True))
async def process_admin_update_country_channel_url_prompt(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    country_id = callback_data.get("country_id")
    country = CountryLogics.get_by_id(country_id)
    if not country or country.is_removed:
        await call.answer("Currency not found.", show_alert=True)
        return

    await state.update_data(country_id=country_id)
    await UpdateCountryChannelUrl.send_channel_url.set()
    current_url_safe = html_escape(country.channel_url or 'Not configured')
    await call.message.answer(
        f"🔗 <b>Update Channel URL</b>\n\n"
        f"Current Channel URL: {current_url_safe}\n\n"
        f"Enter new public or invite URL to join the channel (e.g. <i>https://t.me/my_channel</i> or <i>https://t.me/+joinlink</i>):\n"
        f"<i>Send - to clear</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    await call.message.delete()
    await call.answer()


@dp.message_handler(UserFilter(only_managers=True), state=UpdateCountryChannelUrl.send_channel_url, content_types=(ContentType.TEXT,))
async def process_admin_update_country_channel_url(message: types.Message, state: FSMContext):
    channel_url = message.text.strip()
    if channel_url == "-":
        channel_url = ""

    data = await state.get_data()
    country_id = data.get("country_id")
    await state.finish()

    country = CountryLogics.get_by_id(country_id)
    if not country or country.is_removed:
        await message.answer("Currency not found.", reply_markup=manage_keyboard())
        return

    CountryLogics.update(country, channel_url=channel_url)
    updated_url_safe = html_escape(country.channel_url or 'Not configured')
    await message.answer(
        f"✅ Channel URL successfully updated to {updated_url_safe}!",
        reply_markup=manage_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    await sleep(0.5)
    await _send_country_card(message.from_user.id, country.id)


# ==================== CREATE COUNTRY FSM ====================

@dp.callback_query_handler(UserFilter(only_managers=True), text=CallbackQueryTypes.CreateCountry.value)
async def process_admin_create_country_start(call: types.CallbackQuery, state: FSMContext):

    await call.answer()
    await CreateNewCountry.send_country_name.set()
    await call.message.answer(
        "➕ <b>Create New Currency</b>\n\n"
        "<b>Step 1/4:</b> Enter currency name and emoji\n"
        "<i>Example: US Dollar 💵 or Euro 💶</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@dp.message_handler(UserFilter(only_managers=True), state=CreateNewCountry.send_country_name, content_types=(ContentType.TEXT,))
async def process_admin_create_country_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 64:
        await message.answer("Currency name must be between 2 and 64 characters. Please try again:")
        return

    await state.update_data(name=name)
    await CreateNewCountry.send_country_code.set()
    await message.answer(
        f"✅ Name set: <b>{name}</b>\n\n"
        "<b>Step 2/4:</b> Enter 2-5 letter currency code\n"
        "<i>Example: USD, EUR, TRY</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@dp.message_handler(UserFilter(only_managers=True), state=CreateNewCountry.send_country_code, content_types=(ContentType.TEXT,))
async def process_admin_create_country_code(message: types.Message, state: FSMContext):
    code = message.text.strip().upper()
    if len(code) < 2 or len(code) > 8:
        await message.answer("Currency code must be between 2 and 8 characters (e.g. USD, EUR). Try again:")
        return

    existing = CountryLogics.get_by_code(code)
    if existing and not existing.is_removed:
        await message.answer(f"A currency with code <b>{code}</b> already exists! Enter a different code:", parse_mode="HTML")
        return

    await state.update_data(code=code)
    await CreateNewCountry.send_channel_id.set()
    await message.answer(
        f"✅ Code set: <b>{code}</b>\n\n"
        "<b>Step 3/4:</b> Enter Telegram Channel ID or Username for subscription verification\n"
        "<i>Example: -1001234567890 or @my_currency_channel</i>\n\n"
        "⚠️ <i>Ensure the bot is added as an administrator in this channel!</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@dp.message_handler(UserFilter(only_managers=True), state=CreateNewCountry.send_channel_id, content_types=(ContentType.TEXT,))
async def process_admin_create_country_channel_id(message: types.Message, state: FSMContext):
    channel_id = message.text.strip()
    if channel_id == "-":
        channel_id = ""
    await state.update_data(channel_id=channel_id)
    await CreateNewCountry.send_channel_url.set()
    display_cid = html_escape(channel_id) if channel_id else "Skipped"
    await message.answer(
        f"✅ Channel ID set: <code>{display_cid}</code>\n\n"
        "<b>Step 4/4:</b> Enter public or invite URL to join the channel (or <code>-</code> to skip)\n"
        "<i>Example: https://t.me/my_currency_channel or t.me/+joinlink</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@dp.message_handler(UserFilter(only_managers=True), state=CreateNewCountry.send_channel_url, content_types=(ContentType.TEXT,))
async def process_admin_create_country_finish(message: types.Message, state: FSMContext):
    channel_url = message.text.strip()
    if channel_url == "-":
        channel_url = ""
    data = await state.get_data()
    await state.finish()

    name = data.get("name")
    code = data.get("code")
    channel_id = data.get("channel_id")

    country = CountryLogics.create(
        name=name,
        code=code,
        channel_id=channel_id,
        channel_url=channel_url,
        is_active=True
    )

    safe_name = html_escape(country.name)
    safe_code = html_escape(country.code)
    safe_cid = html_escape(country.channel_id or "Not configured")
    safe_url = html_escape(country.channel_url or "Not configured")

    await message.answer(
        f"🎉 <b>Currency successfully created!</b>\n\n"
        f"💱 <b>Name:</b> {safe_name}\n"
        f"🔤 <b>Code:</b> <code>{safe_code}</code>\n"
        f"📢 <b>Channel:</b> <code>{safe_cid}</code>\n"
        f"🔗 <b>URL:</b> {safe_url}",
        reply_markup=manage_keyboard(),
        parse_mode="HTML"
    )
    await sleep(0.5)
    await _send_country_card(message.from_user.id, country.id)


# ==================== ADMIN CHANGE USER COUNTRY ====================

@dp.callback_query_handler(change_user_country_callback.filter(), UserFilter(only_managers=True))
async def process_admin_change_user_country_prompt(call: types.CallbackQuery, callback_data: dict):
    opened_user_id = callback_data.get("opened_user_id")
    target_user = UserLogics.get_by_id(opened_user_id)
    if not target_user:
        await call.answer("User not found.", show_alert=True)
        return

    countries = CountryLogics.get_list(is_removed=False)
    if not countries:
        await call.answer("No currencies created yet. Create a currency first.", show_alert=True)
        return

    current_c_id = target_user.country.id if target_user.country else None
    await call.message.answer(
        f"Select new currency for user <code>{target_user.chat_id}</code>:",
        reply_markup=change_user_country_keyboard(opened_user_id=opened_user_id, countries=countries, current_country_id=current_c_id),
        parse_mode="HTML"
    )
    await call.message.delete()


@dp.callback_query_handler(change_user_country_cancel_callback.filter(), UserFilter(only_managers=True))
async def process_admin_change_user_country_cancel(call: types.CallbackQuery, callback_data: dict):
    opened_user_id = callback_data.get("opened_user_id")
    from bot.handlers.profile import _send_user_info
    await call.message.delete()
    await _send_user_info(call.message, opened_user_id)


@dp.callback_query_handler(set_user_country_callback.filter(), UserFilter(only_managers=True))
async def process_admin_set_user_country(call: types.CallbackQuery, callback_data: dict):
    opened_user_id = callback_data.get("opened_user_id")
    country_id = callback_data.get("country_id")

    target_user = UserLogics.get_by_id(opened_user_id)
    country = CountryLogics.get_by_id(country_id)

    if not target_user or not country:
        await call.answer("Target user or currency not found.", show_alert=True)
        return

    UserLogics.set_country(target_user, country)
    await call.answer(f"User currency set to {country.name} ✅", show_alert=True)

    from bot.handlers.profile import _send_user_info
    await call.message.delete()
    await _send_user_info(call.message, opened_user_id)


# ==================== ADMIN CHANGE BONUS COUNTRY ====================

@dp.callback_query_handler(change_bonus_country_callback.filter(), UserFilter(only_managers=True))
async def process_admin_change_bonus_country_prompt(call: types.CallbackQuery, callback_data: dict):
    bonus_id = callback_data.get("bonus_id")
    bonus = BonusLogics.get_by_id(bonus_id)
    if not bonus or bonus.is_removed:
        await call.answer("Bonus not found.", show_alert=True)
        return

    countries = CountryLogics.get_list(is_removed=False)
    current_c_id = bonus.country.id if bonus.country else None

    await call.message.answer(
        "Select target currency for this bonus (or All Currencies):",
        reply_markup=change_bonus_country_keyboard(bonus_id=bonus_id, countries=countries, current_country_id=current_c_id),
        parse_mode="HTML"
    )
    await call.message.delete()


@dp.callback_query_handler(change_bonus_country_cancel_callback.filter(), UserFilter(only_managers=True))
async def process_admin_change_bonus_country_cancel(call: types.CallbackQuery, callback_data: dict):
    bonus_id = callback_data.get("bonus_id")
    from bot.handlers.bonus import _send_bonus_info
    await call.message.delete()
    await _send_bonus_info(call.from_user.id, bonus_id)


@dp.callback_query_handler(set_bonus_country_callback.filter(), UserFilter(only_managers=True))
async def process_admin_set_bonus_country(call: types.CallbackQuery, callback_data: dict):
    bonus_id = callback_data.get("bonus_id")
    country_id = callback_data.get("country_id")

    bonus = BonusLogics.get_by_id(bonus_id)
    if not bonus or bonus.is_removed:
        await call.answer("Bonus not found.", show_alert=True)
        return

    if country_id == "all":
        BonusLogics.set_country(bonus, None)
        await call.answer("Bonus is now global for All Currencies 💱", show_alert=True)
    else:
        country = CountryLogics.get_by_id(country_id)
        if country:
            BonusLogics.set_country(bonus, country)
            await call.answer(f"Bonus set for {country.name} 💱", show_alert=True)

    from bot.handlers.bonus import _send_bonus_info
    await call.message.delete()
    await _send_bonus_info(call.from_user.id, bonus_id)
