import asyncio
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import re
from AI.Chat import Chat
from AI.ChatMessage import ChatMessage, ChatResponse
from MikeyBotInterface import MikeyBotInterface
import commands
from database.beans import League, Race, Report, Rule, VoteType, getLeague
from database.dao import (
    AttendanceDAO,
    MessagesDAO,
    RaceDAO,
    ReportDAO,
    RuleDAO,
    SummaryDAO,
    UserDAO,
    VotesDAO,
)
from database.databaseHandler import Database
from exceptions import RateLimitException, ResponseException
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
            raise ValueError()

        self.serverId = config.serverId
        self.dmsChannel = None
        self.errorChannel = None
        self.reportChannel = None
        self.ccChannel = None
        self.lobbiesChannel = None

        self.lobbiesLists = []
        self.geminiChats = {}

        self.ready = False

    async def on_ready(self):
        activity = discord.Game(name="Starting...", type=discord.ActivityType.streaming)
        await self.change_presence(
            status=discord.Status.do_not_disturb, activity=activity
        )

        await self.add_cog(
            slashCommands.setup(self), guild=discord.Object(id=self.serverId)
        )

        await self.tree.sync(guild=discord.Object(id=self.serverId))
        self.errorChannel = self.get_channel(config.errorChannelId)
        self.reportChannel = self.get_channel(config.reportChannelId)
        self.ccChannel = self.get_channel(config.ccChannelId)
        self.dmsChannel = self.get_channel(1151113045997797440)
        self.lobbiesChannel = self.get_channel(config.lobbiesChannelId)

        self.dbHandler = Database()
        self.dbHandler.connect()

        for guild in self.guilds:
            try:
                self.geminiChats[guild.id] = Chat(self, guild=guild)
            except:
                logging.warning(f"{guild.name} not found")

        try:

            reports = await ReportDAO(self, self.dbHandler).getActiveReports()
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

                    activeReports = await self.getActiveReports()

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
                        if str(league) in config.leaguesChannelIds.keys():
                            currRace = self.getCurrentRace(league)
                            now = datetime.now(timezone.utc)
                            reportWindowNotice = utils.load_reportWindowNotice()

                            if (
                                reportWindowNotice[str(league)].timestamp()
                                < currRace.date.timestamp()
                                and now.timestamp()
                                < utils.closeWindowDate(race=currRace).timestamp()
                            ):
                                msg = f"Reports window is now open until <t:{int(utils.closeWindowDate(race=currRace).timestamp())}:f>. Use </report:1194650188376199239> to report"

                                await self.sendMessage(
                                    msg, config.leaguesChannelIds[str(league)]
                                )

                                reportWindowNotice[str(league)] = datetime.now(
                                    timezone.utc
                                )
                                utils.update_reportWindowNotice(reportWindowNotice)

                await asyncio.sleep(60)
            except Exception as e:
                logging.error(e)

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        await self.devCommands(message)

        reply = False
        if message.reference:
            repliedMsg = await message.channel.fetch_message(
                message.reference.message_id
            )
            if repliedMsg.author == self.user:
                reply = True

        if (
            message.content
            and message.guild.id
            in [1142186588537880637, 881632566589915177, 449754203238301698]
            and (self.user in message.mentions or reply)
        ):
            async with message.channel.typing():
                messagesHistory = []
                chat = self.getGeminiChat(guild=message.guild)

                try:
                    response = await chat.sendMessage(message=message)

                    if response.getText():
                        msg = await self.replyMessage(message, response.getText())
                        msg.content = response.content
                        messagesHistory.append(msg)

                    await self.executeCommand(
                        chat=chat,
                        channel=message.channel,
                        response=response
                    )

                except ResponseException as e:
                    await self.errorHandlingAI(
                        chta=chat, channel=message.channel, error=e
                    )
                except RateLimitException:
                    await self.replyMessage(
                        message,
                        "At the moment I'm experiencing high traffic. Please wait a few minutes before asking for a response again.",
                    )
                except Exception as e:
                    await message.reply(e)
                    raise e

                for msg in messagesHistory:
                    chat.updateHistory(msg)

        if message.mention_everyone:
            await message.author.ban(
                reason="Silence. Enforced.", delete_message_seconds=60
            )
            await message.channel.send("Silence. Enforced.")

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
        dao = UserDAO(self.dbHandler)

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
        return UserDAO(self.dbHandler).getNick(member)

    async def sendReport(self, data: Report):
        view = views.ReportView(self, data)
        message = await self.reportChannel.send(embed=view.embed, view=view)

        await self.reportChannel.create_thread(
            name=f"Report {self.getNick(data.offender)} ({data.id})",
            message=message,
            auto_archive_duration=1440,
        )

        return message

    async def sendPenalty(self, data: Report, offence=True) -> None:
        if offence:
            embed = views.ReportEmbed(
                self,
                data,
                permission=False,
            )

            await data.offender.send(embed=embed)

            if data.penalty != "Warning":
                msg = f"[{data.id}] {str(data.race)} {self.getNick(data.offender)}({data.offender.mention}) {data.penalty}"

                user = await self.getUser(id=992795187900321802)
                await user.send(msg)

                user = await self.getUser(id=666666262490906647)
                await user.send(msg)

                user = await self.getUser(id=493028834640396289)
                await user.send(msg)
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

        dao = ReportDAO(self, self.dbHandler)

        report = await dao.insertReport(
            sender=await self.getUser(sender.id),
            offender=await self.getUser(offender.id),
            race=race,
            description=description,
            proof=proof,
        )

        message = await self.sendReport(report)

        report = dao.setMessageId(report, message)

        self.updateAttendance(user=offender, race=race, attended=True)

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
        max_level = len(report.rule.levels) - 1

        for attendance in attendances:
            if attendance[1]:

                offences = ReportDAO(self, self.dbHandler).searchReports(
                    offender=report.offender, rule=report.rule, race=attendance[0]
                )

                if len(offences) > 0:
                    for offence in offences:

                        if offence.aggravated:
                            level += 2 * offence.rule.escalation
                        else:
                            level += offence.rule.escalation

                        level = min(max_level, level)
                elif attendance[0].date < report.race.date:
                    level -= report.rule.de_escalation
                    level = max(0, level)

                else:
                    for offence in offences:

                        if offence.aggravated:
                            level += 2 * offence.rule.escalation
                        else:
                            level += offence.rule.escalation

                        level = min(max_level, level)

        return level

    def getPenalty(self, report: Report) -> str:
        if report.race.league != League.OT:
            level = self.getOffenceLevel(report=report)
        else:
            level = 0

        penalty = report.rule.levels[level]

        if report.aggravated:
            max_level = len(report.rule.levels) - 1
            penalty += (
                " + "
                + report.rule.levels[min(max_level, level + report.rule.escalation)]
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

        await self.sendPenalty(data=report, offence=offence)

        VotesDAO(self.dbHandler).deleteVotes(report=report)

        await self.archiveThread(report.id)

        dao.closeReport(report=report)
        report = await dao.getReport(id=report.id)

        return report

    async def deleteMessage(self, channelId: int, messageId: int) -> None:
        channel = await self.fetch_channel(channelId)
        msg = await channel.fetch_message(messageId)
        await msg.delete()

    async def sendMessage(self, msg: str, channelId: int) -> discord.Message:
        if msg:
            channel = self.get_channel(channelId)
            return await channel.send(msg[: config.maxCharsText - 1])

        return None

    async def replyMessage(
        self, message: discord.Message, reply: str
    ) -> discord.Message:
        if reply:
            return await message.reply(reply[: config.maxCharsText - 1])

        return None

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
        dao = UserDAO(self.dbHandler)

        guild = await self.fetch_guild(self.serverId)
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

    async def getActiveReports(self, user: discord.Member = None) -> tuple[Report]:
        activeReports = await ReportDAO(self, self.dbHandler).getActiveReports(
            user=user
        )

        return activeReports

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
        userDao = UserDAO(self.dbHandler)

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

    async def errorHandlingAI(
        self,
        chat: Chat,
        channel: discord.TextChannel,
        error: Exception,
        tries: int = 1,
    ) -> None:
        logging.error(error)
        if tries >= 3:
            raise Exception("Too many tries, the command can't be executed.")

        chat = self.getGeminiChat(guild=channel.guild)

        try:
            response = await chat.sendSystemMessage(error.__str__())
            if response.getText():
                msg = await channel.send(response.getText())
            chat.updateHistory(msg)
            await self.executeCommand(
                chat=chat, channel=channel, response=response, tries=tries + 1
            )
        except ResponseException as e:
            await self.errorHandlingAI(
                chat=chat, channel=channel, error=e, tries=tries + 1
            )

    async def executeCommand(
        self,
        chat: Chat,
        channel: discord.TextChannel,
        response: ChatResponse,
        tries: int = 0,
    ) -> None:

        if tries >= 3:
            raise Exception("Too many tries, the command can't be executed.")

        chat = self.getGeminiChat(guild=channel.guild)

        if response.getCommand():
            result = await commands.executeCommand(
                bot=self, command=response.getCommand()
            )
            newResponse = await chat.sendSystemMessage(result)
            if newResponse.getText():
                msg = await self.sendMessage(
                    newResponse.getText(), channelId=channel.id
                )

            chat.updateHistory(msg)

            await self.executeCommand(
                chat=chat, channel=channel, response=newResponse, tries=tries + 1
            )

    def insertMessage(self, message: discord.Message) -> ChatMessage:
        dao = MessagesDAO(self.dbHandler)
        dao.insertMessage(message)
        return dao.getMessage(id=message.id)

    def getMessages(self, guild: discord.Guild) -> tuple[ChatMessage]:
        dao = MessagesDAO(self.dbHandler)
        return dao.getMessages(guild=guild)

    def getSummary(self, guild: discord.Guild) -> str | None:
        dao = SummaryDAO(self.dbHandler)

        return dao.getSummary(guild=guild)

    def updateSummary(self, guild: discord.Guild, summary: str) -> None:
        dao = SummaryDAO(self.dbHandler)

        dao.updateSummary(guild=guild, summary=summary)

    def deleteMessages(self, messages: tuple[ChatMessage]) -> None:
        dao = MessagesDAO(self.dbHandler)
        for message in messages:
            dao.deleteMessage(message=message)

    def getGeminiChat(self, guild: discord.Guild) -> Chat:
        return self.geminiChats[guild.id]

    async def on_error(self, *args, **kwargs) -> None:
        logging.error(sys.exception().with_traceback())


def run():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    bot = MikeyBot(intents=intents, command_prefix=".")
    bot.run(config.Token, reconnect=True)
