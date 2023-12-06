from typing import Any
import discord
from discord.ext import commands
import slashCommands
import moderation.views
import moderation.moderation
import config
import logging
import sys
import utils


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if sys.argv[1] == "run":
            config.RUN()
        elif sys.argv[1] == "test":
            config.TEST()
        else:
            raise ValueError
        self.server = config.serverId
        self.dmsChannel = None
        self.errorChannel = None
        self.reportChannel = None

    async def on_ready(self):
        await self.add_cog(
            slashCommands.setup(self), guild=discord.Object(id=self.server)
        )
        await self.tree.sync(guild=discord.Object(id=self.server))
        self.errorChannel = self.get_channel(config.errorChannelId)
        self.reportChannel = self.get_channel(config.reportChannelId)

        reports = await moderation.moderation.getActive(self)

        for r in reports:
            view = moderation.views.ReportView(bot=self, data=r)
            self.add_view(view)

        print("Mikey is up")

        self.ready = True

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if (
            message.content.startswith("$send")
            and message.author.id == 493028834640396289
        ):
            str = message.content.split("-")
            try:
                channel = await self.fetch_channel(str[1])
                await channel.send(str[2])
            except:
                await self.errorChannel.send("Error during sending message")

        if (
            message.content.startswith("$reply")
            and message.author.id == 493028834640396289
        ):
            str = message.content.split("-")
            try:
                channel = await self.fetch_channel(str[1])
                msg = await channel.fetch_message(str[2])
                await msg.reply(str[3])
            except:
                await self.errorChannel.send("Error during replying message")

        if (
            message.content.startswith("$logs")
            and message.author.id == 493028834640396289
        ):
            file = discord.File("./data/logging.log")
            await message.channel.send(file=file)

        if (
            message.content.startswith("$history")
            and (message.author.id == 493028834640396289 or message.author.id == 1181521363127767130) 
        ):
            file = discord.File("./data/history.json")
            await self.reportChannel.send(file=file)

        if (message.channel.id == self.reportChannel.id):
            await self.deleteMessage(self.reportChannel.id, message.id)

        if isinstance(message.channel, discord.DMChannel):
            logging.info(
                f"DM by {message.author.name} ({message.channel.id}): {message.content}"
            )

    async def sendReport(self, data: moderation.moderation.ReportData):
        view = moderation.views.ReportView(self, data)
        message = await self.reportChannel.send(embed=view.embed, view=view)
        await self.reportChannel.create_thread(
            name=f"Report {data.offender.nick} ({data.id})",
            message=message,
            auto_archive_duration=1440,
        )

    async def sendReminder(self, data: moderation.moderation.ReportData) -> None:
        embed = moderation.views.ReminderEmbed(data)
        await data.offender.send(embed=embed)

    async def deleteMessage(self, channelId: int, messageId: int) -> None:
        channel = await self.fetch_channel(channelId)
        msg = await channel.fetch_message(messageId)
        await msg.delete(msg)

    async def sendMessage(self, msg: str, channelId: int) -> None:
        channel = self.get_channel(channelId)
        await channel.send(msg)

    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        logging.error(f"Error: {event_method}")


def runBot():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = MyBot(intents=intents, command_prefix=".")
    bot.run(config.Token, reconnect=True)


async def reconnect(bot):
    await bot.close()
    runBot()


if __name__ == "__main__":
    logging.basicConfig(
        filename="data/logging.log",
        format="%(asctime)s [%(levelname)s]:%(name)s:%(message)s",
        level=logging.INFO,
    )

    runBot()
