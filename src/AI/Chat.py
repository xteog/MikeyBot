import json
import logging
import re
import discord
import AI.api as api
import config
from database.dao import UserDAO
from database.databaseHandler import Database


class Chat:
    def __init__(self, dbHandler: Database, previous_chats: dict = None):
        self.dbHandler = dbHandler
        self.model = "gemini-2.0-flash"
        self.history = []

        with open(config.geminiDescPath, "r") as f:
            description = f.read()

        if previous_chats:
            for user_message, model_response in previous_chats:
                self.history.append(self.formatMessage("user", user_message))
                self.history.append(self.formatMessage("model", model_response))

        if self.history:
            self.history = [self.formatMessage("user", description)] + self.history
        else:
            self.history = [self.formatMessage("user", description)]

    def sendMessage(self, user: discord.Member, message: str) -> tuple[str, dict]:
        nick = user.name#UserDAO(self.dbHandler).getNick(user)
        message = f"{nick}({user.id}): " + message
        self.history.append(self.formatMessage("user", message))

        response = api.sendMessage(history=self.history, message=message)
        response, command = self.extractJson(response)

        self.history.append(self.formatMessage("model", response))

        return self.extractJson(response)
    
    def formatMessage(self, author: str, message: str) -> dict:
        return {"role": author, "parts": {"text": message}}

    def extractJson(self, string: str) -> tuple[str, dict]:
        pattern = r"```json(.|\n)*```"

        match = re.search(pattern, string)
        json_data = None

        if match:
            json_string = match.group()
            json_string = json_string.removeprefix("```json")
            json_string = json_string.removesuffix("```")

            try:
                json_data = json.loads(json_string)
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON: {e}")
                raise e

        text = re.split(pattern, string)[0].strip()

        return text, json_data
