import logging
from aiogram import Bot, types, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from common.constants import LOG_FORMAT
from config import BOT_TOKEN, BOT_LOG_LVL, BOT_LOG_FILENAME


logging.basicConfig(format=LOG_FORMAT,
                    level=BOT_LOG_LVL,
                    filename=BOT_LOG_FILENAME)

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
