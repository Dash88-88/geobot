from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Command, Text
from bot.filters import UserFilter
from bot.keyboards.inline import invite_keyboard, share_keyboard
from bot.loader import dp
from common.constants import DefaultKeyboardButtons, InlineQueryTypes
from config import RESOURCE_NAME, BOT_ADMINS
from logics import UserLogics

REFERRAL_LINK_TEMPLATE = "https://t.me/%s?start=%s"


def _get_referral_link(bot_username: str, arg: str):
    return REFERRAL_LINK_TEMPLATE % (bot_username, arg)


@dp.message_handler(Command(["invite", "ref", "referral"]), UserFilter(), state="*")
@dp.message_handler(
    Text([
        DefaultKeyboardButtons.Invite.value,
        "📨 Refer a friend",
        "Refer a friend",
        "Invite"
    ], ignore_case=True),
    UserFilter(),
    state="*"
)
async def process_invite(message: types.Message, state: FSMContext = None):
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

    referral_link = _get_referral_link((await message.bot.get_me()).username, user.id)

    await message.answer(
        "👉 Invite a friend by sharing your referral link, or click the button below. 🙂\n\n"
        f"<i>Your referral link:</i> {referral_link}",
        reply_markup=share_keyboard()
    )


@dp.inline_handler(UserFilter(), text="")
@dp.inline_handler(UserFilter(), text=InlineQueryTypes.Invite.value)
async def share_query(query: types.InlineQuery):
    user = UserLogics.get_by_chat_id(query.from_user.id)
    if not user:
        user = UserLogics.create(
            chat_id=query.from_user.id,
            username=query.from_user.username,
            nickname=query.from_user.username or query.from_user.first_name or str(query.from_user.id),
            site_id='',
            is_manager=bool(query.from_user.id in BOT_ADMINS)
        )

    referral_link = _get_referral_link((await query.bot.get_me()).username, user.id)

    await query.answer(
        results=[
            types.InlineQueryResultArticle(
                id="1",
                title="Send your referral link to: ",
                reply_markup=invite_keyboard(referral_link),
                input_message_content=types.InputTextMessageContent(
                    message_text=f"<b>💎 {RESOURCE_NAME} | Your Bonus Assistant!</b>\n{referral_link}",
                    parse_mode="HTML",
                )
            )
        ],
        cache_time=5
    )
