import asyncio
from datetime import datetime
from datetime import timedelta
import utils
import discord
from discord.ext import commands
import slashCommands
from moderation import views
from moderation import violations
import config
import logging
import sys
import lobby

#import load_log


class MikeyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if len(sys.argv) <= 1:
            config.TEST()
        elif sys.argv[1] == "run":
            config.RUN()
        elif sys.argv[1] == "test":
            config.TEST()
        else:
            raise ValueError

        self.server = config.serverId
        self.dmsChannel = None
        self.errorChannel = None
        self.reportChannel = None
        self.ccChannel = None
        self.lobbiesChannel = None

        self.lobbies = {}
        self.reportWindowNotice = utils.load_reportWindowNotice()
        self.schedule = utils.load_schedule()

        self.ready = False

    async def on_ready(self):
        await self.add_cog(
            slashCommands.setup(self), guild=discord.Object(id=self.server)
        )
        await self.tree.sync(guild=discord.Object(id=self.server))
        self.errorChannel = self.get_channel(config.errorChannelId)
        self.reportChannel = self.get_channel(config.reportChannelId)
        self.ccChannel = self.get_channel(config.ccChannelId)
        self.lobbiesChannel = self.get_channel(config.lobbiesChannelId)

        try:
            reports = await violations.getActive(self)

            for r in reports:
                view = views.ReportView(bot=self, data=r)
                self.add_view(view)

            self.add_view(views.SwitchView(self))
            lobbies = lobby.getLobbiesList()
            self.add_view(lobby.LobbiesView(self, lobbies))
        except Exception as e:
            print(e)

        print("Mikey is up")
        #await load_log.loadLog(self)
        
        self.ready = True

    async def setup_hook(self) -> None:
        self.bg_task = self.loop.create_task(self.background_task())

    async def background_task(self):
        awake_at = datetime.utcnow()

        await self.wait_until_ready()
        while not self.ready:
            await asyncio.sleep(1)

        while not self.is_closed():
            lobbies = lobby.getLobbiesList()
            view = lobby.LobbiesView(self, lobbies)

            oldMessage = None
            async for message in self.lobbiesChannel.history(limit=100):
                if message.author == self.user:
                    oldMessage = message

            if oldMessage == None:
                await self.lobbiesChannel.send(view=view, embed=view.embed)
            elif len(lobbies) != len(self.lobbies):
                await oldMessage.delete()
                await self.lobbiesChannel.send(view=view, embed=view.embed)
            else:
                await oldMessage.edit(view=view, embed=view.embed)

            self.lobbies = lobbies
            
            if awake_at < datetime.utcnow():
                awake_at = datetime.utcnow() + timedelta(hours=1)

                for thread in self.reportChannel.threads:
                    if not thread.archived:
                        id = thread.name[
                            thread.name.find("(") + 1 : thread.name.find(")")
                        ]
                        report = await violations.getReports(self, id=id)

                        if len(report) > 0 and not report[0].active:
                            await thread.edit(archived=True)

                for league in config.reportWindowDelta.keys():
                    open_date = self.schedule[league]["rounds"][
                        self.getCurrentRound(league) - 1
                    ] + timedelta(days=1)

                    if (
                        self.reportWindowNotice[league] < open_date
                        and datetime.utcnow()
                        < open_date + config.reportWindowDelta[league]
                        and league in config.leaguesChannelIds.keys()
                    ):
                        if datetime.utcnow() > open_date:
                            msg = f"Reports window is now open until <t:{int((open_date + config.reportWindowDelta[league]).timestamp())}:f>."
                            await self.sendMessage(
                                msg, config.leaguesChannelIds[league]
                            )

                            self.reportWindowNotice[league] = datetime.utcnow()
                            utils.update_reportWindowNotice(self.reportWindowNotice)
                        elif datetime.utcnow() + timedelta(minutes=59) > open_date:
                            awake_at = (open_date - datetime.utcnow())

            if self.lobbies != None and len(self.lobbies) > 0:
                sleep = 60
            else:
                sleep = 5 * 60

            await asyncio.sleep(sleep)

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        await self.devCommands(message)

        if message.mention_everyone and len(message.author.roles) < 5:
            await message.author.ban(reason="Gotcha u moron", delete_message_seconds=60)
            await message.channel.send("Gotcha u moron")

        if message.channel.id == self.reportChannel.id:
            await self.deleteMessage(self.reportChannel.id, message.id)

        if isinstance(message.channel, discord.DMChannel):
            logging.info(
                f"DM by {message.author.name} ({message.channel.id}): {message.content}"
            )
            await self.errorChannel.send(
                f"DM by {message.author.name} ({message.channel.id}): {message.content}"
            )

    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):
        if reaction.message_id == 1201493634218995774:
            guild = await self.fetch_guild(reaction.guild_id)
            role = guild.get_role(1201294515621867621)

            await reaction.member.add_roles(role)

        if reaction.channel_id != self.ccChannel.id:
            return

        message = await self.ccChannel.fetch_message(reaction.message_id)

        if (
            reaction.emoji.name == "✅"
            and reaction.event_type == "REACTION_ADD"
            and utils.hasPermissions(user=reaction.member, role=config.ccOfficialRole)
        ):
            guild = await self.fetch_guild(reaction.guild_id)
            role = guild.get_role(config.connectedRole)

            await message.author.add_roles(
                role, reason=f"Verified by {reaction.member.display_name}"
            )
            logging.info(
                f"@Connected role added to {message.author.display_name} by {reaction.member.display_name}"
            )

    async def on_member_join(self, user: discord.Member):
        str = f"Hey {user.mention}, welcome to **Ultimate Racing 2D eSports**!\nCheck https://discord.com/channels/449754203238301698/902522821761187880/956575872909987891 to get involved!"
        channel = await self.fetch_channel(449755432202928128)
        await channel.send(str)
        with open(config.welcomeMessagePath) as f:
            text = f.read()

        await user.send(text)

    async def devCommands(self, message: discord.Message):
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
            message.content.startswith("$delete")
            and message.author.id == 493028834640396289
        ):
            str = message.content.split("-")
            try:
                await self.deleteMessage(str[1], str[2])
            except:
                await self.errorChannel.send("Error during replying message")

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

        if message.content.startswith("$history") and (
            message.author.id == 493028834640396289
            or message.author.id == 1181521363127767130
        ):
            file = discord.File("./data/history.json")
            await self.reportChannel.send(file=file)

    async def sendReport(self, data: violations.ReportData):
        view = views.ReportView(self, data)
        message = await self.reportChannel.send(embed=view.embed, view=view)

        await self.reportChannel.create_thread(
            name=f"Report {data.offender.display_name} ({data.id})",
            message=message,
            auto_archive_duration=1440,
        )

        await message.add_reaction("👍")
        await message.add_reaction("👎")

    async def sendReminder(self, data: violations.ReportData, offence=True) -> None:
        view = views.ReminderView(self, data)

        if offence:
            await data.offender.send(embed=view.embed, view=view)
        await data.creator.send(embed=view.embed)

    async def deleteMessage(self, channelId: int, messageId: int) -> None:
        channel = await self.fetch_channel(channelId)
        msg = await channel.fetch_message(messageId)
        await msg.delete()

    async def sendMessage(self, msg: str, channelId: int) -> None:
        channel = self.get_channel(channelId)
        await channel.send(msg)

    async def archiveThread(self, id: str) -> None:
        threads = self.reportChannel.threads
        for t in threads:
            if t.name.find(id) != -1:
                await t.edit(archived=True)

    def getCurrentRound(self, league: str) -> int:
        if league in self.schedule.keys():
            rounds = self.schedule[league]["rounds"]

            for i in range(0, len(rounds)):
                if rounds[i] > datetime.utcnow():
                    break

            if (
                datetime.utcnow()
                < self.schedule[league]["rounds"][i]
                + config.reportWindowDelta[league]
            ):
                return i

            return i + 1

        return 0

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        logging.error(f"Error: {event_method}")


def run():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    bot = MikeyBot(intents=intents, command_prefix=".")
    bot.run(config.Token, reconnect=True)


async def reconnect(bot):
    await bot.close()
    run()
