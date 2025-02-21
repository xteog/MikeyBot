from datetime import datetime, timezone
import logging
import discord
from AI.ChatMessage import ChatMessage, ChatResponse
import AI.api as api
from MikeyBotInterface import MikeyBotInterface
import config
from utils import listInsert


class Chat:
    def __init__(self, bot: MikeyBotInterface, guild: discord.Guild):
        self.bot = bot
        self.guild = guild
        self.model = "gemini-2.0-flash"
        self.summary = self.loadSummary()
        self.history = self.loadMessages()
        self.lock = False

        with open(config.geminiDescPath, "r") as f:
            self.prompt = f.read()

    def loadSummary(self) -> str | None:
        return self.bot.getSummary(guild=self.guild)

    def loadMessages(self) -> list[ChatMessage]:
        return list(self.bot.getMessages(guild=self.guild))

    def updateHistory(self, message: discord.Message) -> ChatMessage:
        msg = self.bot.insertMessage(message)
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

        return msg

    def formatInput(self, prompt: bool = True) -> list:
        data = []

        if prompt:
            desc = {"role": "user", "parts": {"text": self.prompt}}
            data.append(desc)

        if self.summary:
            summary = {
                "role": "user",
                "parts": {
                    "text": "This is a summary of what happened before:\n" + self.summary
                },
            }

            data.append(summary)

        for msg in self.history:
            data.append(msg.formatMessage())

        return data

    async def sendMessage(self, message: discord.Message) -> ChatResponse:

        if message.reference:
            repliedMsg = await message.channel.fetch_message(
                message.reference.message_id
            )

            self.updateHistory(repliedMsg)

        async for msg in message.channel.history(limit=10):
            if msg.id != message.id and msg.content:
                self.updateHistory(msg)

        
        msg = self.bot.insertMessage(message)

        response, tokens = await api.sendMessage(history=self.formatInput(), message=str(msg))

        self.updateHistory(message)

        if tokens > config.maxTokens and not self.lock:
            self.lock = True
            await self.generateSummary()
            self.lock = False

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

        logging.info(str(msg))

        response, tokens = await api.sendMessage(history=self.formatInput(), message=str(msg))

        return response
    

    async def generateSummary(self) -> None:
        history = self.history[:len(self.history) // 2] #TODO based on the number of the tokens

        data = []
        for msg in history:
            data.append(msg.formatMessage())

        response, tokens = await api.sendMessage(history=self.formatInput(prompt=False), message=config.summaryRequest)

        self.bot.updateSummary(guild=self.guild, summary=response.getText())
        self.summary = response.getText()

        self.bot.deleteMessages(messages=history) #TODO potrebbe volerci un po'
        self.history = self.loadMessages()

