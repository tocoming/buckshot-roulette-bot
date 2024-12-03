import logging
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext  

from keyboards import game_tracking_keyboard, setup_game_keyboard  
from states import GameStates
from config import i18n, logger  

router = Router()
logger = logging.getLogger("bot_logger")  

@router.callback_query(F.data == "cancel_predict", StateFilter(GameStates.PredictingShot))
async def cancel_predict(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Handler 'cancel_predict' triggered by user {callback.from_user.id}")
    data = await state.get_data()
    lang = data.get("language", "eng")
    await callback.message.edit_text(
        i18n.get(lang, "prediction_cancelled"),
        parse_mode="Markdown",
        reply_markup=game_tracking_keyboard(lang=lang)
    )
    logger.info(f"User {callback.from_user.id} cancelled prediction.")
    await state.set_state(GameStates.GameTracking)
    await callback.answer()

@router.callback_query(F.data == "reset_game", StateFilter(GameStates.GameTracking))
async def reset_game(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Handler 'reset_game' triggered by user {callback.from_user.id}")

    data = await state.get_data()
    lang = data.get("language", "eng")

    await state.clear()

    await state.set_data({"language": lang})
    logger.debug(f"Language preserved as: {lang}")

    reset_text = i18n.get(lang, "game_reset")
    await callback.message.edit_text(reset_text, parse_mode="Markdown", reply_markup=setup_game_keyboard(lang=lang))
    await state.set_state(GameStates.GameSetup)
    await callback.answer()

@router.callback_query(F.data == 'cancel', StateFilter(GameStates.GameSetup, GameStates.GameTracking, GameStates.PredictingShot))
async def cancel_action(callback_query: CallbackQuery, state: FSMContext):
    logger.info(f"Handler 'cancel_action' triggered by user {callback_query.from_user.id}")

    data = await state.get_data()
    lang = data.get("language", "eng")

    await state.clear()

    await state.set_data({"language": lang})
    logger.debug(f"Language preserved as: {lang}")

    await callback_query.answer()
    await callback_query.message.edit_reply_markup()  
    await callback_query.message.answer(i18n.get(lang, "action_cancelled"))
    logger.info(f"User {callback_query.from_user.id} cancelled the action.")
