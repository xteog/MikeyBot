from datetime import datetime, timezone
import json
import logging
import re

import config
from exceptions import ResponseException


class ChatResponse:
    def __init__(self, content: str):
        self.content = content
        self.authorId = config.botId
        self.authorName = "Mikey"

        self.content = self.content.replace("@everyone", "@ everyone")
        self.content = self.content.replace("@here", "@ here")

    def getText(self) -> str:
        pattern = r"```json(.|\n)*```"
        return re.split(pattern, self.content)[0].strip()

    def getCommand(self) -> dict:
        pattern = r"```json(.|\n)*```"
        match = re.search(pattern, self.content)

        if match:
            json_string = match.group()
            json_string = json_string.removeprefix("```json")
            json_string = json_string.removesuffix("```")

            try:
                json_data = json.loads(json_string)

                if not isinstance(json_data, dict):
                    raise Exception("Command not formatted correctly")
            except Exception as e:
                logging.error(f"Error decoding JSON: {e}")
                raise ResponseException("Command not formatted correctly")

            return json_data
        # else: TODO caso in cui {}

        return None


class ChatMessage(ChatResponse):
    def __init__(
        self,
        id: str | int,
        content: str,
        author_name: str,
        author_id: str | int,
        channel_name: str,
        channel_id: str | int,
        date: datetime,
        reference: ChatResponse | None = None,
    ):
        super().__init__(content=content)
        self.id = id
        self.authorName = author_name
        self.authorId = author_id
        self.channelName = channel_name
        self.channelId = channel_id
        self.date = date
        self.reference = reference

    def formatMessage(self) -> dict:
        if int(self.authorId) == config.botId:
            author = "model"
        else:
            author = "user"

        return {"role": author, "parts": {"text": self.__str__()}}

    def __str__(self) -> str:
        """
        #"channel_name"("channel_id")
        "datetime"
        "user_name"("user_id"): "message"
        """

        if self.id == 0:
            return f"[System]: {self.getText()}"

        result = ""
        if self.authorId == str(config.botId):
            return self.content
        else:
            if self.reference:
                result = f"[Reply to {self.reference.authorName}: {self.reference.getText()[:50]}...]\n\n"

        result += f"#{self.channelName}({self.channelId})\n"
        result += f"{self.date.strftime(config.timeFormat)}\n"
        result += f"{self.authorName}({self.authorId}): {self.getText()}"

        return result

    def __eq__(self, value: object):
        return self.id == value.id
