from datetime import datetime, timezone

import discord

import config


class ChatResponse:
    def __init__(self, content: str, command: dict = None):
        self.content = content
        self.command = command
        self.authorId = config.botId
        self.authorName = "Mikey"


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
        command: dict = None,
        replying_to: str | int = None,
    ):
        super().__init__(content=content, command=command)
        self.id = id
        self.authorName = author_name
        self.authorId = author_id
        self.channelName = channel_name
        self.channelId = channel_id
        self.date = date
        self.replying_to = replying_to

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
            return f"[System]: {self.content}"

        result = ""
        if self.authorId == config.botId:
            if self.command:
                return self.content  # TODO valuta se serve command
            else:
                return self.content
        else:
            if self.replying_to and False: # TODO do this
                result = self.replying_to + "\n"

        result += f"#{self.channelName}({self.channelId})\n"
        result += f"{self.date.strftime(config.timeFormat)}\n"
        result += f"{self.authorName}({self.authorId}): {self.content}"

        return result

    def __eq__(self, value: object):
        return self.id == value.id


def convertMessage(message: discord.Message) -> ChatMessage:
    msg = message.content

    for user in message.mentions:
        msg = msg.replace(user.mention, f"@{user.name}({user.id})")
        

    reply = None
    if message.reference:
        reply = message.reference.message_id

    return ChatMessage(
        id=message.id,
        content=msg,
        author_name=message.author.name,
        author_id=message.author.id,
        channel_name=message.channel.name,
        channel_id=message.channel.id,
        date=message.created_at,
        replying_to=reply,
    )
