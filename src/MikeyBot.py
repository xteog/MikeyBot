import asyncio
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import re
from MikeyBotInterface import MikeyBotInterface
from database.beans import League, Race, Report, Rule, VoteType, getLeague
from database.dao import AttendanceDAO, RaceDAO, ReportDAO, RuleDAO, UserDAO, VotesDAO
from database.databaseHandler import Database
import google_sheets.api as api
import utils
import discord
import slashCommands
import views
import config
import logging
import sys
import lobby as lobby
import google_sheets.commands as sheets

# import load_log


class MikeyBot(MikeyBotInterface):
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
        awake_at = datetime.now(timezone.utc)

        await self.wait_until_ready()
        while not self.ready:
            await asyncio.sleep(1)

        while not self.is_closed():
            try:

                for lobbies in self.lobbiesLists:
                    await lobbies.update()

                if awake_at < datetime.now(timezone.utc):
                    awake_at = datetime.now(timezone.utc) + timedelta(hours=1)

                    activeReports = await ReportDAO(
                        self, self.dbHandler
                    ).getActiveReports()

                    for thread in self.reportChannel.threads:
                        match = re.search(r"\d{4}", thread.name)
                        id = match.group()

                        found = False
                        for report in activeReports:
                            if id == report.id:
                                found = True

                        if found:
                            await thread.edit(archived=False)
                        else:
                            await thread.edit(archived=True)

                    for league in League:
                        currRace = self.getCurrentRace(league)
                        now = datetime.now(timezone.utc)
                        reportWindowNotice = utils.load_reportWindowNotice()

                        if (
                            reportWindowNotice[str(league)] < currRace.date
                            and now < utils.closeWindowDate(race=currRace)
                            and str(league) in config.leaguesChannelIds.keys()
                        ):
                            msg = f"Reports window is now open until <t:{int(utils.closeWindowDate(race=currRace).timestamp())}:f>. Use </report:1194650188376199239> to report"

                            await self.sendMessage(
                                msg, config.leaguesChannelIds[str(league)]
                            )

                            reportWindowNotice[str(league)] = datetime.now(timezone.utc)
                            utils.update_reportWindowNotice()

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

        if message.content.startswith("$load_attendance") and utils.hasPermissions(
            message.author, roles=[config.stewardsRole, config.devRole]
        ):
            await message.delete()
            await self.updateAttendanceSheet()

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

        row = [
            data.id,
            dao.getNick(data.offender),
            data.penalty,
            str(data.aggravated),
            data.race.season,
            data.race.round,
            str(data.rule),
            data.proof,
            data.notes,
            dao.getNick(data.sender),
            data.description,
            data.timestamp.strftime(config.timeFormat),
        ]

        if data.penalty == "No offence":
            return

        sheets.appendRow(row, sheetName=str(data.race.league))

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
        if offence:
            embed = views.ReportEmbed(
                self,
                data,
                permission=False,
            )

            await data.offender.send(embed=embed)
        else:
            embed = views.ReportEmbed(
                self,
                data,
                permission=False,
            )

        await data.sender.send(embed=embed)

    async def openReport(
        self,
        sender: discord.Member,
        offender: discord.Member,
        race: Race,
        description: str,
        proof: str,
    ) -> Report:
        self.updateAttendance(user=offender, race=race, attended=True)

        dao = ReportDAO(self, self.dbHandler)

        report = await dao.insertReport(
            sender=await self.getUser(sender.id),
            offender=await self.getUser(offender.id),
            race=race,
            description=description,
            proof=proof,
        )

        await self.sendReport(report)

        return report

    def getColor(self, report: Report) -> int:
        return RuleDAO(self.dbHandler).getColor(penalty=report.penalty)

    def getAttendances(
        self, user: discord.Member, league: League
    ) -> tuple[tuple[Race, bool]]:
        return AttendanceDAO(self.dbHandler).getAttendances(user=user, league=league)

    def getOffenceLevel(self, report: Report) -> int:
        attendances = self.getAttendances(
            user=report.offender, league=report.race.league
        )

        if len(attendances) == 0:
            return 0

        level = 0

        for attendance in attendances:
            if attendance[1]:
                attendance = attendance[0]

                offences = ReportDAO(self, self.dbHandler).searchReports(
                    offender=report.offender, rule=report.rule, race=attendance
                )

                if len(offences) == 0:
                    level -= report.rule.de_escalation
                    level = max(0, level)

                else:
                    for offence in offences:

                        if offence.aggravated:
                            level += 2 * offence.rule.escalation
                        else:
                            level += offence.rule.escalation

                        level = min(8, level)
                        level = max(0, level)

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

    def getCurrentRace(self, league: League) -> Race:
        return RaceDAO(self.dbHandler).getCurrentRace(
            league=league, date=datetime.now(timezone.utc)
        )

    async def getUser(self, id: int) -> discord.Member | None:
        dao = UserDAO(self, self.dbHandler)

        guild = await self.fetch_guild(self.server)
        try:
            member = await guild.fetch_member(id)
        except:
            return None

        if not dao.userExists(id):
            dao.insertUser(id, member.display_name)

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
        VotesDAO(self.dbHandler).insertVote(
            user=user, report=report, type=type, in_favor=in_favor
        )

    def getRace(self, id: int) -> Race:
        return RaceDAO(self.dbHandler).getRaceById(id=id)

    def updateAttendance(
        self, user: discord.Member, race: Race, attended: bool
    ) -> None:
        if attended:
            AttendanceDAO(self.dbHandler).insertAttendance(user_id=user.id, race=race)
        else:
            AttendanceDAO(self.dbHandler).deleteAttendance(user=user, race=race)

    async def updateAttendanceSheet(self) -> None:
        sheets.statusAttendance("Loading...")

        race, data = sheets.loadAttendance()

        attendanceDao = AttendanceDAO(self.dbHandler)
        userDao = UserDAO(self, self.dbHandler)

        attendanceDao.deleteAttendances(race=race)

        for row in data[:1000]:
            try:
                id = row[0]
                nick = row[1]

                if row[2] == "TRUE":
                    attendance = True
                elif row[2] == "FALSE":
                    attendance = False
                else:
                    raise ValueError("Attendance is not bool")

            except Exception as e:
                sheets.statusAttendance(f"Error: row {id} not valid. {e}")
                logging.warning(f"{id} not valid.  {e}")
                return

            if id == "":
                break

            if not userDao.userExists(id):
                user = await self.getUser(id)

                if user == None:
                    sheets.statusAttendance(f"Error: user {id} not found")
                    logging.warning(f"{id} not valid")
                    return
            else:
                userDao.setNick(id_user=id, nick=nick)

            if attendance:
                attendanceDao.insertAttendance(user_id=id, race=race)

        sheets.resetAttendance(users=userDao.getUsers())

        sheets.statusAttendance("Ready")

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        logging.error(f"Error: {event_method}")


def run():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    bot = MikeyBot(intents=intents, command_prefix=".")
    bot.run(config.Token, reconnect=True)
