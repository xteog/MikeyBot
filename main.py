import datetime
import discord
from discord.ext import commands
import slashCommands
import views
import moderation
import config
import utils
import logging
import sys


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if sys.argv[1] == "run":
            self.config = config.Run
        elif sys.argv[1] == "test":
            self.config = config.Test
        else:
            raise ValueError
        self.server = self.config.serverId
        self.day = datetime.date.today() + datetime.timedelta(days=1)
        self.warningChannel = None
        self.errorChannel = None

    async def on_ready(self):
        await self.add_cog(
            slashCommands.setup(self), guild=discord.Object(id=self.server)
        )
        await self.tree.sync(guild=discord.Object(id=self.server))
        self.errorChannel = self.get_channel(self.config.errorChannelId)
        self.warningChannel = self.get_channel(self.config.warningsChannelId)
        moderation.setPaths(self.config.swearWordsPath, self.config.historyPath)
        #await self.change_presence(status=discord.Status.online)
        print("Mikey is up".format(self.user.name))

        self.ready = True

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if len(moderation.findSwearWords(message.content)) > 0:
            await message.add_reaction("🛑")
            await self.issueWarning(message)

    async def issueWarning(self, message):
        view = views.ViolationReportView(self, message, self.user)
        await self.warningChannel.send(embed=view.embed, view=view)

    async def sendWarning(self, message, badWordsSaid):
        await self.warningChannel.send(f"{message.author.name} said a bad word")

    async def deletMessage(self, id):
        msg = await self.depotChannel.fetch_message(id)
        await msg.delete()

    async def sendMessage(self, msg, channelId):
        channel = self.get_channel(channelId)
        await self.channel.send(msg)


def runBot():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = MyBot(intents=intents, command_prefix=".")
    bot.run(bot.config.Token, reconnect=True)


async def reconnect(bot):
    await bot.close()
    runBot()


if __name__ == "__main__":
    logging.basicConfig(
        filename="logging.log",
        format="%(asctime)s [%(levelname)s]:%(name)s:%(message)s",
        level=logging.INFO,
    )

    runBot()
