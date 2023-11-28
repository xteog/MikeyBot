import datetime
from typing import Any
import discord
from discord.ext import commands
import slashCommands
import moderation.views
import moderation.moderation
import config
import logging
import sys
import verification.views


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
        self.day = datetime.date.today() + datetime.timedelta(days=1)
        self.warningChannel = None
        self.dmsChannel = None
        self.errorChannel = None
        self.verifyChannel = None
        self.checkVerificationChannel = None

    async def on_ready(self):
        await self.add_cog(
            slashCommands.setup(self), guild=discord.Object(id=self.server)
        )
        await self.tree.sync(guild=discord.Object(id=self.server))
        self.errorChannel = self.get_channel(config.errorChannelId)
        self.warningChannel = self.get_channel(config.warningsChannelId)
        self.dmsChannel = self.get_channel(config.dmsChannelId)
        self.verifyChannel = self.get_channel(config.verifyChannelId)
        self.checkVerificationChannel = self.get_channel(
            config.checkVerificationChannelId
        )
        # await self.change_presence(status=discord.Status.online)

        view = verification.views.VerificationView(self)
        # await self.verifyChannel.send(view=view, embed=view.embed)

        print("Mikey is up".format(self.user.name))

        self.ready = True

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if message.content == "$role":
            await message.author.add_roles(
                discord.utils.get(message.author.guild.roles, id=config.fiaRole)
            )

        if message.content.startswith("$message") and message.author.id == 493028834640396289:
            str = message.content.split(" ")
            try:
                channel = await self.fetch_channel(str[1])
                await channel.send(str[2])
            except:
                await self.errorChannel.send("Error during sending message")

        if message.content.startswith("$reply") and message.author.id == 493028834640396289:
            str = message.content.split(" ")
            try:
                channel = await self.fetch_channel(str[1])
                msg = await channel.fetch_message(str[2])
                await msg.reply(str[3])
            except:
                await self.errorChannel.send("Error during replying message")

        if isinstance(message.channel, discord.DMChannel):
            logging.info(f"DM by {message.author.name} ({message.channel.id}): {message.content}")

        """
        if isinstance(message.channel,discord.DMChannel):
            if message.attachments:
                if verification.views.isVerifying(message.author.id, checkConnection=True):
                    await self.checkVerificationChannel.send(message.attachments[0].url)
                if verification.views.isVerifying(message.author.id, checkSteamId=True):
                    await self.checkVerificationChannel.send(message.attachments[0].url)
        """

        if message.channel.id == self.dmsChannel.id:
            if message.attachments:
                if verification.views.isVerifying(
                    userId=message.author.id, checkConnection=True
                ):
                    view = verification.views.VerifyView(
                        self,
                        user=message.author,
                        file=message.attachments[0].url,
                        connection=True,
                    )
                    await self.checkVerificationChannel.send(
                        view=view, embed=view.embed
                    )
                elif verification.views.isVerifying(
                    userId=message.author.id, checkSteamId=True
                ):
                    view = verification.views.VerifyView(
                        self,
                        user=message.author,
                        file=message.attachments[0].url,
                        steamId=True,
                    )
                    await self.checkVerificationChannel.send(
                        view=view, embed=view.embed
                    )

        if len(moderation.moderation.findSwearWords(message.content)) > 0:
            await message.add_reaction("<:WarningFlag:1150224008881647657>")
            await self.issueWarning(message)

    async def issueWarning(self, message: discord.Message):
        view = moderation.views.ReportMessageView(message, self.user)
        print("done")
        await self.warningChannel.send(embed=view.embed, view=view)

    async def sendWarning(self, data: moderation.moderation.WarningData):
        view = moderation.views.AppealView(bot=self, data=data)
        await self.dmsChannel.send(
            content=f"dms of {data.offender.name}", embed=view.embed, view=view
        )

    async def sendReport(self, data: moderation.moderation.ReportData):
        view = moderation.views.ReportView(self, data)
        message = await self.warningChannel.send(embed=view.embed, view=view)
        await self.warningChannel.create_thread(
            name=f"Report by {data.creator} ({data.id})",
            message=message,
            auto_archive_duration=1440,
        )

    async def sendReminder(self, data: moderation.moderation.ReportData):
        embed = moderation.views.ReminderEmbed(data)
        await data.offender.send(embed=embed)

    async def deleteMessage(self, id: int):
        msg = await self.depotChannel.fetch_message(id)
        await msg.delete()

    async def sendMessage(self, msg: str, channelId: int):
        channel = self.get_channel(channelId)
        await channel.send(msg)

    async def on_error(self, event_method: str) -> None:
        print(f"Error: {event_method}")


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
