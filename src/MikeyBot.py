import asyncio
from datetime import datetime
from datetime import timedelta
import re
from MikeyBotInterface import MikeyBotInterface
from database.beans import Report, Rule, VoteType
from database.dao import ReportDAO, RuleDAO, UserDAO, VotesDAO
from database.databaseHandler import Database
import googleApi
import utils
import discord
import slashCommands
import views
import config
import logging
import sys
import lobby

# import load_log


class MikeyBot(MikeyBotInterface):  # TODO Controller
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

        self.lobbiesLists = []
        self.reportWindowNotice = utils.load_reportWindowNotice()
        self.schedule = utils.loadSchedule()

        self.ready = False

    async def on_ready(self):
        activity = discord.Game(name="Starting...", type=discord.ActivityType.streaming)
        await self.change_presence(
            status=discord.Status.do_not_disturb, activity=activity
        )

        await self.add_cog(
            slashCommands.setup(self), guild=discord.Object(id=self.server)
        )
        await self.tree.sync(guild=discord.Object(id=self.server))
        self.errorChannel = self.get_channel(config.errorChannelId)
        self.reportChannel = self.get_channel(config.reportChannelId)
        self.ccChannel = self.get_channel(config.ccChannelId)
        self.dmsChannel = self.get_channel(1151113045997797440)
        self.lobbiesChannel = self.get_channel(config.lobbiesChannelId)

        self.dbHandler = Database()
        self.dbHandler.connect()

        reports = await ReportDAO(self, self.dbHandler).getActiveReports()

        try:
            for r in reports:
                view = views.ReportView(bot=self, data=r)
                self.add_view(view)
            self.add_view(views.SwitchView(self))

        except Exception as e:
            print(e)

        if sys.argv[1] == "run":
            self.lobbiesLists = [
                lobby.LobbiesList(0, self, self.lobbiesChannel.id, "pc"),
                lobby.LobbiesList(1, self, 1142190503081803898, "mobile"),
            ]

        self.ready = True
        print("Mikey is up")

        await self.change_presence(status=discord.Status.online)

        """
        guild = await self.fetch_guild(self.server)
        role = guild.get_role(967141781353431091)

        async for member in guild.fetch_members():
            await member.remove_roles(role)

        print("Done")
        """

    async def setup_hook(self) -> None:
        self.bg_task = self.loop.create_task(self.background_task())

    async def background_task(self):
        awake_at = datetime.utcnow()

        await self.wait_until_ready()
        while not self.ready:
            await asyncio.sleep(1)

        while not self.is_closed():
            try:

                for lobbies in self.lobbiesLists:
                    await lobbies.update()

                if awake_at < datetime.utcnow():
                    awake_at = datetime.utcnow() + timedelta(hours=1)

                    activeReports = await ReportDAO(
                        self, self.dbHandler
                    ).getActiveReports()

                    for thread in self.reportChannel.threads:
                        if not thread.archived:
                            match = re.search(r"\d{4}", thread.name)
                            id = int(match.group())

                            for report in activeReports:
                                if id == report.id and not report.active:
                                    await thread.edit(archived=True)

                            if len(activeReports) > 0 and not activeReports[0].active:
                                await thread.edit(archived=True)

                    for league in config.reportWindowDelta.keys():
                        open_date = self.schedule[league]["rounds"][
                            self.getCurrentRound(league) - 1
                        ]

                        if (
                            self.reportWindowNotice[league] < open_date
                            and datetime.utcnow()
                            < open_date + config.reportWindowDelta[league]
                            and league in config.leaguesChannelIds.keys()
                        ):
                            if datetime.utcnow() > open_date:
                                msg = f"Reports window is now open until <t:{int((open_date + config.reportWindowDelta[league]).timestamp())}:f>. Use </report:1194650188376199239> to report"
                                await self.sendMessage(
                                    msg, config.leaguesChannelIds[league]
                                )

                                self.reportWindowNotice[league] = datetime.utcnow()
                                utils.update_reportWindowNotice(self.reportWindowNotice)
                            elif datetime.utcnow() + timedelta(minutes=59) > open_date:
                                awake_at = datetime.utcnow() + (
                                    open_date - datetime.utcnow()
                                )

                await asyncio.sleep(60)
            except Exception as e:
                logging.error(e)

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        await self.devCommands(message)

        if message.mention_everyone:
            await message.author.ban(reason="Gotcha u moron", delete_message_seconds=60)
            await message.channel.send("Gotcha u moron")

        if message.channel.id == self.reportChannel.id:
            await self.deleteMessage(self.reportChannel.id, message.id)

        if message.channel.id == 930047083510132746:
            with open(config.connectionTipsPath) as f:
                text = f.read()
            await self.pingMessage(930047083510132746, text)

        if message.channel.id == 990229907479076914:
            channel = self.get_channel(990229907479076914)
            async for msg in channel.history(limit=100):
                if msg.author == self.user and len(msg.attachments) > 0:
                    text = f"## Choose your number\nType </set_number:1191721403163095071>, choose a number and check from the list shown if it is available.\nYou can also check {msg.attachments[0].url} which numbers are available."
                    break
            await self.pingMessage(channel.id, text)

        for lobbies in self.lobbiesLists:
            if message.channel.id == lobbies.channelId:
                await lobbies.ping()

        if message.channel.id == 962786348635406367:
            if len(message.attachments) == 0:
                await self.deleteMessage(962786348635406367, message.id)
                await self.sendMessage(
                    f"{message.author.mention} write here", 963011311518773278
                )

        if isinstance(message.channel, discord.DMChannel):
            logging.info(
                f"DM by {message.author.name} ({message.channel.id}): {message.content}"
            )
            await self.dmsChannel.send(
                f"DM by {message.author.name} ({message.channel.id}): {message.content}"
            )

    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):
        try:
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
                and utils.hasPermissions(
                    user=reaction.member, role=config.ccOfficialRole
                )
            ):
                guild = await self.fetch_guild(reaction.guild_id)
                role = guild.get_role(config.connectedRole)

                await message.author.add_roles(
                    role, reason=f"Verified by {self.getNick(reaction.member)}"
                )
                logging.info(
                    f"@Connected role added to {self.getNick(message.author)} by {self.getNick(reaction.member)}"
                )
        except Exception as e:
            logging.error(f"Reaction error: {e}")

    async def on_member_join(self, user: discord.Member):
        str = f"Hey {user.mention}, welcome to **Ultimate Racing 2D eSports**!\nCheck https://discord.com/channels/449754203238301698/902522821761187880/956575872909987891 to get involved!"
        channel = await self.fetch_channel(449755432202928128)

        # await channel.send(str) TODO
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

    async def pingMessage(self, channelId: int, message: str) -> None:
        oldMessage = None

        channel = self.get_channel(channelId)
        i = 0
        async for msg in channel.history(limit=100):
            if msg.author == self.user and msg.content.startswith(message[:5]):
                oldMessage = msg
                break
            i += 1

        if i < 1:
            return

        if oldMessage != None:
            await oldMessage.delete()
            await channel.send(message)
        else:
            await channel.send(message)

    def updateSpreadSheet(self, data: Report) -> None:
        dao = UserDAO(self, self.dbHandler)

        season, round = utils.formatLeagueRounds(
            league=data.league, season=data.season, round=data.round
        )

        row = [
            data.id,
            dao.getNick(data.offender),
            data.penalty,
            str(data.aggravated),
            season,
            round,
            str(data.rule),
            data.proof,
            data.notes,
            dao.getNick(data.sender),
            data.description,
            data.timestamp.strftime(config.timeFormat),
        ]

        if data.penalty == "No offence":
            return

        outcome = False
        i = 0
        while not outcome and i < 3:
            outcome = googleApi.appendRow(row, sheetName=data.league)
            i += 1

        if not outcome:
            logging.error("SpreadSheet not updated")

    def getNick(self, member: discord.Member) -> str:
        return UserDAO(self, self.dbHandler).getNick(member)

    async def sendReport(self, data: Report):
        view = views.ReportView(self, data)
        message = await self.reportChannel.send(embed=view.embed, view=view)

        await self.reportChannel.create_thread(
            name=f"Report {self.getNick(data.offender)} ({data.id})",
            message=message,
            auto_archive_duration=1440,
        )

    async def sendReminder(self, data: Report, offence=True) -> None:
        embed = views.ReportEmbed(data, permission=False)

        if offence:
            await data.offender.send(embed=embed)

        await data.sender.send(embed=embed)

    async def openReport(
        self,
        sender: discord.Member,
        offender: discord.Member,
        league: str,
        season: int,
        round: int,
        description: str,
        proof: str,
    ) -> Report:
        dao = ReportDAO(self, self.dbHandler)

        report = await dao.addReport(
            sender=await self.getUser(sender.id),
            offender=await self.getUser(offender.id),
            league=league,
            season=season,
            round=round,
            description=description,
            proof=proof,
        )

        await self.sendReport(report)

        return report

    def getColor(self, offence: Rule, level: int) -> int:
        return RuleDAO(self.dbHandler).getColor(offence=offence, level=level)

    def getOffenceLevel(self, report: Report) -> int:
        previousOffences = ReportDAO(self, self.dbHandler).getPreviousOffences(offender=report.offender,
            rule=report.rule, league=report.league
        )

        if len(previousOffences) == 0:
            return 0

        level = 0
        prev_round = 10 * previousOffences[0].season + previousOffences[0].round - 1

        for _offence in previousOffences:
            curr_round = 10 * _offence.season + _offence.round - 1

            if _offence.aggravated:
                level += 2 * report.rule.escalation
            else:
                level += report.rule.escalation

            level = min(8, level)

            if curr_round > prev_round:
                level -= report.rule.de_escalation * (curr_round - prev_round - 1)

            level = max(0, level)

            prev_round = curr_round

        return level

    def getPenalty(self, report: Report) -> str:
        level = self.getOffenceLevel(report=report)

        penalty = report.rule.levels[level]

        if report.aggravated:
            penalty += (
                " + " + report.rule.levels[min(8, level + report.rule.escalation)]
            )

        return penalty

    async def closeReport(self, report: Report, offence: bool) -> Report:
        dao = ReportDAO(self, self.dbHandler)

        report.active = False

        if offence:
            report.penalty = self.getPenalty(report=report)
        else:
            report.rule = None
            report.aggravated = False
            report.penalty = "No Offence"

        if offence:
            self.updateSpreadSheet(data=report)

        await self.sendReminder(data=report, offence=offence)

        VotesDAO(self.dbHandler).deleteVotes(report=report)

        await self.archiveThread(report.id)

        dao.closeReport(report=report)
        report = await dao.getReport(id=report.id)

        return report

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

            found = False
            for i in range(0, len(rounds)):
                if rounds[i] > datetime.utcnow():
                    found = True
                    break

            if found:
                return i

            return i + 1

        return 1

    async def getUser(self, id: int) -> discord.Member | None:
        dao = UserDAO(self, self.dbHandler)

        guild = await self.fetch_guild(self.server)
        member = await guild.fetch_member(id)

        if not dao.userExists(id):
            dao.addUser(id, member.display_name)

        return member

    def getRules(self) -> tuple[Rule]:
        return RuleDAO(self.dbHandler).getRules()

    def getRule(self, id: int) -> Rule:
        return RuleDAO(self.dbHandler).getRule(id)

    def getVotesCount(self, report: Report, type: VoteType, in_favor: bool) -> int:
        return VotesDAO(self.dbHandler).getVotesCount(
            report=report, type=type, in_favor=in_favor
        )

    async def getVotesUsers(
        self, report: Report, type: VoteType, in_favor: bool
    ) -> tuple[discord.Member]:
        users = VotesDAO(self.dbHandler).getVotesUsers(
            report=report, type=type, in_favor=in_favor
        )

        users = list(users)
        for i in range(len(users)):
            users[i] = await self.getUser(id=users[i])

        return users

    async def addVote(
        self, user: discord.Member, report: Report, type: VoteType, in_favor: bool
    ) -> None:
        user = await self.getUser(user.id)
        VotesDAO(self.dbHandler).addVote(
            user=user, report=report, type=type, in_favor=in_favor
        )

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        logging.error(f"Error: {event_method}")


def run():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    bot = MikeyBot(intents=intents, command_prefix=".")
    bot.run(config.Token, reconnect=True)
