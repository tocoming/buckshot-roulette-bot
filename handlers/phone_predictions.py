import logging
import re
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards import create_predict_shot_keyboard, select_shot_type_keyboard, game_tracking_keyboard
from states import GameStates
from config import i18n, logger  

router = Router()
logger = logging.getLogger("bot_logger")  

@router.callback_query(F.data == "use_phone", StateFilter(GameStates.GameTracking))
async def use_phone(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Handler 'use_phone' triggered by user {callback.from_user.id}")
    data = await state.get_data()
    total_shots = data.get('total_shots', 0)
    current_shot = data.get('current_shot', 1)
    lang = data.get("language", "eng")

    if current_shot > total_shots:
        await callback.answer(i18n.get(lang, "game_over"), show_alert=True)
        logger.warning(f"User {callback.from_user.id} tried to use phone after all shots.")
        return

    keyboard = create_predict_shot_keyboard(total_shots, current_shot, lang=lang)
    await callback.message.edit_text(
        i18n.get(lang, "use_phone"),
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await state.set_state(GameStates.PredictingShot)
    logger.info(f"User {callback.from_user.id} transitioned to PredictingShot state.")
    await callback.answer()

@router.callback_query(F.data.startswith("predict_shot_"), StateFilter(GameStates.PredictingShot))
async def predict_shot(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Handler 'predict_shot' triggered by user {callback.from_user.id}")
    match = re.match(r'predict_shot_(\d+)', callback.data)
    if not match:
        await callback.answer("❌ Некорректные данные.", show_alert=True)
        logger.error(f"User {callback.from_user.id} sent invalid predict_shot data: {callback.data}")
        return
    shot_number = int(match.group(1))

    data = await state.get_data()
    lang = data.get("language", "eng")
    total_shots = data.get('total_shots', 0)
    history = data.get('history', [])
    phone_predictions = data.get('phone_predictions', [])

    if shot_number < 1 or shot_number > total_shots:
        await callback.answer(i18n.get(lang, "invalid_shot_number"), show_alert=True)
        logger.warning(f"User {callback.from_user.id} tried to predict invalid shot number: {shot_number}")
        return

    if any(shot['shot_number'] == shot_number for shot in history):
        await callback.answer(i18n.get(lang, "shot_already_occurred"), show_alert=True)
        logger.warning(f"User {callback.from_user.id} tried to predict already occurred shot {shot_number}.")
        return

    if any(pred['shot_number'] == shot_number for pred in phone_predictions):
        await callback.answer(i18n.get(lang, "prediction_already_exists"), show_alert=True)
        logger.warning(f"User {callback.from_user.id} tried to predict shot {shot_number} multiple times.")
        return

    phone_predictions.append({'shot_number': shot_number, 'result': None})
    await state.update_data(phone_predictions=phone_predictions)
    logger.info(f"User {callback.from_user.id} added a phone prediction for shot {shot_number}.")

    await callback.message.edit_text(
        i18n.get(lang, "choose_shot_type").format(shot_number=shot_number),
        parse_mode="Markdown",
        reply_markup=select_shot_type_keyboard(lang=lang)
    )
    await state.set_state(GameStates.PredictingShot)
    logger.info(f"User {callback.from_user.id} is setting shot type for shot {shot_number}.")
    await callback.answer()

@router.callback_query(F.data.startswith("set_shot_type_"), StateFilter(GameStates.PredictingShot))
async def set_shot_type(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Handler 'set_shot_type' triggered by user {callback.from_user.id}")
    data = callback.data
    lang = (await state.get_data()).get("language", "eng")
    if data == "set_shot_type_blank":
        shot_type = 'blank'
    elif data == "set_shot_type_not_blank":
        shot_type = 'not_blank'
    else:
        await callback.answer("❌ Некорректные данные типа выстрела.", show_alert=True)
        logger.error(f"User {callback.from_user.id} sent invalid shot type data: {callback.data}")
        return

    state_data = await state.get_data()
    phone_predictions = state_data.get('phone_predictions', [])
    history = state_data.get('history', [])

    pending_predictions = [pred for pred in phone_predictions if pred['result'] is None]
    if not pending_predictions:
        await callback.answer(i18n.get(lang, "invalid_shot_type"), show_alert=True)
        logger.error(f"User {callback.from_user.id} tried to set shot type without pending predictions.")
        return
    prediction = pending_predictions[0]
    shot_number = prediction['shot_number']
    prediction['result'] = shot_type
    await state.update_data(phone_predictions=phone_predictions)
    logger.info(f"User {callback.from_user.id} set prediction for shot {shot_number} as {shot_type}.")

    remaining_blank = state_data.get('remaining_blank', 0)
    remaining_not_blank = state_data.get('remaining_not_blank', 0)
    if shot_type == 'blank':
        remaining_blank -= 1
    else:
        remaining_not_blank -= 1

    if remaining_blank < 0 or remaining_not_blank < 0:
        await callback.answer(i18n.get(lang, "invalid_shot_type"), show_alert=True)
        logger.error(f"User {callback.from_user.id} set invalid remaining counts: blank={remaining_blank}, not_blank={remaining_not_blank}")
        return

    await state.update_data(
        remaining_blank=remaining_blank,
        remaining_not_blank=remaining_not_blank
    )
    remaining_shots = remaining_blank + remaining_not_blank

    logger.debug(f"User {callback.from_user.id} | Remaining Blank: {remaining_blank} | Remaining Not Blank: {remaining_not_blank} | Remaining Shots: {remaining_shots}")

    prob_blank = (remaining_blank / remaining_shots) * 100 if remaining_shots > 0 else 0
    prob_not_blank = (remaining_not_blank / remaining_shots) * 100 if remaining_shots > 0 else 0

    if remaining_shots == 0:
        history = state_data.get('history', [])
        history_text = ' | '.join([
            f"№{shot['shot_number']}: ✅ Blank" if shot['result'] == 'blank' else f"№{shot['shot_number']}: 💥 Combat"
            for shot in history
        ])
        game_over_text = i18n.get(lang, "game_over").format(
            history=history_text,
            predictions_info=""
        )
        await callback.message.edit_text(
            game_over_text,
            parse_mode="Markdown",
            reply_markup=None
        )
        logger.info(f"User {callback.from_user.id} завершил игру.")
        await state.clear()
        await callback.answer()
        return

    shots_selector = []
    for i in range(1, state_data.get('total_shots', 0) + 1):
        shot_record = next((shot for shot in history if shot['shot_number'] == i), None)
        if shot_record:
            result = shot_record['result']
            emoji = '✅' if result == 'blank' else '💥'
        else:
            prediction = next((pred for pred in phone_predictions if pred['shot_number'] == i and pred['result']), None)
            if prediction:
                result = prediction['result']
                emoji = '✅' if result == 'blank' else '💥'
            else:
                emoji = '❓'
        if i == state_data.get('current_shot', 1):
            shots_selector.append(f"**№{i}: {emoji}**")
        else:
            shots_selector.append(f"№{i}: {emoji}")

    shots_selector_text = " | ".join(shots_selector)

    predictions_info = ""
    if phone_predictions:
        predictions_info += "\n📱 **Phone Predictions:**\n"
        for pred in phone_predictions:
            if pred['result']:
                pred_result = '✅ Blank' if pred['result'] == 'blank' else '💥 Combat'
                predictions_info += f"• Shot №{pred['shot_number']}: {pred_result}\n"

    updated_data = await state.get_data()
    updated_current_shot = updated_data.get('current_shot', 1)

    game_tracking_text = i18n.get(lang, "game_tracking_current_shot").format(
        current_shot=updated_current_shot,
        shots_selector=shots_selector_text,
        prob_blank=prob_blank,
        prob_not_blank=prob_not_blank,
        predictions_info=predictions_info
    )

    await callback.message.edit_text(
        game_tracking_text,
        parse_mode="Markdown",
        reply_markup=game_tracking_keyboard(lang=lang)
    )
    logger.info(f"Updated probabilities for user {callback.from_user.id}: blank={prob_blank:.2f}%, not_blank={prob_not_blank:.2f}%")
    logger.debug(f"User {callback.from_user.id} | Next Shot: {updated_current_shot} | Remaining Blank: {remaining_blank} | Remaining Not Blank: {remaining_not_blank}")

    await state.set_state(GameStates.GameTracking)
    logger.debug(f"User {callback.from_user.id} state set back to GameTracking.")
    await callback.answer()
