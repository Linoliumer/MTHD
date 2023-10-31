import json


class File:
    path = str
    text = dict

    def __init__(self, path):
        self.path = path
        self.text = self.open_file()

    def open_file(self) -> dict:
        """
        Get text from JSON File
        :return:
        """
        with open(self.path, "r", encoding="utf-8") as file_data:
            text = json.loads(file_data.read())
            file_data.close()
            return text

    async def save_change(self) -> None:
        """
        Save text in JSON File
        :return:
        """
        with open(self.path, "w", encoding="utf-8") as file_data:
            json.dump(self.text, file_data)
            file_data.close()
