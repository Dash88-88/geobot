import html
import logging
from asyncio import sleep

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, Command
from aiogram.types import ContentType
from bot.filters import UserFilter
from bot.keyboards.callback_datas import (
    view_bonus_callback,
    enable_bonus_callback,
    disable_bonus_callback,
    set_bonus_all_callback,
    set_bonus_vip_callback,
    set_bonus_negative_callback,
    set_bonus_neutral_callback,
    set_bonus_positive_callback,
    group_display_dict,
    update_bonus_description_callback,
    update_bonus_image_url_callback,
    delete_bonus_callback,
    bonuses_page_callback,
    delete_bonus_approve_callback,
    delete_bonus_cancel_callback,
    set_bonus_not_for_request_callback,
    set_bonus_for_request_callback,
    set_bonus_for_request_cancel_callback,
    set_bonus_for_request_approve_callback,
    set_bonus_not_for_request_cancel_callback,
    set_bonus_not_for_request_approve_callback,
    enable_bonus_approve_callback,
    enable_bonus_cancel_callback,
    disable_bonus_cancel_callback,
    disable_bonus_approve_callback,
    change_bonus_group_callback,
    change_bonus_group_cancel_callback,
)
from bot.keyboards.default import cancel_keyboard, manage_keyboard
from bot.keyboards.inline import (
    bonus_keyboard,
    bonuses_navigation_keyboard,
    delete_bonus_confirmation_keyboard,
    set_bonus_is_for_request_confirmation_keyboard,
    set_bonus_is_not_for_request_confirmation_keyboard,
    enable_bonus_confirmation_keyboard,
    disable_bonus_confirmation_keyboard,
    change_bonus_group_keyboard,
)
from bot.loader import dp, bot
from bot.states import UpdateBonusDescription, UpdateBonusImageURL
from common.constants import DefaultInlineButtons, Groups, DefaultKeyboardButtons, BonusRequestStatuses
from common.exceptions import (
    BonusAlreadyEnabledError,
    BonusAlreadyDisabledError,
    BonusAlreadyNegativeError,
    BonusAlreadyAllError,
    BonusAlreadyNeutralError,
    BonusAlreadyPositiveError,
    BonusAlreadyVipError,
    BonusAlreadyRemovedError,
    BonusAlreadyRequestError,
    BonusAlreadyNotRequestError,
)
from common.utils import is_pure_image_url, is_url
from config import BONUSES_PER_PAGE
from logics import UserLogics, BonusLogics, BonusRequestLogics
from models import Bonus


@dp.channel_post_handler()
async def handle_channel_post(message: types.Message):
    logging.debug(f"Channel ID is: {message.chat.id}")


async def _send_bonus_info(user_id: str or int, bonus_id: str, is_requested: bool = False):
    user = UserLogics.get_by_chat_id(user_id)
    if not user:
        return

    bonus = BonusLogics.get_by_id(bonus_id)
    if not bonus or bonus.is_removed:
        return

    country_display = bonus.country.name if bonus.country else "🌍 All Countries"

    if user.is_manager:
        if bonus.photo_url:
            if bonus.photo_url.startswith(('http://', 'https://')):
                bonus_image_url_link = f"<a href='{html.escape(bonus.photo_url)}'>THE LINK</a>"
            else:
                bonus_image_url_link = "Attached photo 🖼️"
        else:
            bonus_image_url_link = "None"

        is_for_request_text = "Could be requested ⚙️💌" if bonus.is_request else "For info! No requests! ⚙️🪧"

        bonus_text_data = (
            f"<b>Description</b>: {bonus.description}\n"
            f"<b>Group</b>: {group_display_dict.get(bonus.group, [bonus.group])[0]}, {bonus.group}\n"
            f"<b>Country</b>: {country_display}\n"
            f"<b>Request-able</b>: {is_for_request_text}\n"
            f"<b>Image URL</b>: {bonus_image_url_link}"
        )

        if bonus.is_request:
            all_statuses_requests = BonusRequestLogics.get_list(bonus_id=bonus_id)
            canceled_requests = len([r for r in all_statuses_requests if r.status == BonusRequestStatuses.Canceled.value])
            waiting_requests = len([r for r in all_statuses_requests if r.status == BonusRequestStatuses.Active.value])
            approved_requests = len([r for r in all_statuses_requests if r.status == BonusRequestStatuses.Approved.value])

            bonus_text_data += f"\n<b>Requests</b>: ⏰: {waiting_requests}, ❌: {canceled_requests}, ✅: {approved_requests}"
    else:
        bonus_text_data = f"{bonus.description}"

    reply_markup = bonus_keyboard(
        bonus_id=bonus_id,
        is_for_request=bonus.is_request,
        is_bonus_active=bonus.is_active,
        current_group=bonus.group,
        is_manager=user.is_manager,
        is_requested=is_requested
    )

    if bonus.photo_url:
        try:
            await bot.send_photo(
                chat_id=int(user.chat_id),
                photo=bonus.photo_url,
                caption=bonus_text_data,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            return
        except Exception as e:
            logging.warning(f"Failed to send bonus photo {bonus.photo_url} to {user.chat_id}: {e}")

    try:
        await bot.send_message(
            chat_id=int(user.chat_id),
            text=bonus_text_data,
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        logging.error(f"Failed to send bonus message to {user.chat_id}: {e}")
        try:
            await bot.send_message(
                chat_id=int(user.chat_id),
                text=bonus.description,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
        except Exception as e2:
            logging.error(f"Failed fallback bonus message to {user.chat_id}: {e2}")



@dp.callback_query_handler(view_bonus_callback.filter(), UserFilter(), state="*")
async def process_view_bonus(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get('bonus_id')
    bonus = BonusLogics.get_by_id(bonus_id)
    if not bonus or bonus.is_removed:
        await call.answer("Bonus not found or removed", show_alert=True)
        return
    await _send_bonus_info(call.from_user.id, bonus_id)


def get_paginated_bonuses(user, page: int):
    if user.is_manager:
        all_bonuses = BonusLogics.get_list(is_removed=False)
    else:
        country_id = user.country.id if user.country else None
        all_bonuses = BonusLogics.get_list(is_active=True, is_removed=False, country_id=country_id, for_user=True)
        all_bonuses = [bonus for bonus in all_bonuses if bonus.group == user.group or bonus.group == Groups.All.value]

    total = len(all_bonuses)
    start = (page - 1) * BONUSES_PER_PAGE
    end = start + BONUSES_PER_PAGE
    return all_bonuses[start:end], total


async def send_bonuses_page(message=None, call=None, user=None, page=1):
    bonuses, total = get_paginated_bonuses(user, page)

    target = call.message if call else message
    if not bonuses:
        if user and user.is_manager:
            await target.answer("No bonuses found in database 🔍\nYou can create one using <b>🎁 Create Bonus</b>.", parse_mode="HTML")
        else:
            await target.answer("Waiting for new bonuses 👓")
        return

    for bonus in bonuses:
        is_requested = bool(len([r for r in BonusRequestLogics.get_list(user_id=user.id, bonus_id=bonus.id) if r.status in (BonusRequestStatuses.Active.value, BonusRequestStatuses.Approved.value)]))
        await _send_bonus_info(
            user_id=user.chat_id,
            bonus_id=bonus.id,
            is_requested=is_requested
        )
        await sleep(0.2)

    await target.answer(
        text=f"Page {page} / {(total + BONUSES_PER_PAGE - 1) // BONUSES_PER_PAGE}",
        reply_markup=bonuses_navigation_keyboard(page=page, total=total)
    )


@dp.message_handler(Command(["bonuses", "all_bonuses"]), UserFilter(), state="*")
@dp.message_handler(
    Text([
        DefaultKeyboardButtons.Bonuses.value,
        DefaultKeyboardButtons.AllBonuses.value,
        "🎁 Bonuses",
        "Bonuses",
        "🔍 All Bonuses",
        "🔍 🎁"
    ], ignore_case=True),
    UserFilter(),
    state="*"
)
async def process_open_my_bonuses(message: types.Message, state: FSMContext = None):
    if state:
        await state.finish()
    user = UserLogics.get_by_chat_id(message.from_user.id)
    await send_bonuses_page(message=message, user=user, page=1)


@dp.callback_query_handler(bonuses_page_callback.filter(), state="*")
async def process_bonuses_pagination(call: types.CallbackQuery, callback_data: dict):
    page = int(callback_data["page"])
    user = UserLogics.get_by_chat_id(call.from_user.id)
    await send_bonuses_page(call=call, user=user, page=page)
    await call.answer()


@dp.callback_query_handler(change_bonus_group_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_change_bonus_group_callback(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    bonus_id = callback_data.get('bonus_id')
    bonus = BonusLogics.get_by_id(bonus_id)
    if not bonus or bonus.is_removed:
        await call.answer("Bonus not found", show_alert=True)
        return

    await state.update_data(bonus_id=bonus_id)
    group_icon = group_display_dict.get(bonus.group, ['🟩'])[0]
    await call.message.answer(
        f"Select new group for the bonus (Current: {group_icon} <b>{bonus.group}</b>):",
        reply_markup=change_bonus_group_keyboard(bonus_id=bonus_id, current_group=bonus.group),
        parse_mode="HTML"
    )
    await call.message.delete()


@dp.callback_query_handler(change_bonus_group_cancel_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_change_bonus_group_cancel_callback(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get("bonus_id")
    await call.message.answer("Bonus group was not changed 😌", reply_markup=manage_keyboard())
    await _send_bonus_info(call.from_user.id, bonus_id)
    await call.message.delete()
    await sleep(0.5)


@dp.callback_query_handler(enable_bonus_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_enable_bonus(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    bonus_id = callback_data.get('bonus_id')
    await state.update_data(bonus_id=bonus_id)
    await call.message.answer("Are you sure you want to enable the bonus? ⚠️",
                              reply_markup=enable_bonus_confirmation_keyboard(bonus_id=bonus_id))
    await call.message.delete()


@dp.callback_query_handler(enable_bonus_cancel_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_enable_bonus_cancel(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get("bonus_id")
    await call.message.answer("Bonus was not enabled 😌", reply_markup=manage_keyboard())
    await _send_bonus_info(call.from_user.id, bonus_id)
    await call.message.delete()
    await sleep(0.5)


@dp.callback_query_handler(enable_bonus_approve_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_enable_bonus_approve(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get("bonus_id")
    bonus = BonusLogics.get_by_id(bonus_id)
    try:
        BonusLogics.enable(bonus)
        await call.answer('The bonus has been enabled! 🟢', show_alert=True)
    except BonusAlreadyEnabledError:
        await call.answer("Ups, the bonus already has been enabled 🤭", show_alert=True)

    await call.message.delete()
    await process_view_bonus(call, {"bonus_id": bonus_id})


@dp.callback_query_handler(disable_bonus_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_disable_bonus(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    bonus_id = callback_data.get('bonus_id')
    await state.update_data(bonus_id=bonus_id)
    await call.message.answer("Are you sure you want to disable the bonus? ⚠️",
                              reply_markup=disable_bonus_confirmation_keyboard(bonus_id=bonus_id))
    await call.message.delete()


@dp.callback_query_handler(disable_bonus_cancel_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_disable_bonus_cancel(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get("bonus_id")
    await call.message.answer("Bonus was not disabled 😌", reply_markup=manage_keyboard())
    await _send_bonus_info(call.from_user.id, bonus_id)
    await call.message.delete()
    await sleep(0.5)


@dp.callback_query_handler(disable_bonus_approve_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_disable_bonus_approve(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get("bonus_id")
    bonus = BonusLogics.get_by_id(bonus_id)
    try:
        BonusLogics.disable(bonus)
        await call.answer('The bonus has been disabled! 🔴', show_alert=True)
    except BonusAlreadyDisabledError:
        await call.answer("Ups, the bonus already has been disabled 🤭", show_alert=True)

    await call.message.delete()
    await process_view_bonus(call, {"bonus_id": bonus_id})


@dp.callback_query_handler(set_bonus_all_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_set_bonus_all(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get('bonus_id')
    bonus = BonusLogics.get_by_id(bonus_id)
    try:
        BonusLogics.set_group_all(bonus)
        await call.answer(f'The bonus has been set to {DefaultInlineButtons.AllBonus.value} {Groups.All.value} group!', show_alert=True)
    except BonusAlreadyAllError:
        await call.answer(f"Ups, the bonus group is already {DefaultInlineButtons.AllBonus.value} {Groups.All.value} 🤭", show_alert=True)

    await call.message.delete()
    await process_view_bonus(call, {"bonus_id": bonus_id})


@dp.callback_query_handler(set_bonus_negative_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_set_bonus_negative(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get('bonus_id')
    bonus = BonusLogics.get_by_id(bonus_id)
    try:
        BonusLogics.set_group_negative(bonus)
        await call.answer(f'The bonus has been set to {DefaultInlineButtons.NegativeBonus.value} {Groups.Negative.value} group!', show_alert=True)
    except BonusAlreadyNegativeError:
        await call.answer(f"Ups, the bonus group is already {DefaultInlineButtons.NegativeBonus.value} {Groups.Negative.value} 🤭", show_alert=True)

    await call.message.delete()
    await process_view_bonus(call, {"bonus_id": bonus_id})


@dp.callback_query_handler(set_bonus_neutral_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_set_bonus_neutral(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get('bonus_id')
    bonus = BonusLogics.get_by_id(bonus_id)
    try:
        BonusLogics.set_group_neutral(bonus)
        await call.answer(f'The bonus has been set to {DefaultInlineButtons.NeutralBonus.value} {Groups.Neutral.value} group!', show_alert=True)
    except BonusAlreadyNeutralError:
        await call.answer(f"Ups, the bonus group is already {DefaultInlineButtons.NeutralBonus.value} {Groups.Neutral.value} 🤭", show_alert=True)

    await call.message.delete()
    await process_view_bonus(call, {"bonus_id": bonus_id})


@dp.callback_query_handler(set_bonus_positive_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_set_bonus_positive(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get('bonus_id')
    bonus = BonusLogics.get_by_id(bonus_id)
    try:
        BonusLogics.set_group_positive(bonus)
        await call.answer(f'The bonus has been set to {DefaultInlineButtons.PositiveBonus.value} {Groups.Positive.value} group!', show_alert=True)
    except BonusAlreadyPositiveError:
        await call.answer(f"Ups, the bonus group is already {DefaultInlineButtons.PositiveBonus.value} {Groups.Positive.value} 🤭", show_alert=True)

    await call.message.delete()
    await process_view_bonus(call, {"bonus_id": bonus_id})


@dp.callback_query_handler(set_bonus_vip_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_set_bonus_vip(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get('bonus_id')
    bonus = BonusLogics.get_by_id(bonus_id)
    try:
        BonusLogics.set_group_vip(bonus)
        await call.answer(f'The bonus has been set to {DefaultInlineButtons.VIPBonus.value} {Groups.Vip.value} group!', show_alert=True)
    except BonusAlreadyVipError:
        await call.answer(f"Ups, the bonus group is already {DefaultInlineButtons.VIPBonus.value} {Groups.Vip.value} 🤭", show_alert=True)

    await call.message.delete()
    await process_view_bonus(call, {"bonus_id": bonus_id})


@dp.callback_query_handler(update_bonus_description_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_update_bonus_description(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    bonus_id = callback_data.get("bonus_id")
    await state.update_data(bonus_id=bonus_id)
    await call.message.answer("📝 Enter new bonus description (&lt;1000 symbols) 👉:", reply_markup=cancel_keyboard(), parse_mode="HTML")
    await call.message.delete()
    await UpdateBonusDescription.send_bonus_description.set()


@dp.message_handler(UserFilter(only_managers=True), state=UpdateBonusDescription.send_bonus_description, content_types=(ContentType.ANY,))
async def process_confirm_bonus_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bonus_id = data.get("bonus_id")

    bonus = BonusLogics.get_by_id(bonus_id)
    if not bonus or bonus.is_removed:
        await state.finish()
        await message.answer("Bonus not found 🤷", reply_markup=manage_keyboard())
        return

    text = (message.text or message.caption or "").strip()
    if not text:
        await message.answer("⚠️ Please enter a text description for the bonus (or send /cancel):")
        return

    if is_pure_image_url(text):
        await message.answer(
            "⚠️ <b>Warning:</b> You entered an image URL instead of a text description.\n\n"
            "Please enter a text description for the bonus. You can attach an image URL separately using the 🖼️ Img button.",
            parse_mode="HTML"
        )
        return

    if len(text) > 1000:
        await message.answer("The bonus description must be 1000 characters or less 😉. Try again:")
        return

    await state.finish()
    bonus.description = text
    bonus.save(only=(Bonus.description,))
    await message.answer("The new bonus description was successfully saved 😉", reply_markup=manage_keyboard())
    await _send_bonus_info(message.from_user.id, bonus_id)


@dp.callback_query_handler(update_bonus_image_url_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_update_image_url(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    bonus_id = callback_data.get("bonus_id")
    await state.update_data(bonus_id=bonus_id)
    await call.message.answer(
        "🖼️ <b>Update Bonus Image</b>\n\n"
        "Enter the direct image <b>URL</b> (must start with <code>http://</code> or <code>https://</code>):\n"
        "<i>Example: https://example.com/image.jpg</i>\n\n"
        "<i>Send <code>-</code> to remove current image</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await call.message.delete()
    await UpdateBonusImageURL.send_bonus_image_url.set()


@dp.message_handler(UserFilter(only_managers=True), state=UpdateBonusImageURL.send_bonus_image_url, content_types=(ContentType.ANY,))
async def process_confirm_bonus_image_url(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bonus_id = data.get("bonus_id")

    bonus = BonusLogics.get_by_id(bonus_id)
    if not bonus or bonus.is_removed:
        await state.finish()
        await message.answer("Bonus not found 🤷", reply_markup=manage_keyboard())
        return

    # If admin sent a photo/document/video directly, warn that only URLs are accepted
    if message.photo or message.document or message.animation or message.video:
        await message.answer(
            "⚠️ <b>Only URLs are accepted:</b>\n"
            "Please send an image <b>URL link</b> (starting with <code>http://</code> or <code>https://</code>), "
            "or send <code>-</code> to remove the image.",
            parse_mode="HTML"
        )
        return

    raw_text = (message.text or "").strip()
    if not raw_text:
        await message.answer(
            "⚠️ Please send an image URL (starting with <code>http://</code> or <code>https://</code>), "
            "or send <code>-</code> to remove the image:",
            parse_mode="HTML"
        )
        return

    # Check for clearing
    if raw_text.lower() in ("-", "clear", "none", "del", "delete", "0"):
        await state.finish()
        bonus.photo_url = ""
        bonus.save(only=(Bonus.photo_url,))
        await message.answer("Bonus image removed successfully ✅", reply_markup=manage_keyboard())
        await _send_bonus_info(message.from_user.id, bonus_id)
        return

    if len(raw_text) > 500:
        await message.answer("The image URL is too long (max 500 characters). Try again:")
        return

    if not raw_text.startswith(('http://', 'https://')):
        await message.answer(
            "⚠️ <b>Invalid URL format:</b>\n"
            "The link must start with <code>http://</code> or <code>https://</code>\n"
            "<i>Example: https://example.com/image.jpg</i>\n\n"
            "Please try again or send <code>-</code> to remove the image.",
            parse_mode="HTML"
        )
        return

    # Verify if Telegram can load this image by attempting a test send
    test_msg = None
    try:
        test_msg = await bot.send_photo(
            chat_id=message.chat.id,
            photo=raw_text,
            caption="🔍 <i>Checking image link...</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.warning(f"Image URL verification failed for {raw_text}: {e}")
        await message.answer(
            "❌ <b>Telegram cannot load an image from this URL!</b>\n\n"
            "Possible reasons:\n"
            "• The link is a regular webpage, not a direct image file (.jpg/.png/.webp)\n"
            "• The website blocks Telegram's bot access\n"
            "• The link is broken or inaccessible\n\n"
            "Please enter a valid direct image URL or send <code>-</code> to cancel.",
            parse_mode="HTML"
        )
        return

    if test_msg:
        try:
            await test_msg.delete()
        except Exception:
            pass

    await state.finish()
    bonus.photo_url = raw_text
    bonus.save(only=(Bonus.photo_url,))
    await message.answer("The new bonus image URL was successfully verified and saved 😉", reply_markup=manage_keyboard())
    await _send_bonus_info(message.from_user.id, bonus_id)


@dp.callback_query_handler(delete_bonus_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_delete_bonus(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    bonus_id = callback_data.get("bonus_id")
    await state.update_data(bonus_id=bonus_id)
    await call.message.answer("Are you sure you want to remove the bonus? ⚠️",
                              reply_markup=delete_bonus_confirmation_keyboard(bonus_id=bonus_id))
    await call.message.delete()


@dp.callback_query_handler(delete_bonus_approve_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_delete_bonus_approve(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get("bonus_id")
    bonus = BonusLogics.get_by_id(bonus_id)
    try:
        BonusLogics.set_bonus_removed(bonus)
        await call.message.answer('The bonus has been removed 😈', reply_markup=manage_keyboard())
    except BonusAlreadyRemovedError:
        await call.message.answer("Ups, the bonus is already removed 🤭", reply_markup=manage_keyboard())

    await call.message.delete()
    await sleep(0.5)


@dp.callback_query_handler(delete_bonus_cancel_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_delete_bonus_cancel(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get("bonus_id")
    await call.message.answer("Huh, the bonus was not removed 😌", reply_markup=manage_keyboard())
    await _send_bonus_info(call.from_user.id, bonus_id)
    await call.message.delete()
    await sleep(0.5)


@dp.callback_query_handler(set_bonus_for_request_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_set_bonus_is_for_request(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    bonus_id = callback_data.get('bonus_id')
    await state.update_data(bonus_id=bonus_id)
    await call.message.answer("Are you sure you want to make the bonus requestable? ⚠️",
                              reply_markup=set_bonus_is_for_request_confirmation_keyboard(bonus_id=bonus_id))
    await call.message.delete()


@dp.callback_query_handler(set_bonus_for_request_cancel_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_set_bonus_for_request_cancel(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get("bonus_id")
    await call.message.answer("Huh, the bonus was not set for requests 😌", reply_markup=manage_keyboard())
    await _send_bonus_info(call.from_user.id, bonus_id)
    await call.message.delete()
    await sleep(0.5)


@dp.callback_query_handler(set_bonus_for_request_approve_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_set_bonus_for_request_approve(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get("bonus_id")
    bonus = BonusLogics.get_by_id(bonus_id)
    try:
        BonusLogics.set_as_request(bonus)
        await call.answer('The bonus is for requests now ⚙️💌', show_alert=True)
    except BonusAlreadyRequestError:
        await call.answer("Ups, the bonus already has been set for requests 🤭", show_alert=True)

    await call.message.delete()
    await process_view_bonus(call, {"bonus_id": bonus_id})


@dp.callback_query_handler(set_bonus_not_for_request_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_set_bonus_not_for_request(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    bonus_id = callback_data.get('bonus_id')
    await state.update_data(bonus_id=bonus_id)
    await call.message.answer("Are you sure you want to make the bonus for information only? ⚠️",
                              reply_markup=set_bonus_is_not_for_request_confirmation_keyboard(bonus_id=bonus_id))
    await call.message.delete()


@dp.callback_query_handler(set_bonus_not_for_request_cancel_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_set_bonus_not_for_request_cancel(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get("bonus_id")
    await call.message.answer("Huh, the bonus was not set for Info only 😌", reply_markup=manage_keyboard())
    await _send_bonus_info(call.from_user.id, bonus_id)
    await call.message.delete()
    await sleep(0.5)


@dp.callback_query_handler(set_bonus_not_for_request_approve_callback.filter(), UserFilter(only_managers=True), state="*")
async def process_set_bonus_not_for_request_approve(call: types.CallbackQuery, callback_data: dict, state: FSMContext = None):
    if state:
        await state.finish()
    bonus_id = callback_data.get("bonus_id")
    bonus = BonusLogics.get_by_id(bonus_id)
    try:
        BonusLogics.set_not_request(bonus)
        await call.answer('The bonus is for Info only now ⚙️🪧', show_alert=True)
    except BonusAlreadyNotRequestError:
        await call.answer("Ups, the bonus already has been set for Info 🤭", show_alert=True)

    await call.message.delete()
    await process_view_bonus(call, {"bonus_id": bonus_id})
