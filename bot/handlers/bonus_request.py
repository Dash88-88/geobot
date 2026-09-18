import logging
from asyncio import sleep
from aiogram import types
from aiogram.dispatcher.filters import Text
from bot.filters import UserFilter
from bot.keyboards.callback_datas import (
    group_display_dict,
    request_bonus_callback,
    bonus_already_requested_callback,
    cancel_bonus_request_callback,
    approve_bonus_request_callback,
    activate_bonus_request_callback,
    bonus_requests_page_callback,
    activate_br_cancel_callback,
    activate_br_approve_callback,
    cancel_br_cancel_callback,
    cancel_br_approve_callback,
    approve_br_approve_callback,
    approve_br_cancel_callback,
    refresh_bonus_request_callback,
    cancel_br_approve_opt_callback,
)
from bot.keyboards.default import main_menu_keyboard, manage_keyboard
from bot.keyboards.inline import (
    bonus_request_keyboard,
    bonus_requests_navigation_keyboard,
    activate_bonus_request_confirmation_keyboard,
    approve_bonus_request_confirmation_keyboard,
    cancel_bonus_request_options_keyboard,
)
from bot.loader import dp, bot
from common.constants import (
    DATETIME_FORMAT,
    DefaultKeyboardButtons,
    BonusRequestStatuses,
    bonus_request_icon_dict,
    DefaultInlineButtons,
    BonusRequestRejectReasons,
    get_reject_reason_text,
    Groups,
)
from common.exceptions import (
    BonusAlreadyApprovedError,
    BonusAlreadyActivatedError,
    BonusAlreadyCanceledError,
)
from config import REGISTRATION_URL, COMMUNITY_URL, BONUS_REQUESTS_PER_PAGE
from logics import UserLogics, BonusRequestLogics, BonusLogics


async def _send_bonus_request_info(user_id: str or int, bonus_request_id: str, bonus_id: str):
    user = UserLogics.get_by_id(user_id) if isinstance(user_id, str) and not str(user_id).isdigit() else UserLogics.get_by_chat_id(user_id)
    if not user:
        return

    bonus_request = BonusRequestLogics.get_by_id(bonus_request_id)
    if not bonus_request:
        return

    bonus = BonusLogics.get_by_id(bonus_id)
    if not bonus:
        return

    bonus_user = UserLogics.get_by_id(bonus_request.user_id)
    if not bonus_user:
        return

    user_subscribed = await UserLogics.is_subscriber(bot=bot, chat_id=bonus_user.chat_id, user=bonus_user)

    if user.is_manager:
        bonus_group_icon = group_display_dict.get(bonus.group, [bonus.group])
        user_group_icon = group_display_dict.get(bonus_user.group, [bonus_user.group])
        country_display = bonus_user.country.name if bonus_user.country else "🌍 None"

        subscribed_text = '🟢 <b>Subscribed</b>' if user_subscribed else '🔴 <b>Not subscribed</b>'
        request_creation_date = f'<i>{bonus_request.created_at.strftime(DATETIME_FORMAT)}</i>'

        reject_reason_text = f"\n<b>❌ Reject Reason:</b> {bonus_request.reject_reason}" if bonus_request.reject_reason else ""
        request_text_data = (
            f"<b>📝 Request:</b> <i>{request_creation_date}</i>\n"
            f"<b>Status:</b> {bonus_request_icon_dict.get(bonus_request.status)}{reject_reason_text}\n\n"
            f"<b>{bonus_group_icon[0]} Bonus ID:</b> {bonus_id}\n"
            f"<b>📄 Bonus text:</b>\n{bonus.description}\n"
            f"<b>{user_group_icon[0]} User ID:</b> <code>{bonus_user.chat_id}</code>\n"
            f"<b>🌍 Country:</b> {country_display}\n"
            f"<b>🃏 Site ID / Nickname:</b> {bonus_user.site_id if bonus_user.site_id else 'No site ID / nickname provided!'}\n"
            f"{subscribed_text}"
        )
    else:
        reject_reason_text = f"\n<b>❌ Reason:</b> {bonus_request.reject_reason}" if bonus_request.status == BonusRequestStatuses.Canceled.value and bonus_request.reject_reason else ""
        request_text_data = (
            f"<b>🚀 Request is: {bonus_request_icon_dict.get(bonus_request.status)}</b>{reject_reason_text}\n\n"
            f"<b>🎁 Bonus:</b>\n{bonus.description}"
        )

    reply_markup = bonus_request_keyboard(
        bonus_request_id=bonus_request_id,
        is_manager=user.is_manager,
        request_is_active=bonus_request.status == BonusRequestStatuses.Active.value,
        user_id=bonus_request.user_id,
        bonus_id=bonus_id
    )

    if bonus.photo_url:
        try:
            await bot.send_photo(
                chat_id=int(user.chat_id),
                photo=bonus.photo_url,
                caption=request_text_data,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            return
        except Exception as e:
            logging.warning(f"Failed to send bonus request photo {bonus.photo_url} to {user.chat_id}: {e}")

    try:
        await bot.send_message(
            chat_id=int(user.chat_id),
            text=request_text_data,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception as e:
        logging.error(f"Failed to send bonus request message to {user.chat_id}: {e}")
        try:
            await bot.send_message(
                chat_id=int(user.chat_id),
                text=bonus.description,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
        except Exception as e2:
            logging.error(f"Failed fallback bonus request message to {user.chat_id}: {e2}")


@dp.callback_query_handler(bonus_already_requested_callback.filter(), UserFilter())
async def process_bonus_already_requested(call: types.CallbackQuery, callback_data: dict):
    bonus_id = callback_data.get('bonus_id')
    bonus = BonusLogics.get_by_id(bonus_id)
    if not bonus:
        return

    user = UserLogics.get_by_chat_id(call.from_user.id)
    if not user:
        return

    all_requests = BonusRequestLogics.get_list(user_id=user.id, bonus_id=bonus.id)
    active_or_approved = [
        r for r in all_requests
        if r.status in (BonusRequestStatuses.Active.value, BonusRequestStatuses.Approved.value)
    ]
    if not active_or_approved:
        from bot.handlers.bonus import _send_bonus_info
        await call.message.delete()
        await _send_bonus_info(user_id=user.chat_id, bonus_id=bonus.id, is_requested=False)
        return

    bonus_request = active_or_approved[0]
    await call.message.answer(
        f"A request for this bonus already exists 🏁\nCheck the status in {DefaultKeyboardButtons.BonusRequests.value}"
    )
    await sleep(0.2)
    await call.message.delete()
    await _send_bonus_request_info(
        user_id=bonus_request.user_id,
        bonus_id=bonus_request.bonus_id,
        bonus_request_id=bonus_request.id
    )


@dp.callback_query_handler(bonus_requests_page_callback.filter())
async def process_bonus_requests_pagination(call: types.CallbackQuery, callback_data: dict):
    page = int(callback_data["page"])
    user = UserLogics.get_by_chat_id(call.from_user.id)
    await send_bonus_requests_page(call=call, user=user, page=page)
    await call.answer()


async def send_bonus_requests_page(message=None, call=None, user=None, page=1):
    bonus_requests, total = get_paginated_bonus_requests(user, page)
    target = call.message if call else message

    if not bonus_requests:
        await target.answer(f"Check available bonuses in {DefaultKeyboardButtons.Bonuses.value}")
        return

    for request in bonus_requests:
        await _send_bonus_request_info(
            user_id=request.user_id,
            bonus_id=request.bonus_id,
            bonus_request_id=request.id
        )
        await sleep(0.2)

    await target.answer(
        text=f"Page {page} / {(total + BONUS_REQUESTS_PER_PAGE - 1) // BONUS_REQUESTS_PER_PAGE}",
        reply_markup=bonus_requests_navigation_keyboard(page=page, total=total)
    )


@dp.message_handler(Text(DefaultKeyboardButtons.BonusRequests.value), UserFilter())
async def process_open_my_bonus_requests(message: types.Message):
    user = UserLogics.get_by_chat_id(message.from_user.id)
    await send_bonus_requests_page(message=message, user=user, page=1)


def get_paginated_bonus_requests(user, page: int):
    if user.is_manager:
        all_requests = BonusRequestLogics.get_list()
    else:
        all_requests = BonusRequestLogics.get_list(user_id=user.id)

    total = len(all_requests)
    start = (page - 1) * BONUS_REQUESTS_PER_PAGE
    end = start + BONUS_REQUESTS_PER_PAGE
    return all_requests[start:end], total


@dp.callback_query_handler(refresh_bonus_request_callback.filter(), UserFilter())
async def process_refresh_bonus_request(call: types.CallbackQuery, callback_data: dict):
    bonus_request_id = callback_data.get('bonus_request_id')
    bonus_request = BonusRequestLogics.get_by_id(bonus_request_id)
    if not bonus_request:
        await call.message.answer("Request not found")
        return

    await sleep(0.2)
    await call.message.delete()
    await _send_bonus_request_info(
        user_id=bonus_request.user_id,
        bonus_id=bonus_request.bonus_id,
        bonus_request_id=bonus_request.id
    )


@dp.callback_query_handler(activate_bonus_request_callback.filter(), UserFilter(only_managers=True))
async def process_activate_bonus_request(call: types.CallbackQuery, callback_data: dict):
    await call.message.delete()
    bonus_request_id = callback_data.get('bonus_request_id')
    await call.message.answer(
        "Are you sure you want to activate the request? 👉",
        reply_markup=activate_bonus_request_confirmation_keyboard(bonus_request_id=bonus_request_id)
    )


@dp.callback_query_handler(activate_br_approve_callback.filter(), UserFilter(only_managers=True))
async def process_activate_br_approve(call: types.CallbackQuery, callback_data: dict):
    bonus_request_id = callback_data.get('bonus_request_id')
    bonus_request = BonusRequestLogics.get_by_id(bonus_request_id)
    user = UserLogics.get_by_chat_id(call.from_user.id)
    try:
        BonusRequestLogics.activate(bonus_request)
        await call.message.answer('The request has been activated 🥳', reply_markup=manage_keyboard())
    except BonusAlreadyActivatedError:
        await call.message.answer("Ups, the request is already active 🤭", reply_markup=manage_keyboard())

    await call.message.delete()
    await sleep(0.2)
    await _send_bonus_request_info(
        user_id=user.id,
        bonus_id=bonus_request.bonus_id,
        bonus_request_id=bonus_request.id
    )


@dp.callback_query_handler(activate_br_cancel_callback.filter(), UserFilter(only_managers=True))
async def process_activate_br_cancel(call: types.CallbackQuery, callback_data: dict):
    bonus_request_id = callback_data.get('bonus_request_id')
    bonus_request = BonusRequestLogics.get_by_id(bonus_request_id)
    user = UserLogics.get_by_chat_id(call.from_user.id)
    await call.message.answer("Huh, the request was not activated 😌", reply_markup=manage_keyboard())
    await call.message.delete()
    await sleep(0.2)
    await _send_bonus_request_info(
        user_id=user.id,
        bonus_id=bonus_request.bonus_id,
        bonus_request_id=bonus_request.id
    )


@dp.callback_query_handler(cancel_bonus_request_callback.filter(), UserFilter(only_managers=True))
async def process_cancel_bonus_request(call: types.CallbackQuery, callback_data: dict):
    bonus_request_id = callback_data.get('bonus_request_id')
    markup = cancel_bonus_request_options_keyboard(bonus_request_id=bonus_request_id)
    await call.message.delete()
    await call.message.answer(
        "Select reject reason to cancel the request? 👉",
        reply_markup=markup
    )


@dp.callback_query_handler(cancel_br_approve_callback.filter(), UserFilter(only_managers=True))
async def process_cancel_br_approve(call: types.CallbackQuery, callback_data: dict):
    bonus_request_id = callback_data.get('bonus_request_id')
    bonus_request = BonusRequestLogics.get_by_id(bonus_request_id)
    user = UserLogics.get_by_chat_id(call.from_user.id)
    user_chat_id = bonus_request.user.chat_id
    canceled = False
    reason_text = "Your request was rejected."
    try:
        BonusRequestLogics.cancel(bonus_request, reject_reason=reason_text)
        canceled = True
        await call.message.answer('The request has been canceled ❌', reply_markup=manage_keyboard())
        await bot.send_message(
            chat_id=int(user_chat_id),
            text=f"⚠️ Your bonus request status is: {bonus_request_icon_dict.get(BonusRequestStatuses.Canceled.value)}\n"
                 f"<i>Reason: {reason_text}</i>",
            parse_mode="HTML"
        )
    except BonusAlreadyCanceledError:
        await call.message.answer("Ups, the request is already canceled 🤭", reply_markup=manage_keyboard())

    await call.message.delete()
    await sleep(0.2)
    await _send_bonus_request_info(
        user_id=user.id,
        bonus_id=bonus_request.bonus_id,
        bonus_request_id=bonus_request.id
    )
    if canceled:
        await sleep(0.2)
        await _send_bonus_request_info(
            user_id=user_chat_id,
            bonus_id=bonus_request.bonus_id,
            bonus_request_id=bonus_request.id
        )


@dp.callback_query_handler(cancel_br_approve_opt_callback.filter(), UserFilter(only_managers=True))
async def process_cancel_br_approve_opt(call: types.CallbackQuery, callback_data: dict):
    bonus_request_id = callback_data.get('bonus_request_id')
    reject_reason = callback_data.get('reject_reason')
    bonus_request = BonusRequestLogics.get_by_id(bonus_request_id)
    user = UserLogics.get_by_chat_id(call.from_user.id)
    user_chat_id = bonus_request.user.chat_id
    canceled = False
    reason_text = get_reject_reason_text(reject_reason)
    try:
        BonusRequestLogics.cancel(bonus_request, reject_reason=reason_text)
        canceled = True
        await call.message.answer('The request has been canceled ❌', reply_markup=manage_keyboard())
        await bot.send_message(
            chat_id=int(user_chat_id),
            text=f"⚠️ Your bonus request status is: {bonus_request_icon_dict.get(BonusRequestStatuses.Canceled.value)}\n"
                 f"<i>Reason: {reason_text}</i>",
            parse_mode="HTML"
        )
    except BonusAlreadyCanceledError:
        await call.message.answer("Ups, the request is already canceled 🤭", reply_markup=manage_keyboard())

    await call.message.delete()
    await sleep(0.2)
    await _send_bonus_request_info(
        user_id=user.id,
        bonus_id=bonus_request.bonus_id,
        bonus_request_id=bonus_request.id
    )
    if canceled:
        await sleep(0.2)
        await _send_bonus_request_info(
            user_id=user_chat_id,
            bonus_id=bonus_request.bonus_id,
            bonus_request_id=bonus_request.id
        )


@dp.callback_query_handler(cancel_br_cancel_callback.filter(), UserFilter(only_managers=True))
async def process_cancel_br_cancel(call: types.CallbackQuery, callback_data: dict):
    bonus_request_id = callback_data.get('bonus_request_id')
    bonus_request = BonusRequestLogics.get_by_id(bonus_request_id)
    user = UserLogics.get_by_chat_id(call.from_user.id)
    await call.message.answer("Huh, the request was not canceled 😌", reply_markup=manage_keyboard())
    await call.message.delete()
    await sleep(0.2)
    await _send_bonus_request_info(
        user_id=user.id,
        bonus_id=bonus_request.bonus_id,
        bonus_request_id=bonus_request.id
    )


@dp.callback_query_handler(approve_bonus_request_callback.filter(), UserFilter(only_managers=True))
async def process_approve_bonus_request(call: types.CallbackQuery, callback_data: dict):
    await call.message.delete()
    bonus_request_id = callback_data.get('bonus_request_id')
    await call.message.answer(
        "Are you sure you want to approve the request? 👉",
        reply_markup=approve_bonus_request_confirmation_keyboard(bonus_request_id=bonus_request_id)
    )


@dp.callback_query_handler(approve_br_approve_callback.filter(), UserFilter(only_managers=True))
async def process_approve_br_approve(call: types.CallbackQuery, callback_data: dict):
    bonus_request_id = callback_data.get('bonus_request_id')
    bonus_request = BonusRequestLogics.get_by_id(bonus_request_id)
    user = UserLogics.get_by_chat_id(call.from_user.id)
    user_chat_id = bonus_request.user.chat_id
    try:
        BonusRequestLogics.approve(bonus_request)
        await call.message.answer('The request has been approved 🥳', reply_markup=manage_keyboard())
        await bot.send_message(
            chat_id=int(user_chat_id),
            text=f"🎉 Your bonus request status is: {bonus_request_icon_dict.get(BonusRequestStatuses.Approved.value)}"
        )
    except BonusAlreadyApprovedError:
        await call.message.answer("Ups, the request is already approved 🤭", reply_markup=manage_keyboard())

    await call.message.delete()
    await sleep(0.5)
    await _send_bonus_request_info(
        user_id=user.id,
        bonus_id=bonus_request.bonus_id,
        bonus_request_id=bonus_request.id
    )
    await sleep(0.2)
    await _send_bonus_request_info(
        user_id=user_chat_id,
        bonus_id=bonus_request.bonus_id,
        bonus_request_id=bonus_request.id
    )


@dp.callback_query_handler(approve_br_cancel_callback.filter(), UserFilter(only_managers=True))
async def process_approve_br_cancel(call: types.CallbackQuery, callback_data: dict):
    bonus_request_id = callback_data.get('bonus_request_id')
    bonus_request = BonusRequestLogics.get_by_id(bonus_request_id)
    user = UserLogics.get_by_chat_id(call.from_user.id)
    await call.message.answer("Huh, the request was not approved 😌", reply_markup=manage_keyboard())
    await call.message.delete()
    await sleep(0.5)
    await _send_bonus_request_info(
        user_id=user.id,
        bonus_id=bonus_request.bonus_id,
        bonus_request_id=bonus_request.id
    )


@dp.callback_query_handler(request_bonus_callback.filter(), UserFilter())
async def process_request_bonus(call: types.CallbackQuery, callback_data: dict):
    bonus_id = callback_data.get('bonus_id')
    bonus = BonusLogics.get_by_id(bonus_id)
    if not bonus:
        await call.message.answer("The bonus is no longer active 🕰️", reply_markup=main_menu_keyboard())
        return

    user = UserLogics.get_by_chat_id(call.from_user.id)
    if not user:
        return

    bonus_requests = BonusRequestLogics.get_list(user_id=user.id, bonus_id=bonus_id)
    active_or_approved = [
        r for r in bonus_requests
        if r.status in (BonusRequestStatuses.Active.value, BonusRequestStatuses.Approved.value)
    ]
    if active_or_approved:
        bonus_request = active_or_approved[0]
        if bonus_request.status == BonusRequestStatuses.Approved.value:
            await call.message.answer("This bonus has already been claimed by your account ✅", reply_markup=main_menu_keyboard())
        else:
            await call.message.answer("A request for this bonus already exists 🏁", reply_markup=main_menu_keyboard())
        await sleep(0.2)
        await call.message.delete()
        await _send_bonus_request_info(
            user_id=bonus_request.user_id,
            bonus_id=bonus_request.bonus_id,
            bonus_request_id=bonus_request.id
        )
        return

    # Check user subscription
    user_subscribed = await UserLogics.is_subscriber(bot=bot, chat_id=user.chat_id, user=user)
    if not user_subscribed:
        channel_url = (user.country.channel_url if user.country and user.country.channel_url else COMMUNITY_URL) or "https://t.me"
        await call.message.answer(
            f"Subscribe to our 👉 <a href='{channel_url}'>CHANNEL</a> to request the Bonus 📰",
            reply_markup=main_menu_keyboard(),
            disable_web_page_preview=True,
            parse_mode="HTML"
        )
        return

    if not user.site_id:
        reg_link = f"<a href='{REGISTRATION_URL}'>HERE</a>" if REGISTRATION_URL else "Registration"
        await call.message.answer(
            f"Enter your Site ID or Nickname in {DefaultKeyboardButtons.Profile.value} from {reg_link} to request the Bonus",
            reply_markup=main_menu_keyboard(),
            disable_web_page_preview=True,
            parse_mode="HTML"
        )
        return

    # Check bonus active
    if not bonus.is_active or bonus.is_removed:
        await call.message.answer("The bonus is no longer active 🕰️", reply_markup=main_menu_keyboard())
        await sleep(0.2)
        await call.message.delete()
        return

    # Check country access
    if bonus.country and user.country and bonus.country.id != user.country.id:
        await call.message.answer("This bonus is not available for your country 🔒", reply_markup=main_menu_keyboard())
        await sleep(0.2)
        await call.message.delete()
        return

    # Check group access
    if bonus.group != Groups.All.value and user.group != bonus.group:
        await call.message.answer("This bonus is not available for your group 🔒", reply_markup=main_menu_keyboard())
        await sleep(0.2)
        await call.message.delete()
        return

    new_bonus_request = BonusRequestLogics.create(user_id=user.id, bonus_id=bonus_id)
    await call.message.answer("The bonus request has been successfully created ✅", reply_markup=main_menu_keyboard())
    await _send_bonus_request_info(
        user_id=new_bonus_request.user_id,
        bonus_id=new_bonus_request.bonus_id,
        bonus_request_id=new_bonus_request.id
    )
    await sleep(0.2)
    await call.message.delete()
