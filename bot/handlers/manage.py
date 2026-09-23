import re
import html
import logging
from datetime import datetime, timedelta
from asyncio import sleep, gather

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Command, Text
from aiogram.types import ContentType
from aiogram.utils.exceptions import ChatNotFound, BotBlocked, UserDeactivated

from bot.filters import UserFilter
from bot.handlers.bonus import _send_bonus_info
from bot.handlers.bonus_request import _send_bonus_request_info
from bot.handlers.profile import _send_user_info
from bot.keyboards.callback_datas import (
    message_user_callback,
    send_bonus_to_user_callback,
    send_bonus_to_group_callback,
    send_message_to_group_callback,
    group_display_dict,
    all_bonus_requests_page_callback,
    user_group_display_dict,
    send_bonus_2_group_approve_callback,
    send_bonus_2_group_cancel_callback,
    bonus_request_status_filter_callback,
    open_bonus_request_status_filter_callback,
    approve_personal_message_callback,
    cancel_personal_message_callback,
    approve_group_message_callback,
    cancel_group_message_callback,
    cancel_all_message_callback,
    approve_all_message_callback,
    approve_by_chat_id_message_callback,
    cancel_by_chat_id_message_callback,
    select_bonus_create_country_callback,
    send_message_to_country_callback,
    send_message_to_country_group_country_callback,
    send_message_to_country_group_callback,
    approve_country_message_callback,
    cancel_country_message_callback,
    approve_country_group_message_callback,
    cancel_country_group_message_callback,
)
from bot.keyboards.default import manage_keyboard, cancel_keyboard, main_menu_keyboard
from bot.keyboards.inline import (
    view_bonus_keyboard,
    message_group_keyboard,
    all_bonus_requests_navigation_keyboard,
    send_bonus_2_group_confirmation_keyboard,
    select_bonus_request_filter_keyboard,
    message_inline_button_keyboard,
    personal_message_confirmation_keyboard,
    group_message_confirmation_keyboard,
    all_message_confirmation_keyboard,
    by_chat_id_message_confirmation_keyboard,
    select_bonus_country_keyboard,
    message_country_keyboard,
    message_country_group_select_country_keyboard,
    message_country_group_select_group_keyboard,
    country_message_confirmation_keyboard,
    country_group_message_confirmation_keyboard,
)
from bot.loader import dp, bot
from bot.states import (
    SendMessageToAll,
    CreateNewBonus,
    SendChatID,
    SendMessageToOne,
    MessageUser,
    SendBonusToUser,
    SendMessageToGroup,
    SendPersonalMessage,
    SendMessageToCountry,
    SendMessageToCountryGroup,
)
from common.constants import (
    BotCommands,
    DefaultKeyboardButtons,
    Groups,
    RequestReportTitles,
    BonusRequestStatuses,
    RequestReportTotalTitles,
)
from common.utils import ReportGenerator, is_pure_image_url, get_current_datetime
from config import ALL_BONUS_REQUESTS_PER_PAGE, SEND_SCHEDULED_CHUNK_SIZE
from logics import UserLogics, BonusLogics, BonusRequestLogics, ScheduledTargetLogics, CountryLogics
from logics.scheduled_message_logics import ScheduledMessageLogics
from models import User

regex = r"\((?=[^)]*\d)[\d:]+\)"


@dp.message_handler(Command([BotCommands.Manage.value, "admin", "panel"]), UserFilter(only_managers=True), state="*")
@dp.message_handler(Text([DefaultKeyboardButtons.AdminPanel.value, "🛠️ Admin Panel", "Admin Panel", "Manage"], ignore_case=True), UserFilter(only_managers=True), state="*")
async def process_manage(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()
    await message.answer("🛠️ <b>Admin Management Panel</b>", reply_markup=manage_keyboard(), parse_mode="HTML")


@dp.message_handler(Command(["user", "menu", "usermenu"]), UserFilter(), state="*")
@dp.message_handler(Text([DefaultKeyboardButtons.UserMenu.value, "👤 User Menu", "User Menu", "Exit Admin Panel"], ignore_case=True), UserFilter(), state="*")
async def process_switch_to_user_menu(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()
    user = UserLogics.get_by_chat_id(message.from_user.id)
    is_manager = bool(user and user.is_manager)
    await message.answer("Switched to <b>User Menu</b> 👤", reply_markup=main_menu_keyboard(is_manager=is_manager), parse_mode="HTML")


# ==================== REPORT GENERATION ====================

@dp.message_handler(Text([DefaultKeyboardButtons.ReportsGeneration.value, "⚙️ 📊", "Reports"], ignore_case=True), UserFilter(only_managers=True), state="*")
async def process_report_generation(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_requests_db = BonusRequestLogics.get_list()
    totals_user_data = {
        RequestReportTotalTitles.rejected_bonus_request_total.value:
            len([br for br in bonus_requests_db if br.status == BonusRequestStatuses.Canceled.value]),
        RequestReportTotalTitles.approved_bonus_request_total.value:
            len([br for br in bonus_requests_db if br.status == BonusRequestStatuses.Approved.value]),
        RequestReportTotalTitles.waiting_bonus_request_total.value:
            len([br for br in bonus_requests_db if br.status == BonusRequestStatuses.Active.value]),
        RequestReportTotalTitles.bonus_request_total.value:
            len(bonus_requests_db),
        RequestReportTotalTitles.users_total.value: UserLogics.count(),
        RequestReportTotalTitles.users_banned_or_disabled.value: UserLogics.count(is_blocked=True, is_active=False),
        RequestReportTotalTitles.users_with_bonus_request.value:
            len({br.user_id for br in bonus_requests_db}),
        RequestReportTotalTitles.users_with_rejected_bonus_requests.value:
            len({br.user_id for br in bonus_requests_db if br.status == BonusRequestStatuses.Canceled.value}),
        RequestReportTotalTitles.users_with_approved_bonus_requests.value:
            len({br.user_id for br in bonus_requests_db if br.status == BonusRequestStatuses.Approved.value}),
        RequestReportTotalTitles.users_with_waiting_bonus_requests.value:
            len({br.user_id for br in bonus_requests_db if br.status == BonusRequestStatuses.Active.value})
    }

    top_referral_sources_data = [{
        RequestReportTotalTitles.top_referral_sources.value: source.get('chat_id'),
        RequestReportTotalTitles.referrals_count.value: source.get('referral_count')
    } for source in UserLogics.get_top_referral_sources_list()]

    bonus_requests_data = []
    report_generator = ReportGenerator()

    if not report_generator.is_running():
        for bonus_request in bonus_requests_db:
            bonus = BonusLogics.get_by_id(bonus_request.bonus_id)
            user = UserLogics.get_by_id(bonus_request.user_id)

            if not bonus or not user:
                continue

            user_subscribed = str(await UserLogics.is_subscriber(bot=bot, chat_id=user.chat_id, user=user))
            country_name = user.country.name if user.country else "None"

            bonus_request_data = {
                RequestReportTitles.request_created_at.value: bonus_request.created_at,
                RequestReportTitles.user_created_at.value: user.created_at,
                RequestReportTitles.request_status.value: bonus_request.status,
                RequestReportTitles.tg_chat_id.value: user.chat_id,
                RequestReportTitles.site_id.value: user.site_id,
                RequestReportTitles.group.value: user.group,
                RequestReportTitles.country.value: country_name,
                RequestReportTitles.is_subscribed.value: user_subscribed,
                RequestReportTitles.bonus_description.value: bonus.description,
            }
            bonus_requests_data.append(bonus_request_data)

        report_generator.run_bonus_request_generation(bonus_requests_data, totals_user_data, top_referral_sources_data)

        with open(report_generator.report_filepath, "rb") as doc:
            await bot.send_document(
                chat_id=message.chat.id,
                document=doc,
                caption=f"📊 <b>Bonus Requests Report ({get_current_datetime().year})</b>",
                parse_mode="HTML"
            )

        await message.answer(
            text="✅ <b>The report was successfully generated and sent!</b> 📊",
            reply_markup=manage_keyboard(),
            parse_mode="HTML"
        )
        await sleep(1)
        report_generator.finish()
    else:
        await message.answer(text="⚠️ A report generation process is already in progress.",
                             reply_markup=manage_keyboard())


# ==================== BONUS REQUESTS MANAGEMENT ====================

@dp.callback_query_handler(open_bonus_request_status_filter_callback.filter(), UserFilter(only_managers=True))
async def process_bonus_request_status_filter(call: types.CallbackQuery, callback_data: dict):
    bonus_id = callback_data.get('bonus_id')
    await call.message.answer("Select Bonus Request status filter:",
                              reply_markup=select_bonus_request_filter_keyboard(bonus_id=bonus_id))


@dp.message_handler(Text([DefaultKeyboardButtons.AllBonusRequests.value, "🔍 ALL 💌"]), UserFilter(only_managers=True), state="*")
async def process_open_all_bonus_requests(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()
    await message.answer("Select Bonus Request status filter:", reply_markup=select_bonus_request_filter_keyboard())


@dp.callback_query_handler(bonus_request_status_filter_callback.filter(), UserFilter(only_managers=True))
async def process_bonus_request_status_filter(call: types.CallbackQuery, callback_data: dict):
    bonus_request_status = callback_data.get("bonus_request_status")
    bonus_id = callback_data.get("bonus_id", None)

    await send_all_bonus_requests_page(call=call, bonus_request_status=bonus_request_status, page=1, bonus_id=bonus_id)
    await call.answer()
    await call.message.delete()


@dp.callback_query_handler(all_bonus_requests_page_callback.filter(), UserFilter(only_managers=True))
async def process_all_bonus_requests_pagination(call: types.CallbackQuery, callback_data: dict):
    page = int(callback_data["page"])
    await send_all_bonus_requests_page(call=call, page=page)
    await call.answer()


async def send_all_bonus_requests_page(message=None, call=None, bonus_request_status=None, bonus_id=None, page=1):
    all_requests, total = get_paginated_filtered_bonus_requests(bonus_request_status, page, bonus_id)
    user = UserLogics.get_by_chat_id(message.from_user.id if message else call.from_user.id)

    target = call.message if call else message
    if not all_requests:
        status_label = f" ({bonus_request_status})" if bonus_request_status else ""
        await target.answer(
            f"No bonus requests found{status_label} 🔍\n\n"
            f"💡 <i>Bonus requests appear here after users click the <b>📲 Request Bonus</b> button.</i>\n"
            f"To view and manage all created bonuses, press <b>🔍 All Bonuses</b>.",
            parse_mode="HTML"
        )
        return

    for b_request in all_requests:
        await _send_bonus_request_info(
            user_id=user.id,
            bonus_request_id=b_request.id,
            bonus_id=b_request.bonus_id
        )
        await sleep(0.2)

    await target.answer(
        text=f"Page {page} / {(total + ALL_BONUS_REQUESTS_PER_PAGE - 1) // ALL_BONUS_REQUESTS_PER_PAGE}",
        reply_markup=all_bonus_requests_navigation_keyboard(page=page, total=total)
    )


def get_paginated_filtered_bonus_requests(bonus_request_status: str, page: int, bonus_id: str):
    all_requests = BonusRequestLogics.get_list(bonus_id=bonus_id, status=bonus_request_status)
    total = len(all_requests)
    start = (page - 1) * ALL_BONUS_REQUESTS_PER_PAGE
    end = start + ALL_BONUS_REQUESTS_PER_PAGE
    return all_requests[start:end], total


# ==================== BONUS CREATION ====================

@dp.message_handler(Command(["create_bonus", "new_bonus", "bonus_create", "add_bonus"]), UserFilter(only_managers=True), state="*")
@dp.message_handler(
    Text([
        DefaultKeyboardButtons.CreateBonus.value,
        "🎁 Create Bonus",
        "⚙️ 🎁",
        "⚙ 🎁",
        "Create Bonus",
        "+ Create Bonus"
    ], ignore_case=True),
    UserFilter(only_managers=True),
    state="*"
)
async def process_create_new_bonus(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()
    await CreateNewBonus.send_bonus_description.set()
    await message.answer(
        "📝 <b>Enter the new bonus description (&lt;1000 symbols) 👉</b>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@dp.message_handler(UserFilter(only_managers=True), state=CreateNewBonus.send_bonus_description, content_types=(ContentType.ANY,))
async def process_create_new_bonus_description(message: types.Message, state: FSMContext):
    text = (message.text or message.caption or "").strip()
    if not text:
        await message.answer("⚠️ Please enter a text description for the bonus (or send /cancel):")
        return

    if is_pure_image_url(text):
        await message.answer(
            "⚠️ <b>Warning:</b> You entered an image URL instead of a text description.\n\n"
            "Please enter a text description for the bonus. You can attach an image URL separately after creation using the 🖼️ Img button.",
            parse_mode="HTML"
        )
        return

    if len(text) > 1000:
        await message.answer("The bonus description must be less than 1000 characters. Try again:")
        return

    await state.finish()

    bonus = BonusLogics.create(
        description=text,
        group=Groups.All.value,
        country=None,
        is_request=True
    )

    group_icon = group_display_dict.get(Groups.All.value, ['🟩'])[0]
    try:
        await message.answer(
            f"✅ <b>New bonus created!</b> 🔴 <i>(inactive)</i>\n"
            f"💱 Currency: <b>💱 All Currencies</b>\n"
            f"👥 Group: {group_icon} <b>all</b>\n"
            f"💌 Requests: <b>Enabled</b>\n\n"
            f"{html.escape(text)}\n\n"
            f"💡 <i>Enable this bonus with 🟢 ON button below.</i>",
            reply_markup=view_bonus_keyboard(bonus_id=bonus.id),
            parse_mode="HTML"
        )
    except Exception:
        await message.answer(
            f"✅ New bonus created! 🔴 (inactive)\n"
            f"💱 Currency: All Currencies\n"
            f"👥 Group: {group_icon} all\n"
            f"💌 Requests: Enabled\n\n"
            f"{text}\n\n"
            f"💡 Enable this bonus with 🟢 ON button below.",
            reply_markup=view_bonus_keyboard(bonus_id=bonus.id)
        )


@dp.callback_query_handler(select_bonus_create_country_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_create_new_bonus_country(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    country_id = callback_data.get("country_id")
    data = await state.get_data() if state else {}
    description = data.get("description", "New Bonus")
    if state:
        await state.finish()

    target_country = None
    if country_id != "all":
        target_country = CountryLogics.get_by_id(country_id)

    bonus = BonusLogics.create(
        description=description,
        group=Groups.All.value,
        country=target_country
    )

    country_name = target_country.name if target_country else "💱 All Currencies"
    await call.message.delete()
    await call.message.answer(
        f"✅ <b>New bonus successfully created!</b>\n💱 Currency: <b>{country_name}</b>",
        reply_markup=view_bonus_keyboard(bonus_id=bonus.id),
        parse_mode="HTML"
    )


# ==================== SEND BONUS TO GROUP OR USER ====================

@dp.callback_query_handler(send_bonus_to_group_callback.filter(), UserFilter(only_managers=True))
async def process_send_bonus_to_group(call: types.CallbackQuery, callback_data: dict):
    bonus_id = callback_data.get("bonus_id")
    current_group = callback_data.get("current_group")
    await call.message.answer(
        f"<i>The bonus will be sent to {user_group_display_dict.get(current_group)[0]} {current_group} group instantly</i> ⚠️\nAre you sure? 👉",
        reply_markup=send_bonus_2_group_confirmation_keyboard(bonus_id=bonus_id, current_group=current_group),
        parse_mode="HTML"
    )
    await call.message.delete()


@dp.callback_query_handler(send_bonus_2_group_approve_callback.filter(), UserFilter(only_managers=True))
async def process_approve_send_bonus_to_group(call: types.CallbackQuery, callback_data: dict):
    bonus_id = callback_data.get("bonus_id")
    current_group = callback_data.get("current_group")
    bonus = BonusLogics.get_by_id(bonus_id)

    # If bonus is country-specific, only send to users of that country
    if bonus and bonus.country:
        group_users = UserLogics.get_country_list(country_id=bonus.country.id, group=current_group)
    else:
        group_users = UserLogics.get_group_list(group=current_group)

    group_users = [u for u in group_users if u.is_active and not u.is_blocked]

    for g_user in group_users:
        try:
            is_requested = len([r for r in BonusRequestLogics.get_list(user_id=g_user.id, bonus_id=bonus_id) if r.status in (BonusRequestStatuses.Active.value, BonusRequestStatuses.Approved.value)]) > 0
            await _send_bonus_info(user_id=g_user.chat_id, bonus_id=bonus_id, is_requested=is_requested)
        except (BotBlocked, ChatNotFound, UserDeactivated):
            g_user.is_active = False
            g_user.save(only=(User.is_active,))

    await call.message.answer(
        f"The bonus has been sent to {len(group_users)} users in {user_group_display_dict.get(current_group)[0]} {current_group} group ✅",
        reply_markup=manage_keyboard()
    )
    await sleep(0.2)
    await call.message.delete()
    await _send_bonus_info(call.from_user.id, bonus_id)


@dp.callback_query_handler(send_bonus_2_group_cancel_callback.filter(), UserFilter(only_managers=True))
async def process_cancel_send_bonus_to_group(call: types.CallbackQuery, callback_data: dict):
    bonus_id = callback_data.get("bonus_id")
    await call.message.answer("The bonus was not sent 🚨", reply_markup=manage_keyboard())
    await sleep(0.2)
    await call.message.delete()
    await _send_bonus_info(call.from_user.id, bonus_id)


@dp.callback_query_handler(send_bonus_to_user_callback.filter(), UserFilter(only_managers=True))
async def process_send_bonus_to_user(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    bonus_id = callback_data.get("bonus_id")
    await call.message.answer("Enter chat ID 👉:\n<i>The bonus will be sent to the user instantly</i> ⚠️",
                              reply_markup=cancel_keyboard(), parse_mode="HTML")
    await state.update_data(bonus_id=bonus_id)
    await SendBonusToUser.send_bonus.set()
    await call.message.delete()


@dp.message_handler(UserFilter(only_managers=True), state=SendBonusToUser.send_bonus)
async def process_confirm_send_bonus_to_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bonus_id = data.get("bonus_id")
    user_chat_id_to_notify = message.text.strip()
    await state.finish()

    if user_chat_id_to_notify.isdigit() and len(user_chat_id_to_notify) < 20:
        user_to_notify = UserLogics.get_by_chat_id(user_chat_id_to_notify)
        if not user_to_notify:
            await message.answer("Target user not found in database 🚨", reply_markup=manage_keyboard())
            return
        try:
            await _send_bonus_info(user_to_notify.chat_id, bonus_id)
            await message.answer("The bonus has been sent personally ✅", reply_markup=manage_keyboard())
        except (BotBlocked, ChatNotFound, UserDeactivated):
            user_to_notify.is_active = False
            user_to_notify.save(only=(User.is_active,))
            await message.answer("Message not sent: user blocked bot or chat ID not found 🚨", reply_markup=manage_keyboard())
            return
    else:
        await message.answer("Invalid chat ID input (digits only) 🚨", reply_markup=manage_keyboard())

    await _send_bonus_info(message.from_user.id, bonus_id)


# ==================== MESSAGE SINGLE USER ====================

@dp.callback_query_handler(message_user_callback.filter(), UserFilter(only_managers=True))
async def process_message_user(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    opened_user_id = callback_data.get('opened_user_id')
    await call.message.answer(
        "The message will be sent to the user instantly ⚠️\n\n"
        "To schedule the message, add tag at the start in format: (HH:DD:MM:YY)\n"
        "Content formats:\n"
        "1. Text only\n"
        "2. Text | Image URL\n"
        "3. Text | Image URL | Button URL",
        reply_markup=cancel_keyboard()
    )
    await state.update_data(opened_user_id=opened_user_id)
    await MessageUser.send_message.set()


@dp.message_handler(UserFilter(only_managers=True), state=MessageUser.send_message)
async def process_confirm_message_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    opened_user_id = data.get("opened_user_id")
    opened_user = UserLogics.get_by_id(opened_user_id)

    content = message.text.strip()
    send_at = _parse_schedule_time(content)
    if send_at == "INVALID":
        await message.answer("🚨 Invalid time format. Use (HH), (HH:DD), (HH:DD:MM), or (HH:DD:MM:YYYY).", reply_markup=manage_keyboard())
        return

    clean_content = re.sub(regex, '', content).strip() if send_at else content
    parts = clean_content.split("|")
    text = parts[0].strip()
    image_url = parts[1].strip() if len(parts) >= 2 else ''
    button_url = parts[2].strip() if len(parts) == 3 else ''

    await state.update_data({
        "opened_user_id": opened_user_id,
        "text": text,
        "image_url": image_url,
        "button_url": button_url,
        "send_at": send_at.isoformat() if send_at else None
    })

    await message.answer(
        f"📝 Confirm sending message to user <code>{opened_user.chat_id}</code>?",
        reply_markup=personal_message_confirmation_keyboard(),
        parse_mode="HTML"
    )
    await SendPersonalMessage.send_message.set()


@dp.callback_query_handler(UserFilter(only_managers=True), cancel_personal_message_callback.filter(), state=SendPersonalMessage.send_message)
async def cancel_personal_message_handler(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("🚫 Message cancelled.", reply_markup=manage_keyboard())
    await state.finish()


@dp.callback_query_handler(UserFilter(only_managers=True), approve_personal_message_callback.filter(), state=SendPersonalMessage.send_message)
async def approve_personal_message_handler(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await call.message.delete()

    opened_user_id = data.get("opened_user_id")
    opened_user = UserLogics.get_by_id(opened_user_id)
    text = data.get("text", "")
    image_url = data.get("image_url", "")
    button_url = data.get("button_url", "")
    send_at_str = data.get("send_at")
    send_at = datetime.fromisoformat(send_at_str) if send_at_str else None

    reply_markup = message_inline_button_keyboard(button_url) if button_url else None

    if send_at:
        manager = UserLogics.get_by_chat_id(call.from_user.id)
        scheduled_message = ScheduledMessageLogics.create(
            user_id=manager.id, text=text, photo_url=image_url, button_url=button_url, send_at=send_at
        )
        ScheduledTargetLogics.create(scheduled_message_id=scheduled_message.id, chat_id=opened_user.chat_id)
        await call.message.answer(f"⏳ Message scheduled for <b>{send_at.strftime('%Y-%m-%d %H:%M')}</b> ✅", reply_markup=manage_keyboard(), parse_mode="HTML")
    else:
        try:
            if image_url:
                await bot.send_photo(chat_id=opened_user.chat_id, photo=image_url, caption=text, reply_markup=reply_markup, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=opened_user.chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
            await call.message.answer("✅ Message sent successfully.", reply_markup=manage_keyboard())
        except (BotBlocked, ChatNotFound, UserDeactivated):
            opened_user.is_active = False
            opened_user.save(only=(User.is_active,))
            await call.message.answer("🚨 Bot blocked or user chat not found.", reply_markup=manage_keyboard())

    await _send_user_info(call.message, opened_user_id)
    await state.finish()


# ==================== BROADCAST TO GROUP ====================

@dp.message_handler(Text([DefaultKeyboardButtons.SendMessageToGroup.value, "📩 👥 🟧"]), UserFilter(only_managers=True), state="*")
async def process_send_message_to_group(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()
    await message.answer("Select the group to message 👉:", reply_markup=message_group_keyboard())


@dp.callback_query_handler(send_message_to_group_callback.filter(), UserFilter(only_managers=True))
async def process_send_message_to_selected_group(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    group = callback_data.get('group')
    await SendMessageToGroup.send_message.set()
    await call.message.answer(
        f"The message will be sent to <b>{group}</b> group.\n\n"
        "To schedule, add tag at start: (HH:DD:MM:YY)\n"
        "Formats:\n1. Text\n2. Text | Image URL\n3. Text | Image URL | Button URL",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.update_data(group=group)


@dp.message_handler(UserFilter(only_managers=True), state=SendMessageToGroup.send_message, content_types=(ContentType.TEXT,))
async def process_confirm_message_to_group_sending(message: types.Message, state: FSMContext):
    data = await state.get_data()
    group = data.get("group")
    users = [u for u in UserLogics.get_group_list(group) if u.is_active and not u.is_blocked]

    content = message.text.strip()
    send_at = _parse_schedule_time(content)
    if send_at == "INVALID":
        await message.answer("🚨 Invalid time format. Use (HH), (HH:DD), (HH:DD:MM), or (HH:DD:MM:YYYY).", reply_markup=manage_keyboard())
        return

    clean_content = re.sub(regex, '', content).strip() if send_at else content
    parts = clean_content.split("|")
    text = parts[0].strip()
    image_url = parts[1].strip() if len(parts) >= 2 else ''
    button_url = parts[2].strip() if len(parts) == 3 else ''

    await state.update_data({
        "group": group, "text": text, "image_url": image_url, "button_url": button_url,
        "send_at": send_at.isoformat() if send_at else None
    })

    await message.answer(
        f"📝 Confirm sending this message to <b>{len(users)}</b> users in group <b>{group}</b>?",
        reply_markup=group_message_confirmation_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query_handler(UserFilter(only_managers=True), cancel_group_message_callback.filter(), state="*")
async def cancel_group_message_handler(call: types.CallbackQuery, state: FSMContext = None):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer("🚫 Group message cancelled.", reply_markup=manage_keyboard())
    if state:
        await state.finish()


@dp.callback_query_handler(UserFilter(only_managers=True), approve_group_message_callback.filter(), state="*")
async def approve_group_message_handler(call: types.CallbackQuery, state: FSMContext = None):
    data = await state.get_data() if state else {}
    try:
        await call.message.delete()
    except Exception:
        pass

    group = data.get("group")
    text = data.get("text")
    image_url = data.get("image_url")
    button_url = data.get("button_url")
    send_at_str = data.get("send_at")
    send_at = datetime.fromisoformat(send_at_str) if send_at_str else None
    manager = UserLogics.get_by_chat_id(call.from_user.id)

    if not text or not group:
        await call.message.answer("⚠️ Message session expired. Please try sending again.", reply_markup=manage_keyboard())
        if state:
            await state.finish()
        return

    users = [u for u in UserLogics.get_group_list(group) if u.is_active and not u.is_blocked]
    if not users:
        await call.message.answer("🚫 No active users found in the selected group.", reply_markup=manage_keyboard())
        if state:
            await state.finish()
        return

    await _execute_broadcast(call, manager, users, text, image_url, button_url, send_at, target_name=f"group {group}")
    if state:
        await state.finish()


# ==================== BROADCAST TO COUNTRY ====================

@dp.message_handler(Text([DefaultKeyboardButtons.SendMessageToCountry.value, "📩 Message Currency", "📩 Message Country", "📩 👥 🌍", "📩 👥 💱"], ignore_case=True), UserFilter(only_managers=True), state="*")
async def process_send_message_to_country_start(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()
    countries = CountryLogics.get_list(is_removed=False)
    if not countries:
        await message.answer("No currencies available. Please create a currency first.", reply_markup=manage_keyboard())
        return
    await message.answer("Select target currency to broadcast 👉:", reply_markup=message_country_keyboard(countries))


@dp.callback_query_handler(send_message_to_country_callback.filter(), UserFilter(only_managers=True))
async def process_send_message_to_selected_country(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    country_id = callback_data.get('country_id')
    country = CountryLogics.get_by_id(country_id)
    if not country:
        await call.answer("Currency not found.", show_alert=True)
        return

    await SendMessageToCountry.send_message.set()
    await state.update_data(country_id=country_id)
    await call.message.answer(
        f"The message will be sent to all users in <b>{country.name}</b>.\n\n"
        "To schedule, add tag at start: (HH:DD:MM:YY)\n"
        "Formats:\n1. Text\n2. Text | Image URL\n3. Text | Image URL | Button URL",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@dp.message_handler(UserFilter(only_managers=True), state=SendMessageToCountry.send_message, content_types=(ContentType.TEXT,))
async def process_confirm_message_to_country(message: types.Message, state: FSMContext):
    data = await state.get_data()
    country_id = data.get("country_id")
    country = CountryLogics.get_by_id(country_id)
    users = [u for u in UserLogics.get_country_list(country_id=country_id) if u.is_active and not u.is_blocked]

    content = message.text.strip()
    send_at = _parse_schedule_time(content)
    if send_at == "INVALID":
        await message.answer("🚨 Invalid time format. Use (HH), (HH:DD), (HH:DD:MM), or (HH:DD:MM:YYYY).", reply_markup=manage_keyboard())
        return

    clean_content = re.sub(regex, '', content).strip() if send_at else content
    parts = clean_content.split("|")
    text = parts[0].strip()
    image_url = parts[1].strip() if len(parts) >= 2 else ''
    button_url = parts[2].strip() if len(parts) == 3 else ''

    await state.update_data({
        "country_id": country_id, "text": text, "image_url": image_url, "button_url": button_url,
        "send_at": send_at.isoformat() if send_at else None
    })

    await message.answer(
        f"📝 Confirm sending this message to <b>{len(users)}</b> users in <b>{country.name}</b>?",
        reply_markup=country_message_confirmation_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query_handler(UserFilter(only_managers=True), cancel_country_message_callback.filter(), state="*")
async def cancel_country_message_handler(call: types.CallbackQuery, state: FSMContext = None):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer("🚫 Currency message cancelled.", reply_markup=manage_keyboard())
    if state:
        await state.finish()


@dp.callback_query_handler(UserFilter(only_managers=True), approve_country_message_callback.filter(), state="*")
async def approve_country_message_handler(call: types.CallbackQuery, state: FSMContext = None):
    data = await state.get_data() if state else {}
    try:
        await call.message.delete()
    except Exception:
        pass

    country_id = data.get("country_id")
    country = CountryLogics.get_by_id(country_id)
    text = data.get("text")
    image_url = data.get("image_url")
    button_url = data.get("button_url")
    send_at_str = data.get("send_at")
    send_at = datetime.fromisoformat(send_at_str) if send_at_str else None
    manager = UserLogics.get_by_chat_id(call.from_user.id)

    if not text or not country_id:
        await call.message.answer("⚠️ Message session expired. Please try sending again.", reply_markup=manage_keyboard())
        if state:
            await state.finish()
        return

    users = [u for u in UserLogics.get_country_list(country_id=country_id) if u.is_active and not u.is_blocked]
    if not users:
        await call.message.answer(f"🚫 No active users found in {country.name if country else 'selected currency'}.", reply_markup=manage_keyboard())
        if state:
            await state.finish()
        return

    await _execute_broadcast(call, manager, users, text, image_url, button_url, send_at, target_name=f"currency {country.name if country else country_id}")
    if state:
        await state.finish()


# ==================== BROADCAST TO COUNTRY + GROUP ====================

@dp.message_handler(Text([DefaultKeyboardButtons.SendMessageToCountryGroup.value, "📩 Message Currency+Group", "📩 Message Country+Group", "📩 👥 🌍 🟧", "📩 👥 💱 🟧"], ignore_case=True), UserFilter(only_managers=True), state="*")
async def process_send_message_to_country_group_start(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()
    countries = CountryLogics.get_list(is_removed=False)
    if not countries:
        await message.answer("No currencies available. Please create a currency first.", reply_markup=manage_keyboard())
        return
    await message.answer("Select target currency 👉:", reply_markup=message_country_group_select_country_keyboard(countries))


@dp.callback_query_handler(send_message_to_country_group_country_callback.filter(), UserFilter(only_managers=True))
async def process_send_message_cg_select_group(call: types.CallbackQuery, callback_data: dict):
    country_id = callback_data.get('country_id')
    country = CountryLogics.get_by_id(country_id)
    if not country:
        await call.answer("Currency not found.", show_alert=True)
        return

    await call.message.answer(
        f"Select group for currency <b>{country.name}</b> 👉:",
        reply_markup=message_country_group_select_group_keyboard(country_id),
        parse_mode="HTML"
    )
    await call.message.delete()


@dp.callback_query_handler(send_message_to_country_group_callback.filter(), UserFilter(only_managers=True))
async def process_send_message_cg_selected(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    country_id = callback_data.get('country_id')
    group = callback_data.get('group')
    country = CountryLogics.get_by_id(country_id)

    await SendMessageToCountryGroup.send_message.set()
    await state.update_data(country_id=country_id, group=group)

    await call.message.answer(
        f"The message will be sent to <b>{country.name}</b>, group <b>{group}</b>.\n\n"
        "To schedule, add tag at start: (HH:DD:MM:YY)\n"
        "Formats:\n1. Text\n2. Text | Image URL\n3. Text | Image URL | Button URL",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@dp.message_handler(UserFilter(only_managers=True), state=SendMessageToCountryGroup.send_message, content_types=(ContentType.TEXT,))
async def process_confirm_message_to_country_group(message: types.Message, state: FSMContext):
    data = await state.get_data()
    country_id = data.get("country_id")
    group = data.get("group")
    country = CountryLogics.get_by_id(country_id)
    users = [u for u in UserLogics.get_country_list(country_id=country_id, group=group) if u.is_active and not u.is_blocked]

    content = message.text.strip()
    send_at = _parse_schedule_time(content)
    if send_at == "INVALID":
        await message.answer("🚨 Invalid time format. Use (HH), (HH:DD), (HH:DD:MM), or (HH:DD:MM:YYYY).", reply_markup=manage_keyboard())
        return

    clean_content = re.sub(regex, '', content).strip() if send_at else content
    parts = clean_content.split("|")
    text = parts[0].strip()
    image_url = parts[1].strip() if len(parts) >= 2 else ''
    button_url = parts[2].strip() if len(parts) == 3 else ''

    await state.update_data({
        "country_id": country_id, "group": group, "text": text, "image_url": image_url, "button_url": button_url,
        "send_at": send_at.isoformat() if send_at else None
    })

    await message.answer(
        f"📝 Confirm sending this message to <b>{len(users)}</b> users in <b>{country.name}</b> (Group: <b>{group}</b>)?",
        reply_markup=country_group_message_confirmation_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query_handler(UserFilter(only_managers=True), cancel_country_group_message_callback.filter(), state="*")
async def cancel_country_group_message_handler(call: types.CallbackQuery, state: FSMContext = None):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer("🚫 Broadcast cancelled.", reply_markup=manage_keyboard())
    if state:
        await state.finish()


@dp.callback_query_handler(UserFilter(only_managers=True), approve_country_group_message_callback.filter(), state="*")
async def approve_country_group_message_handler(call: types.CallbackQuery, state: FSMContext = None):
    data = await state.get_data() if state else {}
    try:
        await call.message.delete()
    except Exception:
        pass

    country_id = data.get("country_id")
    group = data.get("group")
    country = CountryLogics.get_by_id(country_id)
    text = data.get("text")
    image_url = data.get("image_url")
    button_url = data.get("button_url")
    send_at_str = data.get("send_at")
    send_at = datetime.fromisoformat(send_at_str) if send_at_str else None
    manager = UserLogics.get_by_chat_id(call.from_user.id)

    if not text or not country_id or not group:
        await call.message.answer("⚠️ Message session expired. Please try sending again.", reply_markup=manage_keyboard())
        if state:
            await state.finish()
        return

    users = [u for u in UserLogics.get_country_list(country_id=country_id, group=group) if u.is_active and not u.is_blocked]
    if not users:
        await call.message.answer(f"🚫 No active users found in {country.name if country else 'currency'} for group {group}.", reply_markup=manage_keyboard())
        if state:
            await state.finish()
        return

    await _execute_broadcast(call, manager, users, text, image_url, button_url, send_at, target_name=f"{country.name if country else country_id} - group {group}")
    if state:
        await state.finish()


# ==================== BROADCAST TO ALL ====================

@dp.message_handler(Text([DefaultKeyboardButtons.SendMessageToAll.value, "📩 👥"]), UserFilter(only_managers=True), state="*")
async def process_send_message_to_all(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()
    await SendMessageToAll.send_message.set()
    await message.answer(
        "The message will be sent to <b>all</b> users ⚠️\n\n"
        "To schedule, add tag at start: (HH:DD:MM:YY)\n"
        "Formats:\n1. Text\n2. Text | Image URL\n3. Text | Image URL | Button URL",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@dp.message_handler(UserFilter(only_managers=True), state=SendMessageToAll.send_message, content_types=(ContentType.TEXT,))
async def process_confirm_message_to_all_sending(message: types.Message, state: FSMContext):
    users = list(User.select(User.id, User.chat_id).where(User.is_active, ~User.is_blocked))
    if not users:
        await message.answer("🚫 No active users to send the message to.", reply_markup=manage_keyboard())
        return

    content = message.text.strip()
    send_at = _parse_schedule_time(content)
    if send_at == "INVALID":
        await message.answer("🚨 Invalid time format. Use (HH), (HH:DD), (HH:DD:MM), or (HH:DD:MM:YYYY).", reply_markup=manage_keyboard())
        return

    clean_content = re.sub(regex, '', content).strip() if send_at else content
    parts = clean_content.split("|")
    text = parts[0].strip()
    image_url = parts[1].strip() if len(parts) >= 2 else ''
    button_url = parts[2].strip() if len(parts) == 3 else ''

    await state.update_data({
        "text": text, "image_url": image_url, "button_url": button_url,
        "send_at": send_at.isoformat() if send_at else None
    })

    await message.answer(
        f"📝 Confirm sending this message to <b>{len(users)}</b> users?",
        reply_markup=all_message_confirmation_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query_handler(UserFilter(only_managers=True), cancel_all_message_callback.filter(), state="*")
async def cancel_all_message_handler(call: types.CallbackQuery, state: FSMContext = None):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer("🚫 Sending to all users cancelled.", reply_markup=manage_keyboard())
    if state:
        await state.finish()


@dp.callback_query_handler(UserFilter(only_managers=True), approve_all_message_callback.filter(), state="*")
async def approve_all_message_handler(call: types.CallbackQuery, state: FSMContext = None):
    data = await state.get_data() if state else {}
    try:
        await call.message.delete()
    except Exception:
        pass

    text = data.get("text")
    if not text:
        await call.message.answer("⚠️ Message session expired. Please try sending again.", reply_markup=manage_keyboard())
        if state:
            await state.finish()
        return

    manager = UserLogics.get_by_chat_id(call.from_user.id)
    users = list(User.select(User.id, User.chat_id).where(User.is_active, ~User.is_blocked))

    image_url = data.get("image_url")
    button_url = data.get("button_url")
    send_at_str = data.get("send_at")
    send_at = datetime.fromisoformat(send_at_str) if send_at_str else None

    await _execute_broadcast(call, manager, users, text, image_url, button_url, send_at, target_name="all users")
    if state:
        await state.finish()


# ==================== SEND BY CHAT ID ====================

@dp.message_handler(Text([DefaultKeyboardButtons.SendMessageToOne.value, "📩 👤"]), UserFilter(only_managers=True), state="*")
async def process_send_chat_id(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()
    await SendChatID.send_chat_id.set()
    await message.answer("Enter the recipient <b>chat_id</b>:", reply_markup=cancel_keyboard(), parse_mode="HTML")


@dp.message_handler(UserFilter(only_managers=True), state=SendChatID.send_chat_id, content_types=(ContentType.ANY,))
async def process_send_message_by_chat_id(message: types.Message, state: FSMContext):
    await state.finish()
    recipient_chat_id = message.text.strip()
    if recipient_chat_id.isdigit():
        user = User.select(User.id, User.chat_id).where(User.is_active, User.chat_id == int(recipient_chat_id)).first()
        if user:
            await state.update_data(recipient_chat_id=recipient_chat_id)
            await SendMessageToOne.send_message.set()
            await message.answer(
                f"Send message to Chat ID 📬 <code>{recipient_chat_id}</code>\n"
                "To schedule, add tag at start: (HH:DD:MM:YY)\n\n"
                "Formats:\n1. Text\n2. Text | Image URL\n3. Text | Image URL | Button URL",
                reply_markup=cancel_keyboard(),
                parse_mode="HTML"
            )
        else:
            await message.answer(f"The user with chat_id <code>{recipient_chat_id}</code> was not found ⚠️", reply_markup=manage_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Recipient chat_id must contain numbers only 🚨", reply_markup=manage_keyboard())


@dp.message_handler(UserFilter(only_managers=True), state=SendMessageToOne.send_message, content_types=(ContentType.TEXT,))
async def process_confirm_sending_by_chat_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    recipient_chat_id = data.get("recipient_chat_id")

    user = UserLogics.get_by_chat_id(recipient_chat_id)
    if not user or not user.is_active or user.is_blocked:
        await message.answer("🚫 Target user is not active or is blocked.", reply_markup=manage_keyboard())
        await state.finish()
        return

    content = message.text.strip()
    send_at = _parse_schedule_time(content)
    if send_at == "INVALID":
        await message.answer("❌ Invalid time format. Use (HH), (HH:DD), (HH:DD:MM), or (HH:DD:MM:YYYY).", reply_markup=manage_keyboard())
        return

    clean_content = re.sub(regex, '', content).strip() if send_at else content
    parts = clean_content.split("|")
    text = parts[0].strip()
    image_url = parts[1].strip() if len(parts) >= 2 else ''
    button_url = parts[2].strip() if len(parts) == 3 else ''

    await state.update_data({
        "recipient_chat_id": recipient_chat_id, "text": text, "image_url": image_url, "button_url": button_url,
        "send_at": send_at.isoformat() if send_at else None
    })

    await message.answer(
        f"📝 Confirm sending message to user <code>{recipient_chat_id}</code>?",
        reply_markup=by_chat_id_message_confirmation_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query_handler(UserFilter(only_managers=True), cancel_by_chat_id_message_callback.filter(), state="*")
async def cancel_one_message_handler(call: types.CallbackQuery, state: FSMContext = None):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer("🚫 Sending to user cancelled.", reply_markup=manage_keyboard())
    if state:
        await state.finish()


@dp.callback_query_handler(UserFilter(only_managers=True), approve_by_chat_id_message_callback.filter(), state="*")
async def approve_one_message_handler(call: types.CallbackQuery, state: FSMContext = None):
    data = await state.get_data() if state else {}
    try:
        await call.message.delete()
    except Exception:
        pass

    recipient_chat_id = data.get("recipient_chat_id")
    text = data.get("text")
    if not recipient_chat_id or not text:
        await call.message.answer("⚠️ Message session expired. Please try sending again.", reply_markup=manage_keyboard())
        if state:
            await state.finish()
        return

    image_url = data.get("image_url")
    button_url = data.get("button_url")
    send_at_str = data.get("send_at")
    send_at = datetime.fromisoformat(send_at_str) if send_at_str else None

    user = UserLogics.get_by_chat_id(recipient_chat_id)
    if not user or not user.is_active or user.is_blocked:
        await call.message.answer("🚫 Target user is not active or is blocked.", reply_markup=manage_keyboard())
        if state:
            await state.finish()
        return

    manager = UserLogics.get_by_chat_id(call.from_user.id)
    reply_markup = message_inline_button_keyboard(button_url) if button_url else None

    if send_at:
        scheduled_message = ScheduledMessageLogics.create(
            user_id=manager.id, text=text, photo_url=image_url, button_url=button_url, send_at=send_at
        )
        ScheduledTargetLogics.create(scheduled_message_id=scheduled_message.id, chat_id=recipient_chat_id)
        await call.message.answer(f"⏳ Message scheduled for <b>{send_at.strftime('%Y-%m-%d %H:%M')}</b>.", reply_markup=manage_keyboard(), parse_mode="HTML")
    else:
        try:
            if image_url:
                try:
                    await bot.send_photo(chat_id=recipient_chat_id, photo=image_url, caption=text, reply_markup=reply_markup, parse_mode="HTML")
                except Exception as img_err:
                    logging.warning(f"Failed to send photo to {recipient_chat_id}, falling back to text: {img_err}")
                    await bot.send_message(chat_id=recipient_chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
            else:
                await bot.send_message(chat_id=recipient_chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
            await call.message.answer("✅ Message sent successfully.", reply_markup=manage_keyboard())
        except (BotBlocked, ChatNotFound, UserDeactivated):
            user.is_active = False
            user.save(only=(User.is_active,))
            await call.message.answer("🚫 Bot blocked or user chat not found.", reply_markup=manage_keyboard())
        except Exception as e:
            logging.error(f"Failed to send to {recipient_chat_id}: {e}")
            await call.message.answer("🚨 Unexpected error occurred.", reply_markup=manage_keyboard())

    if state:
        await state.finish()


# ==================== HELPER BROADCAST EXECUTION ====================

async def _execute_broadcast(call, manager, users, text, image_url, button_url, send_at, target_name):
    reply_markup = message_inline_button_keyboard(button_url) if button_url else None

    if send_at:
        scheduled_message = ScheduledMessageLogics.create(
            user_id=manager.id, text=text, photo_url=image_url, button_url=button_url, send_at=send_at
        )
        for u in users:
            if u.chat_id != call.from_user.id:
                ScheduledTargetLogics.create(scheduled_message.id, u.chat_id)

        await call.message.answer(
            f"⏳ Scheduled for <b>{send_at.strftime('%Y-%m-%d %H:%M')}</b> to <b>{len(users)}</b> users in <b>{target_name}</b>.",
            reply_markup=manage_keyboard(), parse_mode="HTML"
        )
    else:
        success, fail = 0, 0

        async def send_to_user(u):
            nonlocal success, fail
            if u.chat_id == call.from_user.id:
                return
            try:
                if image_url:
                    try:
                        await bot.send_photo(u.chat_id, image_url, caption=text, reply_markup=reply_markup, parse_mode="HTML")
                    except Exception as img_err:
                        logging.warning(f"Failed to send photo to {u.chat_id}, falling back to text: {img_err}")
                        await bot.send_message(u.chat_id, text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
                else:
                    await bot.send_message(u.chat_id, text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
                success += 1
            except (BotBlocked, ChatNotFound, UserDeactivated):
                u.is_active = False
                u.save(only=(User.is_active,))
                fail += 1
            except Exception as e:
                logging.error(f"Failed to send to {u.chat_id}: {e}")
                fail += 1

        CHUNK_SIZE = 20
        for i in range(0, len(users), CHUNK_SIZE):
            chunk = users[i:i + CHUNK_SIZE]
            await gather(*(send_to_user(u) for u in chunk))
            await sleep(1.5)

        await call.message.answer(
            f"✅ Sent to {success} users in <b>{target_name}</b>.\n🚫 {fail} failed (blocked/inactive).",
            reply_markup=manage_keyboard(), parse_mode="HTML"
        )


def _parse_schedule_time(content: str):
    send_at_match = re.search(regex, content)
    if not send_at_match:
        return None

    raw_time = send_at_match.group()[1:-1]
    try:
        send_time_parts = [int(p.strip()) for p in raw_time.split(':')]
        time_parts = [None, None, None, None]
        for i in range(min(len(send_time_parts), 4)):
            time_parts[i] = send_time_parts[i]

        now = datetime.now()
        hour = time_parts[0]
        day = time_parts[1] or now.day
        month = time_parts[2] or now.month
        year = time_parts[3] or now.year

        tentative_date = datetime(year, month, day, hour)
        if tentative_date <= now:
            if not time_parts[1]:
                tentative_date += timedelta(days=1)
            elif not time_parts[2]:
                tentative_date = datetime(year + 1, 1, day, hour) if month == 12 else datetime(year, month + 1, day, hour)
            elif not time_parts[3]:
                tentative_date = datetime(year + 1, month, day, hour)

        return tentative_date
    except Exception:
        return "INVALID"


# ==================== SCHEDULED MESSAGES CRON ====================

async def process_scheduled_messages():
    all_scheduled_messages = ScheduledMessageLogics.get_list(only_due=True)
    to_remove_scheduled_messages = [sm for sm in all_scheduled_messages if ScheduledMessageLogics.is_expired(sm)]

    for scheduled_message in to_remove_scheduled_messages:
        all_scheduled_targets = ScheduledTargetLogics.get_list(scheduled_message_id=scheduled_message.id)
        for scheduled_target in all_scheduled_targets:
            ScheduledTargetLogics.remove_as_sent(scheduled_target)
        ScheduledMessageLogics.remove_as_sent(scheduled_message)

    for scheduled_message in all_scheduled_messages:
        all_targets = ScheduledTargetLogics.get_list(scheduled_message_id=scheduled_message.id)

        async def send_to_target(target):
            chat_id = target.chat_id
            user = UserLogics.get_by_chat_id(chat_id)
            try:
                reply_markup = message_inline_button_keyboard(scheduled_message.button_url) if scheduled_message.button_url else None
                if scheduled_message.photo_url:
                    await bot.send_photo(chat_id=chat_id, photo=scheduled_message.photo_url, caption=scheduled_message.text, reply_markup=reply_markup, parse_mode="HTML")
                else:
                    await bot.send_message(chat_id=chat_id, text=scheduled_message.text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
                ScheduledTargetLogics.remove_as_sent(target)
            except (BotBlocked, ChatNotFound, UserDeactivated):
                if user:
                    user.is_active = False
                    user.save(only=(User.is_active,))
                ScheduledTargetLogics.remove_as_sent(target)
            except Exception as e:
                logging.error(f"Could not send to {chat_id}: {e}")

        for i in range(0, len(all_targets), SEND_SCHEDULED_CHUNK_SIZE):
            chunk = all_targets[i:i + SEND_SCHEDULED_CHUNK_SIZE]
            await gather(*(send_to_target(t) for t in chunk))
            await sleep(1.5)

        remaining_targets = ScheduledTargetLogics.get_list(scheduled_message_id=scheduled_message.id)
        if not remaining_targets:
            ScheduledMessageLogics.remove_as_sent(scheduled_message)
