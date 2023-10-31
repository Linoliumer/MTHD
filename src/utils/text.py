from .file import File


class TextApp:
    menus = {}
    input = {}
    messages = {}
    errors = {}

    def __init__(self, obj: File):
        self.generating_menus_text(obj.text)
        self.generating_input_text(obj.text)
        self.generating_messages_text(obj.text)
        self.generating_errors_text(obj.text)

    def generating_menus_text(self, text: dict) -> None:
        """
        Generating text for menus
        """
        for element in text['RU']['MENU']['TITLES']:
            self.menus[element] = f"{text['RU']['MENU']['HEADER'][element]}\n\n{text['RU']['MENU']['BODY'][element]}"

    def generating_input_text(self, text: dict) -> None:
        """
        Generating text for input
        """
        for key, value in text['RU']['INPUT'].items():
            self.input[key] = value

    def generating_messages_text(self, text: dict) -> None:
        """
        Generating text for messages
        """
        for key, value in text['RU']['MESSAGE'].items():
            self.messages[key] = value

    def generating_errors_text(self, text: dict) -> None:
        """
        Generating text for errors
        """
        for key, value in text['RU']['ERROR'].items():
            self.errors[key] = value
