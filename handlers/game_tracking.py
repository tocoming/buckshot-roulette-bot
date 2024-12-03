import logging
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext  

from keyboards import game_tracking_keyboard
from states import GameStates
from config import i18n, logger  

router = Router()
logger = logging.getLogger("bot_logger")  

@router.callback_query(F.data == "record_shot_blank", StateFilter(GameStates.GameTracking))
async def record_shot_blank(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Handler 'record_shot_blank' triggered by user {callback.from_user.id}")
    await record_shot(callback, state, shot_type='blank')

@router.callback_query(F.data == "record_shot_not_blank", StateFilter(GameStates.GameTracking))
async def record_shot_not_blank(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Handler 'record_shot_not_blank' triggered by user {callback.from_user.id}")
    await record_shot(callback, state, shot_type='not_blank')

async def record_shot(callback: CallbackQuery, state: FSMContext, shot_type: str):
    data = await state.get_data()
    lang = data.get("language", "eng")
    remaining_blank = data.get('remaining_blank', 0)
    remaining_not_blank = data.get('remaining_not_blank', 0)
    total_shots = data.get('total_shots', 0)
    current_shot = data.get('current_shot', 1)
    history = data.get('history', [])
    phone_predictions = data.get('phone_predictions', [])

    logger.debug(f"User {callback.from_user.id} | Shot Type: {shot_type} | Current Shot: {current_shot} | "
                 f"Remaining Blank: {remaining_blank} | Remaining Not Blank: {remaining_not_blank}")

    predicted_result = None
    for pred in phone_predictions:
        if pred['shot_number'] == current_shot:
            predicted_result = pred.get('result')
            break

    if predicted_result:

        shot_type = predicted_result
        logger.info(f"User {callback.from_user.id} has a prediction for shot {current_shot}: {shot_type}")
    else:

        if shot_type == 'blank':
            if remaining_blank <= 0:
                await callback.answer(i18n.get(lang, "no_remaining_blanks"), show_alert=True)
                logger.warning(f"User {callback.from_user.id} tried to record a blank shot with no remaining blanks.")
                return
            remaining_blank -= 1
        elif shot_type == 'not_blank':
            if remaining_not_blank <= 0:
                await callback.answer(i18n.get(lang, "no_remaining_not_blanks"), show_alert=True)
                logger.warning(f"User {callback.from_user.id} tried to record a not_blank shot with no remaining not blanks.")
                return
            remaining_not_blank -= 1
        else:
            await callback.answer(i18n.get(lang, "invalid_shot_type"), show_alert=True)
            logger.error(f"User {callback.from_user.id} sent invalid shot type: {shot_type}")
            return

    history.append({'shot_number': current_shot, 'result': shot_type})
    remaining_shots = remaining_blank + remaining_not_blank

    logger.info(f"User {callback.from_user.id} recorded shot {current_shot}: {shot_type}")
    logger.debug(f"Updated Remaining Blank: {remaining_blank}, Remaining Not Blank: {remaining_not_blank}")

    if predicted_result:
        for pred in phone_predictions:
            if pred['shot_number'] == current_shot:
                pred['result'] = shot_type
                break

    if remaining_shots == 0:
        history_text = ' | '.join([
            f"№{shot['shot_number']}: ✅ Blank" if shot['result'] == 'blank' else f"№{shot['shot_number']}: 💥 Combat"
            for shot in history
        ])
        predictions_info = ""
        if phone_predictions:
            predictions_info += "\n📱 **Phone Predictions:**\n"
            for pred in phone_predictions:
                if pred['result']:
                    pred_result = '✅ Blank' if pred['result'] == 'blank' else '💥 Combat'
                    predictions_info += f"• Shot №{pred['shot_number']}: {pred_result}\n"

        game_over_text = i18n.get(lang, "game_over").format(
            history=history_text,
            predictions_info=predictions_info
        )

        new_game_text = i18n.get(lang, "start_new_game_button")
        new_game_button = InlineKeyboardButton(text=new_game_text, callback_data="start_new_game")
        game_over_keyboard = InlineKeyboardMarkup(inline_keyboard=[[new_game_button]])

        await callback.message.edit_text(
            game_over_text,
            parse_mode="Markdown",
            reply_markup=game_over_keyboard
        )
        logger.info(f"User {callback.from_user.id} завершил игру.")

        await state.clear()
        await state.set_data({"language": lang})

        await callback.answer()
        return

    current_shot += 1
    await state.update_data(
        current_shot=current_shot,
        history=history,
        remaining_blank=remaining_blank,
        remaining_not_blank=remaining_not_blank,
        phone_predictions=phone_predictions
    )

    prob_blank = (remaining_blank / remaining_shots) * 100 if remaining_shots > 0 else 0
    prob_not_blank = (remaining_not_blank / remaining_shots) * 100 if remaining_shots > 0 else 0

    shots_selector = []
    for i in range(1, total_shots + 1):
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
        if i == current_shot:
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
