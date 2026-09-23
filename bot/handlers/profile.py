import logging
from asyncio import sleep
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Command, Text
from aiogram.types import ContentType, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.filters import UserFilter
from bot.keyboards.callback_datas import (
    open_user_callback,
    user_group_display_dict,
    set_user_negative_callback,
    set_user_positive_callback,
    set_user_neutral_callback,
    set_user_vip_callback,
    set_user_all_callback,
    block_user_callback,
    unblock_user_callback,
    open_users_per_group_callback,
    group_display_dict,
    users_page_callback,
    block_user_approve_callback,
    block_user_cancel_callback,
    unblock_user_approve_callback,
    unblock_user_cancel_callback,
    change_user_group_cancel_callback,
    change_user_group_callback,
)
from bot.keyboards.default import cancel_keyboard, main_menu_keyboard, manage_keyboard
from bot.keyboards.inline import (
    profile_keyboard,
    user_keyboard,
    open_users_per_group_keyboard,
    users_navigation_keyboard,
    block_user_confirmation_keyboard,
    unblock_user_confirmation_keyboard,
    change_user_group_keyboard,
)
from bot.loader import dp, bot
from bot.states import UpdateSiteID, ViewUser
from common.constants import DefaultKeyboardButtons, CallbackQueryTypes, DefaultInlineButtons, Groups
from common.exceptions import (
    UserAlreadyBlockedError,
    UserAlreadyUnblockedError,
    UserAlreadyAllError,
    UserAlreadyNegativeError,
    UserAlreadyNeutralError,
    UserAlreadyPositiveError,
    UserAlreadyVipError,
)
from config import COMMUNITY_URL, REGISTRATION_URL, USERS_PER_PAGE, BONUS_TRANSFER_URL, BOT_ADMINS
from logics import UserLogics
from models import User
from html import escape as html_escape


async def _send_user_info(message: types.Message, user_id: str):
    user = UserLogics.get_by_id(user_id)
    if not user:
        return

    user_subscribed = await UserLogics.is_subscriber(bot=bot, chat_id=user.chat_id, user=user)
    site_id_text = html_escape(user.site_id) if user.site_id else "📛 No Site ID / Nickname!"
    referrals_count = len(UserLogics.get_referral_users_list(user.id))
    source = user.referral_source

    if user.referral_user_id:
        ref_user = UserLogics.get_by_id(user.referral_user_id)
        if ref_user:
            source = str(ref_user.chat_id)

    country = UserLogics.get_safe_country(user)
    country_name = country.name if country else "None (Global)"
    user_display = html_escape(user.username if user.username else (user.nickname or str(user.chat_id)))

    await message.answer(
        f"<pre>{user.chat_id}</pre>\n"
        f"🔗: {user_display}, 🃏: <b>{site_id_text}</b>\n"
        f"💱: <b>{country_name}</b>\n"
        f"📣: <b>{'✅ Subscribed' if user_subscribed else '📛 Not subscribed!'}</b>\n"
        f"⚖️: <b>Referrals:</b> {referrals_count}\n"
        f"📤: <b>Source:</b> \n<pre>{source}</pre>\n"
        f"⛓️‍: <b>{'Blocked' if user.is_blocked else 'Not blocked'}</b>, "
        f"{'👮‍, ' if user.is_manager else ''}Group: {user_group_display_dict.get(user.group)[0]}",
        disable_web_page_preview=True,
        parse_mode="HTML",
        reply_markup=user_keyboard(
            opened_user_id=user_id,
            is_opened_user_blocked=user.is_blocked,
            current_group=user.group
        )
    )


@dp.callback_query_handler(open_user_callback.filter(), UserFilter(only_managers=True))
async def process_open_user_callback(call: types.CallbackQuery, callback_data: dict):
    user_id = callback_data.get('user_id')
    await _send_user_info(call.message, user_id)
    await call.answer()


async def send_users_page(message=None, call=None, group=None, page=1):
    users, total = get_paginated_users(group, page)
    target = call.message if call else message

    if not users:
        await target.answer(f"No users found for group: {group_display_dict.get(group)[0]} {group}")
        return

    for user in users:
        await _send_user_info(target, user.id)
        await sleep(0.2)

    page_text = f"Users in {group_display_dict.get(group)[0]} → Page {page} / {(total + USERS_PER_PAGE - 1) // USERS_PER_PAGE}"
    keyboard = users_navigation_keyboard(group=group, page=page, total=total)

    if call:
        try:
            await call.message.edit_text(page_text, reply_markup=keyboard)
        except Exception:
            await call.message.answer(page_text, reply_markup=keyboard)
    else:
        await message.answer(page_text, reply_markup=keyboard)


def get_paginated_users(group, page: int):
    all_users = UserLogics.get_group_list(group)
    total = len(all_users)
    start = (page - 1) * USERS_PER_PAGE
    end = start + USERS_PER_PAGE
    return all_users[start:end], total


@dp.message_handler(Text([DefaultKeyboardButtons.ViewUsersPerGroup.value, "🔍 👥 🟧"]), UserFilter(only_managers=True), state="*")
async def process_view_users_by_group(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()
    await message.answer("Select user group to view first 👉:", reply_markup=open_users_per_group_keyboard())


@dp.callback_query_handler(open_users_per_group_callback.filter(), UserFilter(only_managers=True), state="*")
async def confirm_view_users_by_group(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    group = callback_data.get('group')
    await send_users_page(message=call.message, group=group, page=1)
    await call.answer()


@dp.callback_query_handler(users_page_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_users_pagination(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    group = callback_data["group"]
    page = int(callback_data["page"])
    await send_users_page(call=call, group=group, page=page)
    await call.answer()


@dp.message_handler(Text([DefaultKeyboardButtons.ViewUser.value, "🔍 👤"]), UserFilter(only_managers=True), state="*")
async def process_view_user_by_id(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()
    await ViewUser.send_chat_id.set()
    await message.answer("Enter user Chat ID, Username (@username) or Site ID / Nickname to view 👉:", reply_markup=cancel_keyboard())


@dp.message_handler(UserFilter(only_managers=True), state=ViewUser.send_chat_id, content_types=(ContentType.ANY,))
async def confirm_view_entered_user(message: types.Message, state: FSMContext):
    user_to_view = (message.text or "").strip()
    await state.finish()

    if not user_to_view or len(user_to_view) > 100:
        await message.answer('Wrong user search input 🚨', reply_markup=manage_keyboard())
        return

    user = UserLogics.find_user(user_to_view)
    if not user:
        await message.answer(text="The user is not found 🚨", reply_markup=manage_keyboard())
        return

    await message.answer(text="The user is found ✅", reply_markup=manage_keyboard())
    await _send_user_info(message=message, user_id=user.id)


@dp.callback_query_handler(block_user_callback.filter(), UserFilter(only_managers=True))
async def process_block_user(call: types.CallbackQuery, callback_data: dict):
    opened_user_id = callback_data.get('opened_user_id')
    await call.message.answer("Are you sure you want to block the user? 👉",
                              reply_markup=block_user_confirmation_keyboard(opened_user_id=opened_user_id))


@dp.callback_query_handler(block_user_approve_callback.filter(), UserFilter(only_managers=True))
async def process_block_user_approve(call: types.CallbackQuery, callback_data: dict):
    opened_user_id = callback_data.get('opened_user_id')
    opened_user = UserLogics.get_by_id(opened_user_id)
    if not opened_user:
        await call.message.answer("User not found", reply_markup=manage_keyboard())
        return

    try:
        UserLogics.block(opened_user)
        await call.message.answer('The user has been blocked 😈', reply_markup=manage_keyboard())
    except UserAlreadyBlockedError:
        await call.message.answer("Ups, the user is already blocked 🤭", reply_markup=manage_keyboard())

    await call.message.delete()
    await _send_user_info(call.message, opened_user_id)


@dp.callback_query_handler(block_user_cancel_callback.filter(), UserFilter(only_managers=True))
async def process_block_user_cancel(call: types.CallbackQuery, callback_data: dict):
    opened_user_id = callback_data.get('opened_user_id')
    await call.message.answer("Huh, the user was not blocked 😌", reply_markup=manage_keyboard())
    await call.message.delete()
    await _send_user_info(call.message, opened_user_id)


@dp.callback_query_handler(unblock_user_callback.filter(), UserFilter(only_managers=True))
async def process_unblock_user(call: types.CallbackQuery, callback_data: dict):
    opened_user_id = callback_data.get('opened_user_id')
    await call.message.answer("Are you sure you want to unblock the user? 👉",
                              reply_markup=unblock_user_confirmation_keyboard(opened_user_id=opened_user_id))
    await call.message.delete()


@dp.callback_query_handler(unblock_user_approve_callback.filter(), UserFilter(only_managers=True))
async def process_unblock_user_approve(call: types.CallbackQuery, callback_data: dict):
    opened_user_id = callback_data.get('opened_user_id')
    opened_user = UserLogics.get_by_id(opened_user_id)
    if not opened_user:
        await call.message.answer("User not found", reply_markup=manage_keyboard())
        return

    try:
        UserLogics.unblock(opened_user)
        await call.message.answer('The user has been unblocked 👼', reply_markup=manage_keyboard())
    except UserAlreadyUnblockedError:
        await call.message.answer("Ups, the user is already unblocked 🤭", reply_markup=manage_keyboard())

    await call.message.delete()
    await _send_user_info(call.message, opened_user_id)


@dp.callback_query_handler(unblock_user_cancel_callback.filter(), UserFilter(only_managers=True))
async def process_unblock_user_cancel(call: types.CallbackQuery, callback_data: dict):
    opened_user_id = callback_data.get('opened_user_id')
    await call.message.answer("Huh, the user was not unblocked 😌", reply_markup=manage_keyboard())
    await call.message.delete()
    await _send_user_info(call.message, opened_user_id)


@dp.callback_query_handler(change_user_group_callback.filter(), UserFilter(only_managers=True))
async def process_change_user_group_callback(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    opened_user_id = callback_data.get('opened_user_id')
    user = UserLogics.get_by_id(opened_user_id)
    if not user:
        await call.message.answer("User not found", reply_markup=manage_keyboard())
        return

    await state.update_data(opened_user_id=opened_user_id)
    await call.message.answer(
        "Select new group for the user:",
        reply_markup=change_user_group_keyboard(opened_user_id=opened_user_id, current_group=user.group)
    )
    await call.message.delete()


@dp.callback_query_handler(change_user_group_cancel_callback.filter(), UserFilter(only_managers=True))
async def process_change_user_group_cancel_callback(call: types.CallbackQuery, callback_data: dict):
    opened_user_id = callback_data.get('opened_user_id')
    await call.message.answer("Huh, the user group was not changed 😌", reply_markup=manage_keyboard())
    await call.message.delete()
    await _send_user_info(call.message, opened_user_id)


@dp.callback_query_handler(set_user_all_callback.filter(), UserFilter(only_managers=True))
async def process_set_user_all(call: types.CallbackQuery, callback_data: dict):
    opened_user_id = callback_data.get('opened_user_id')
    opened_user = UserLogics.get_by_id(opened_user_id)
    if not opened_user:
        await call.message.answer("User not found", reply_markup=manage_keyboard())
        return

    try:
        UserLogics.set_group_all(opened_user)
        await call.answer(f'The user has been set to {DefaultInlineButtons.AllBonus.value} {Groups.All.value} group!', show_alert=True)
    except UserAlreadyAllError:
        await call.answer(f"Ups, the user group is already {DefaultInlineButtons.AllBonus.value} {Groups.All.value} 🤭", show_alert=True)

    await call.message.delete()
    await _send_user_info(call.message, opened_user_id)


@dp.callback_query_handler(set_user_vip_callback.filter(), UserFilter(only_managers=True))
async def process_set_user_vip(call: types.CallbackQuery, callback_data: dict):
    opened_user_id = callback_data.get('opened_user_id')
    opened_user = UserLogics.get_by_id(opened_user_id)
    if not opened_user:
        await call.message.answer("User not found", reply_markup=manage_keyboard())
        return

    try:
        UserLogics.set_group_vip(opened_user)
        await call.answer(f'The user has been set to {DefaultInlineButtons.VIPBonus.value} {Groups.Vip.value} group!', show_alert=True)
    except UserAlreadyVipError:
        await call.answer(f"Ups, the user group is already {DefaultInlineButtons.VIPBonus.value} {Groups.Vip.value} 🤭", show_alert=True)

    await call.message.delete()
    await _send_user_info(call.message, opened_user_id)


@dp.callback_query_handler(set_user_positive_callback.filter(), UserFilter(only_managers=True))
async def process_set_user_positive(call: types.CallbackQuery, callback_data: dict):
    opened_user_id = callback_data.get('opened_user_id')
    opened_user = UserLogics.get_by_id(opened_user_id)
    if not opened_user:
        await call.message.answer("User not found", reply_markup=manage_keyboard())
        return

    try:
        UserLogics.set_group_positive(opened_user)
        await call.answer(f'The user has been set to {DefaultInlineButtons.PositiveBonus.value} {Groups.Positive.value} group!', show_alert=True)
    except UserAlreadyPositiveError:
        await call.answer(f"Ups, the user group is already {DefaultInlineButtons.PositiveBonus.value} {Groups.Positive.value} 🤭", show_alert=True)

    await call.message.delete()
    await _send_user_info(call.message, opened_user_id)


@dp.callback_query_handler(set_user_neutral_callback.filter(), UserFilter(only_managers=True))
async def process_set_user_neutral(call: types.CallbackQuery, callback_data: dict):
    opened_user_id = callback_data.get('opened_user_id')
    opened_user = UserLogics.get_by_id(opened_user_id)
    if not opened_user:
        await call.message.answer("User not found", reply_markup=manage_keyboard())
        return

    try:
        UserLogics.set_group_neutral(opened_user)
        await call.answer(f'The user has been set to {DefaultInlineButtons.NeutralBonus.value} {Groups.Neutral.value} group!', show_alert=True)
    except UserAlreadyNeutralError:
        await call.answer(f"Ups, the user group is already {DefaultInlineButtons.NeutralBonus.value} {Groups.Neutral.value} 🤭", show_alert=True)

    await call.message.delete()
    await _send_user_info(call.message, opened_user_id)


@dp.callback_query_handler(set_user_negative_callback.filter(), UserFilter(only_managers=True))
async def process_set_user_negative(call: types.CallbackQuery, callback_data: dict):
    opened_user_id = callback_data.get('opened_user_id')
    opened_user = UserLogics.get_by_id(opened_user_id)
    if not opened_user:
        await call.message.answer("User not found", reply_markup=manage_keyboard())
        return

    try:
        UserLogics.set_group_negative(opened_user)
        await call.answer(f'The user has been set to {DefaultInlineButtons.NegativeBonus.value} {Groups.Negative.value} group!', show_alert=True)
    except UserAlreadyNegativeError:
        await call.answer(f"Ups, the user group is already {DefaultInlineButtons.NegativeBonus.value} {Groups.Negative.value} 🤭", show_alert=True)

    await call.message.delete()
    await _send_user_info(call.message, opened_user_id)


@dp.message_handler(Command(["profile"]), UserFilter(), state="*")
@dp.message_handler(
    Text([
        DefaultKeyboardButtons.Profile.value,
        "🤴🏻 Profile",
        "🤴 Profile",
        "Profile"
    ], ignore_case=True),
    UserFilter(),
    state="*"
)
async def process_open_profile(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()
    user = UserLogics.get_by_chat_id(message.from_user.id)
    if not user:
        user = UserLogics.create(
            chat_id=message.from_user.id,
            username=message.from_user.username,
            nickname=message.from_user.username or message.from_user.first_name or str(message.from_user.id),
            site_id='',
            is_manager=bool(message.from_user.id in BOT_ADMINS)
        )

    user_subscribed = await UserLogics.is_subscriber(bot=bot, chat_id=message.from_user.id, user=user)

    country = UserLogics.get_safe_country(user)
    channel_url = (country.channel_url if country and country.channel_url else COMMUNITY_URL) or "https://t.me"
    channel_str_link = f"<a href='{channel_url}'>Channel</a>"
    country_name = country.name if country else "Not selected"
    site_id_text = html_escape(user.site_id) if user.site_id else "📛 Not specified"
    display_name = html_escape(user.nickname or user.username or "User")

    await message.answer(
        f"🌟 <b>Profile:</b> {display_name}\n"
        f"💱 <b>Currency:</b> {country_name}\n"
        f"🃏 <b>Site ID / Nickname:</b> {site_id_text}\n"
        f"📣 <b>Status:</b> {'✅ Subscribed' if user_subscribed else f'📛 Please subscribe to our {channel_str_link}'}",
        disable_web_page_preview=True,
        parse_mode="HTML",
        reply_markup=profile_keyboard()
    )


@dp.callback_query_handler(text=CallbackQueryTypes.UpdateSiteID.value, state="*")
async def process_user_request_update_site_id(call: types.CallbackQuery, state: FSMContext):
    if state:
        await state.finish()
    await UpdateSiteID.send_site_id.set()
    await call.message.answer(
        "Enter your <b>Site ID</b> or <b>Nickname</b> on the platform 👉:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


@dp.message_handler(state=UpdateSiteID.send_site_id, content_types=(ContentType.TEXT,))
async def process_confirm_update_site_id(message: types.Message, state: FSMContext):
    site_id = message.text.strip()

    # Guard against capturing menu buttons as Site ID
    menu_buttons = [b.value for b in DefaultKeyboardButtons]
    if site_id in menu_buttons or site_id.lower() in [
        "/cancel", "cancel",
        "/profile", "profile",
        "/bonuses", "bonuses",
        "/invite", "invite"
    ]:
        await state.finish()
        if any(c in site_id.lower() for c in ["cancel"]):
            user = UserLogics.get_by_chat_id(message.from_user.id)
            keyboard = manage_keyboard() if user and user.is_manager else main_menu_keyboard()
            await message.answer("Action canceled.", reply_markup=keyboard)
            return
        if any(p in site_id.lower() for p in ["profile", "🤴"]):
            await process_open_profile(message, state)
            return
        user = UserLogics.get_by_chat_id(message.from_user.id)
        keyboard = manage_keyboard() if user and user.is_manager else main_menu_keyboard()
        await message.answer("Site ID update was canceled.", reply_markup=keyboard)
        return

    if not site_id or len(site_id) > 100 or '\n' in site_id:
        await message.answer(
            "⚠️ Invalid input. Please enter a valid Site ID or Nickname (single line, up to 100 characters):",
            reply_markup=cancel_keyboard()
        )
        return

    user = UserLogics.get_by_chat_id(message.from_user.id)
    is_new_registration = False
    if user:
        if not user.site_id:
            is_new_registration = True
        UserLogics.set_site_id(user, site_id)

    await state.finish()

    if is_new_registration and not (user and user.is_manager):
        # Onboarding complete for new user
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
                photo='https://i.pinimg.com/736x/f9/32/f2/f932f20f8e4f42ccef38af270f323b08.jpg',
                caption="Start smart. Feel the edge from the very first move.\n\n",
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        except Exception as e:
            logging.warning(f"Could not send onboarding photo: {e}")

        country = UserLogics.get_safe_country(user)
        country_name = country.name if country else "Unknown"
        await message.answer(
            f"✅ <b>Registration complete!</b>\n"
            f"🌍 Country: <b>{country_name}</b>\n"
            f"🃏 Site ID / Nickname: <b>{html_escape(site_id)}</b>\n\n"
            f"Welcome, {html_escape(message.from_user.first_name or (user.nickname if user else '') or 'friend')} 👋!",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"✅ Your Site ID / Nickname has been updated to: <b>{html_escape(site_id)}</b>",
            reply_markup=main_menu_keyboard() if not (user and user.is_manager) else manage_keyboard(),
            parse_mode="HTML"
        )


@dp.message_handler(state=UpdateSiteID.send_site_id, content_types=ContentType.ANY)
async def process_invalid_type_update_site_id(message: types.Message):
    await message.answer("Please send text with your Site ID or Nickname 👉:", reply_markup=cancel_keyboard())

