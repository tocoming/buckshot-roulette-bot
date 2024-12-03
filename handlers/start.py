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

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    logger.info(f"Received /start from user {message.from_user.id}")

    data = await state.get_data()

    if 'language' not in data:

        user_lang_code = message.from_user.language_code
        if user_lang_code and user_lang_code.startswith("ru"):
            lang = "ru"
        else:
            lang = "eng"  

        await state.update_data(language=lang)
        logger.info(f"User {message.from_user.id} language set to {lang} based on Telegram settings.")
    else:

        lang = data.get("language", "eng")

    welcome_text = i18n.get(lang, "welcome")
    await message.answer(welcome_text, reply_markup=get_cancel_keyboard(lang=lang))
    await ask_setup_game(message, state)

async def ask_setup_game(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "eng")
    setup_text = i18n.get(lang, "ask_setup_game")
    await message.answer(setup_text, reply_markup=setup_game_keyboard(lang=lang))
    await state.set_state(GameStates.GameSetup)
