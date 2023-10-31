from aiogram import types

from utils import File


class KeyboardApp:
    # Keypad with geo-positioning button
    geo = types.ReplyKeyboardMarkup(
        keyboard=
        [
            [types.KeyboardButton(text="Share Position", request_location=True)]
        ],
        resize_keyboard=True
    )
    # Menu section keypads
    keyboards = {}
    # Selection keypads
    select = {}

    def __init__(self, obj: File, obj_cfg: File):
        self.generating_keyboards(obj.text)
        self.generating_keyboards_select(obj_cfg.text)

    def generating_keyboards(self, text: dict):
        """
        Generating keyboards for menus
        """
        for element in text:
            keyboard = []
            for line in text[element]:
                line_buttons = []
                for button in line:
                    if button["type"] == "callback":
                        line_buttons.append(
                            types.InlineKeyboardButton(text=button["text"], callback_data=button["data"])
                        )
                    else:
                        line_buttons.append(
                            types.InlineKeyboardButton(text=button["text"], url=button["data"])
                        )
                keyboard.append(line_buttons)
            self.keyboards[element] = types.InlineKeyboardMarkup(
                resize_keyboard=True,
                inline_keyboard=keyboard
            )

    def generating_keyboards_select(self, text: dict):
        """
        Generating keyboards for select something
        """
        for element in text["KEYBOARDS_SELECT"]:
            keyboard = []
            len_elements = len(text["KEYBOARDS_SELECT"][element])
            name = element.lower()
            for i in range(0, len_elements):
                line = [
                    types.InlineKeyboardButton(
                        text=text["KEYBOARDS_SELECT"][element][i], callback_data=f"{name}:{i}"
                    )
                ]
                keyboard.append(line)
            self.select[element] = types.InlineKeyboardMarkup(
                resize_keyboard=True,
                inline_keyboard=keyboard
            )
