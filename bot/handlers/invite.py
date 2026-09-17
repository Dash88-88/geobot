from aiogram import types
from aiogram.dispatcher.filters import Text
from bot.filters import UserFilter
from bot.keyboards.inline import invite_keyboard, share_keyboard
from bot.loader import dp
from common.constants import DefaultKeyboardButtons, InlineQueryTypes
from config import RESOURCE_NAME
from logics import UserLogics

REFERRAL_LINK_TEMPLATE = "https://t.me/%s?start=%s"


def _get_referral_link(bot_username: str, arg: str):
    return REFERRAL_LINK_TEMPLATE % (bot_username, arg)


@dp.message_handler(Text(DefaultKeyboardButtons.Invite.value), UserFilter())
async def process_invite(message: types.Message):
    user = UserLogics.get_by_chat_id(message.from_user.id)
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
