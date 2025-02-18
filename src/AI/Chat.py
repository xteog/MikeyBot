from datetime import datetime, timezone
import json
import logging
import re
import discord
from AI.ChatMessage import ChatMessage, ChatResponse, convertMessage
import AI.api as api
import config
from exceptions import ResponseException
from utils import listInsert


class Chat:
    def __init__(self):
        self.model = "gemini-2.0-flash"
        self.history = self.loadDatabase()

        with open(config.geminiDescPath, "r") as f:
            self.description = f.read()

    def loadDatabase(self) -> list[ChatMessage]:
        return []

    def updateHistory(self, messages: list[discord.Message]) -> None: #TODO salva in database
        for message in messages:
            msg = convertMessage(message)
            i = len(self.history) - 1

            found = False
            while i >= 0:

                if self.history[i] == msg:
                    found = True
                    break

                if self.history[i].date < msg.date:
                    listInsert(list=self.history, value=msg, index=i + 1)
                    found = True
                    break

                i -= 1

            if not found:
                listInsert(list=self.history, value=msg, index=0)

    def formatHistory(self) -> list:
        data = []

        for msg in self.history:
            data.append(msg.formatMessage())

        desc = {"role": "user", "parts": {"text": self.description}}

        data = [desc] + data

        return data

    async def sendMessage(self, message: discord.Message, pastMessages: list[discord.Message] = None) -> ChatResponse:
        if pastMessages:
            self.updateHistory(pastMessages)

        msg = convertMessage(message=message)

        response = await api.sendMessage(history=self.formatHistory(), message=str(msg))

        response = self.extractResponse(response)

        return response

    async def sendSystemMessage(self, message: str) -> ChatResponse:
        msg = ChatMessage(
            id=0,
            content=message,
            author_id=0,
            author_name="System",
            channel_id=0,
            channel_name="",
            date=datetime.now(timezone.utc),
        )
        self.history.append(msg)

        response = await api.sendMessage(history=self.formatHistory(), message=str(msg))
        response = self.extractResponse(response)

        return response

    def extractResponse(self, string: str) -> ChatResponse:
        pattern = r"```json(.|\n)*```"

        match = re.search(pattern, string)
        json_data = None

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

        text = re.split(pattern, string)[0].strip()

        return ChatResponse(content=text, command=json_data)
