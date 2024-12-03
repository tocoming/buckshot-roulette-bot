import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.fsm.middleware import FSMContextMiddleware

from config import API_TOKEN

bot_properties = DefaultBotProperties(parse_mode='Markdown')
bot = Bot(token=API_TOKEN, default=bot_properties)

storage = MemoryStorage()

dp = Dispatcher(storage=storage)

router = Router()
dp.include_router(router)

dp.update.middleware.register(FSMContextMiddleware(storage=storage, events_isolation=SimpleEventIsolation()))
