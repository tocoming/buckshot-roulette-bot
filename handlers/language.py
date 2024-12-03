import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards import get_cancel_keyboard, setup_game_keyboard
from states import GameStates
from config import i18n, logger  

router = Router()
logger = logging.getLogger("bot_logger")  

@router.message(Command("ru"))
async def set_language_ru(message: Message, state: FSMContext):
    await state.clear()  
    await state.update_data(language="ru")
    logger.info(f"User {message.from_user.id} set language to Russian.")
    welcome_text = i18n.get("ru", "language_switched_to_ru")
    await message.answer(welcome_text, reply_markup=get_cancel_keyboard(lang="ru"))
    await ask_setup_game(message, state)

@router.message(Command("eng"))
async def set_language_eng(message: Message, state: FSMContext):
    await state.clear()  
    await state.update_data(language="eng")
    logger.info(f"User {message.from_user.id} set language to English.")
    welcome_text = i18n.get("eng", "language_switched_to_eng")
    await message.answer(welcome_text, reply_markup=get_cancel_keyboard(lang="eng"))
    await ask_setup_game(message, state)

async def ask_setup_game(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "eng")
    setup_text = i18n.get(lang, "ask_setup_game")
    await message.answer(setup_text, reply_markup=setup_game_keyboard(lang=lang))
    await state.set_state(GameStates.GameSetup)
