from aiogram import executor
from bot import middlewares, filters
from bot.handlers.manage import process_scheduled_messages
from bot.utils.set_bot_commands import set_default_commands
from bot.utils.notify_admins import on_startup_notify
import asyncio
from config import SCHEDULED_MESSAGE_CHECK_FREQUENCY_MIN


async def scheduler():
    while True:
        try:
            await process_scheduled_messages()
        except Exception as e:
            print(f"[Scheduler Error] {e}")
        await asyncio.sleep(60 * SCHEDULED_MESSAGE_CHECK_FREQUENCY_MIN)


async def _on_startup(dp):
    filters.setup(dp)
    middlewares.setup(dp)

    await set_default_commands(dp)
    await on_startup_notify(dp)
    asyncio.create_task(scheduler())


def run_bot():
    from bot.handlers import dp
    executor.start_polling(dp, on_startup=_on_startup)
