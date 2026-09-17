from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandHelp, Text
from bot.keyboards.default import main_menu_keyboard
from bot.keyboards.inline import bonus_transfer_inline_button_keyboard
from bot.loader import dp
from common.constants import DefaultKeyboardButtons


@dp.message_handler(CommandHelp())
async def process_faq(message: types.Message):
    await message.answer(
        "👋 <b>How to use the bot:</b>\n\n"
        "• <b>🎁 Bonuses:</b> View active promotions and request bonuses.\n"
        "• <b>🤴🏻 Profile:</b> View your account info, subscription status, and change your country.\n"
        "• <b>💬 Our Channel:</b> Join our official Telegram channel for updates.\n"
        "• <b>📨 Refer a friend:</b> Share your referral link with friends.",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )


@dp.message_handler(Text(DefaultKeyboardButtons.BonusTransfer.value))
async def process_bonus_transfer(message: types.Message):
    await message.answer("Claim your Welcome Bonus 👉",
                         reply_markup=bonus_transfer_inline_button_keyboard())
