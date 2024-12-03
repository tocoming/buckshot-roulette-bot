import logging
import re
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from keyboards import setup_game_keyboard, game_tracking_keyboard
from states import GameStates
from config import i18n, logger  

router = Router()
logger = logging.getLogger("bot_logger")  

@router.callback_query(F.data.startswith("set_not_blank_"), StateFilter(GameStates.GameSetup))
async def set_not_blank(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Handler 'set_not_blank' triggered by user {callback.from_user.id}")

    data = await state.get_data()
    lang = data.get("language", "eng")

    match = re.match(r'set_not_blank_(\d+)', callback.data)
    if not match:
        await callback.answer(i18n.get(lang, "invalid_input"), show_alert=True)
        logger.error(f"User {callback.from_user.id} sent invalid set_not_blank data: {callback.data}")
        return
    not_blank = int(match.group(1))
    await state.update_data(not_blank=not_blank)
    logger.info(f"User {callback.from_user.id} set not_blank: {not_blank}")

    blank = data.get('blank', None)
    if blank is not None:
        await finalize_game_setup(callback, state)
    else:
        setup_data = {'not_blank': not_blank}
        setup_text = i18n.get(lang, "ask_setup_game")
        await callback.message.edit_text(
            setup_text,
            reply_markup=setup_game_keyboard(selected=setup_data, lang=lang)
        )

@router.callback_query(F.data.startswith("set_blank_"), StateFilter(GameStates.GameSetup))
async def set_blank(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Handler 'set_blank' triggered by user {callback.from_user.id}")

    data = await state.get_data()
    lang = data.get("language", "eng")

    match = re.match(r'set_blank_(\d+)', callback.data)
    if not match:
        await callback.answer(i18n.get(lang, "invalid_input"), show_alert=True)
        logger.error(f"User {callback.from_user.id} sent invalid set_blank data: {callback.data}")
        return
    blank = int(match.group(1))
    await state.update_data(blank=blank)
    logger.info(f"User {callback.from_user.id} set blank: {blank}")

    not_blank = data.get('not_blank', None)
    if not_blank is not None:
        await finalize_game_setup(callback, state)
    else:
        setup_data = {'blank': blank}
        await callback.message.edit_text(
            i18n.get(lang, "ask_setup_game"),
            reply_markup=setup_game_keyboard(selected=setup_data, lang=lang)
        )

@router.message(F.text & F.text.regexp(r'^\d+/\d+$'), StateFilter(GameStates.GameSetup))
async def set_counts_via_text(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} is setting counts via text: {message.text}")
    data = await state.get_data()
    lang = data.get("language", "eng")
    try:
        parts = message.text.strip().split('/')
        not_blank = int(parts[0])
        blank = int(parts[1])
        if not_blank < 1 or blank < 1:
            raise ValueError
    except ValueError:
        await message.answer(i18n.get(lang, "invalid_format"))
        logger.warning(f"User {message.from_user.id} sent invalid text input for counts: {message.text}")
        return
    await state.update_data(not_blank=not_blank, blank=blank)
    logger.info(f"User {message.from_user.id} set counts via text: not_blank={not_blank}, blank={blank}")
    prob_blank = (blank / (blank + not_blank)) * 100
    prob_not_blank = (not_blank / (blank + not_blank)) * 100
    total_shots = not_blank + blank
    shots_selector_text = " | ".join([f"№{i}: ❓" for i in range(1, total_shots + 1)])
    game_setup_success = i18n.get(
        lang, 
        "game_setup_success", 
        not_blank=not_blank,
        blank=blank,
        shots_selector=shots_selector_text,
        prob_blank=prob_blank,
        prob_not_blank=prob_not_blank
    )
    await message.answer(
        game_setup_success,
        reply_markup=game_tracking_keyboard(lang=lang)
    )
    await state.update_data(
        current_shot=1,
        history=[],
        remaining_blank=blank,
        remaining_not_blank=not_blank,
        total_shots=total_shots,
        phone_predictions=[]
    )
    await state.set_state(GameStates.GameTracking)
    logger.info(f"User {message.from_user.id} transitioned to GameTracking state.")

async def finalize_game_setup(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    not_blank = data.get('not_blank', 0)
    blank = data.get('blank', 0)
    lang = data.get("language", "eng")

    if not_blank < 1 or blank < 1:
        await callback.message.edit_text(
            i18n.get(lang, "invalid_input"),
            reply_markup=setup_game_keyboard(lang=lang)
        )
        logger.warning(f"User {callback.from_user.id} tried to finalize game with not_blank={not_blank}, blank={blank}")
        return

    total_shots = not_blank + blank

    prob_blank = (blank / total_shots) * 100
    prob_not_blank = (not_blank / total_shots) * 100

    shots_selector_text = " | ".join([f"№{i}: ❓" for i in range(1, total_shots + 1)])

    game_setup_success = i18n.get(
        lang, 
        "game_setup_success", 
        not_blank=not_blank,
        blank=blank,
        shots_selector=shots_selector_text,
        prob_blank=prob_blank,
        prob_not_blank=prob_not_blank
    )

    await callback.message.edit_text(
        game_setup_success,
        parse_mode="Markdown",
        reply_markup=game_tracking_keyboard(lang=lang)
    )
    logger.info(f"User {callback.from_user.id} setup game with not_blank={not_blank}, blank={blank}")

    await state.update_data(
        current_shot=1,
        history=[],
        remaining_blank=blank,
        remaining_not_blank=not_blank,
        total_shots=total_shots,
        phone_predictions=[]
    )
    await state.set_state(GameStates.GameTracking)
    logger.info(f"User {callback.from_user.id} transitioned to GameTracking state.")
    await callback.answer()

@router.message(StateFilter(GameStates.GameSetup))
async def invalid_setup_input(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "eng")
    logger.info(f"User {message.from_user.id} sent invalid input during GameSetup: {message.text}")
    await message.answer(i18n.get(lang, "invalid_input"))
