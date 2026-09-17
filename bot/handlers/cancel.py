from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram import types
from bot.keyboards.default import main_menu_keyboard, manage_keyboard
from bot.loader import dp
from common.constants import CallbackQueryTypes, DefaultKeyboardButtons
from logics import UserLogics


@dp.message_handler(Text(DefaultKeyboardButtons.Cancel.value), state="*")
@dp.callback_query_handler(text=CallbackQueryTypes.Cancel.value, state='*')
async def cancel_from_callback(update: types.Message or types.CallbackQuery, state: FSMContext):
    if state:
        await state.finish()

    if isinstance(update, types.Message):
        message = update
        user = UserLogics.get_by_chat_id(message.from_user.id)
        keyboard = manage_keyboard() if user and user.is_manager else main_menu_keyboard()
        await message.answer("Action canceled.", reply_markup=keyboard)
    elif isinstance(update, types.CallbackQuery):
        user = UserLogics.get_by_chat_id(update.from_user.id)
        keyboard = manage_keyboard() if user and user.is_manager else main_menu_keyboard()
        await update.message.answer("Action canceled.", reply_markup=keyboard)
        await update.message.delete()
        await update.answer()
