from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import i18n

def setup_game_keyboard(selected=None, lang="eng"):
    builder = InlineKeyboardBuilder()

    not_blank_buttons = [
        InlineKeyboardButton(
            text=i18n.get(lang, "combat_shot", i=i) + (" ✅" if selected and 'not_blank' in selected and selected['not_blank'] == i else ""),
            callback_data=f"set_not_blank_{i}" if not (selected and 'not_blank' in selected and selected['not_blank'] == i) else "disabled",
            disabled=(selected and 'not_blank' in selected and selected['not_blank'] == i)
        ) for i in range(1, 7)
    ]

    blank_buttons = [
        InlineKeyboardButton(
            text=i18n.get(lang, "blank_shot", i=i) + (" ✅" if selected and 'blank' in selected and selected['blank'] == i else ""),
            callback_data=f"set_blank_{i}" if not (selected and 'blank' in selected and selected['blank'] == i) else "disabled",
            disabled=(selected and 'blank' in selected and selected['blank'] == i)
        ) for i in range(1, 7)
    ]

    builder.row(*not_blank_buttons, width=3)
    builder.row(*blank_buttons, width=3)
    cancel_text = i18n.get(lang, "cancel_button")
    builder.row(
        InlineKeyboardButton(text=cancel_text, callback_data="cancel")
    )
    return builder.as_markup()

def game_tracking_keyboard(lang="eng"):
    builder = InlineKeyboardBuilder()
    record_shot_blank_text = i18n.get(lang, "record_shot_blank")
    record_shot_not_blank_text = i18n.get(lang, "record_shot_not_blank")
    use_phone_text = i18n.get(lang, "use_phone_button")
    reset_game_text = i18n.get(lang, "reset_game_button")

    builder.row(
        InlineKeyboardButton(text=record_shot_blank_text, callback_data="record_shot_blank"),
        InlineKeyboardButton(text=record_shot_not_blank_text, callback_data="record_shot_not_blank"),
        width=2
    )
    builder.row(
        InlineKeyboardButton(text=use_phone_text, callback_data="use_phone"),
        InlineKeyboardButton(text=reset_game_text, callback_data="reset_game"),
        width=2
    )
    return builder.as_markup()

def create_predict_shot_keyboard(total_shots, current_shot, lang="eng"):
    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(text=str(i), callback_data=f"predict_shot_{i}") for i in range(current_shot, total_shots + 1)
    ]
    for i in range(0, len(buttons), 5):
        builder.row(*buttons[i:i+5], width=5)
    cancel_text = i18n.get(lang, "cancel_predict_button")
    builder.row(
        InlineKeyboardButton(text=cancel_text, callback_data="cancel_predict"),
        width=1
    )
    return builder.as_markup()

def select_shot_type_keyboard(lang="eng"):
    builder = InlineKeyboardBuilder()
    set_shot_type_blank_text = i18n.get(lang, "set_shot_type_blank")
    set_shot_type_not_blank_text = i18n.get(lang, "set_shot_type_not_blank")
    cancel_text = i18n.get(lang, "cancel_predict_button")

    builder.row(
        InlineKeyboardButton(text=set_shot_type_blank_text, callback_data="set_shot_type_blank"),
        InlineKeyboardButton(text=set_shot_type_not_blank_text, callback_data="set_shot_type_not_blank"),
        width=2
    )
    builder.row(
        InlineKeyboardButton(text=cancel_text, callback_data="cancel_predict"),
        width=1
    )
    return builder.as_markup()

def get_cancel_keyboard(lang="eng"):
    builder = InlineKeyboardBuilder()
    cancel_text = i18n.get(lang, "cancel_button")
    builder.button(text=cancel_text, callback_data="cancel")
    return builder.as_markup()
