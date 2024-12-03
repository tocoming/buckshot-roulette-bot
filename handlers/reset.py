import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards import setup_game_keyboard
from states import GameStates
from config import i18n, logger  

router = Router()
logger = logging.getLogger("bot_logger")  

@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext):
    logger.info(f"Received /reset from user {message.from_user.id}")

    data = await state.get_data()
    lang = data.get("language", "eng")

    await state.clear()

    await state.set_data({"language": lang})
    logger.debug(f"Language preserved as: {lang}")

    reset_text = i18n.get(lang, "game_reset")
    await message.answer(reset_text, reply_markup=setup_game_keyboard(lang=lang))
    await state.set_state(GameStates.GameSetup)

@router.callback_query(F.data == "start_new_game")
async def start_new_game(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Handler 'start_new_game' triggered by user {callback.from_user.id}")

    data = await state.get_data()
    lang = data.get("language", "eng")

    await state.clear()

    await state.set_data({"language": lang})
    logger.debug(f"Language preserved as: {lang}")

    reset_text = i18n.get(lang, "game_reset")
    await callback.message.edit_text(reset_text, reply_markup=setup_game_keyboard(lang=lang))
    await state.set_state(GameStates.GameSetup)
    await callback.answer()
