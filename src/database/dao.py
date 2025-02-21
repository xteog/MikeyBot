import datetime
import discord
from AI.ChatMessage import ChatMessage
from MikeyBotInterface import MikeyBotInterface
from database.beans import League, Race, Report, Rule, VoteType
from database.databaseHandler import Database
import utils


class UserDAO:
    def __init__(self, dbHandler: Database) -> None:
        self.dbHandler = dbHandler

    def getUsers(self) -> tuple[tuple[int, str]]:
        query = """
            SELECT `id`, nick
            FROM Users
            ORDER BY nick
        """

        values = ()
        self.dbHandler.cursor.execute(query, values)

        results = self.dbHandler.cursor.fetchall()

        users = []
        for line in results:
            users.append((line[0], line[1]))

        return tuple(users)

    def userExists(self, id: int) -> bool:
        query = """
            SELECT *
            FROM Users
            WHERE `id` = %s
        """
        values = (id,)

        self.dbHandler.cursor.execute(query, values)

        result = self.dbHandler.cursor.fetchall()

        if len(result) == 0:
            return False

        return True

    def getNick(self, user: discord.Member) -> str:

        if not self.userExists(user.id):
            self.insertUser(user.id, user.display_name)
            return user.display_name

        query = """
            SELECT nick
            FROM Users
            WHERE `id` = %s
        """
        values = (user.id,)

        self.dbHandler.cursor.execute(query, values)

        result = self.dbHandler.cursor.fetchall()

        return result[0][0]

    def insertUser(self, id: int, nick: str) -> None:
        query = """
            INSERT INTO Users (id, nick)
            VALUES (%s, %s)
        """

        values = (id, nick)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()

    def setNumber(self, user: discord.Member, number: int) -> None:
        query = """
            UPDATE Users
            SET `number` = %s
            WHERE id = %s
        """
        values = (number, user.id)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()

    def getNumbers(self) -> dict[str, str]:
        query = """
            SELECT `nick`, `number`
            FROM Users
            WHERE `number` IS NOT NULL
        """
        values = ()

        self.dbHandler.cursor.execute(query, values)

        result = self.dbHandler.cursor.fetchall()

        if len(result) == 0:
            return False

        return True

    def setNick(self, id_user: int, nick: str) -> None:
        query = """
            UPDATE Users
            SET nick = %s
            WHERE id = %s
        """

        values = (nick, id_user)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()


class RuleDAO:
    def __init__(self, dbHandler: Database) -> None:
        self.dbHandler = dbHandler

    def getRule(self, id: int) -> Rule:
        query = """
            SELECT *
            FROM Rules
            WHERE `id` = %s
        """

        values = (id,)
        self.dbHandler.cursor.execute(query, values)

        result = self.dbHandler.cursor.fetchall()

        if len(result) == 0:
            return None

        result = result[0]

        return Rule(
            id=result[0],
            name=result[1],
            code=result[2],
            description=result[3],
            escalation=result[4],
            de_escalation=result[5],
            levels=self.getLevels(id),
        )

    def getRules(self) -> tuple[Rule]:
        query = """
            SELECT `id`
            FROM Rules
        """

        values = ()
        self.dbHandler.cursor.execute(query, values)

        results = self.dbHandler.cursor.fetchall()

        rules = []
        for line in results:
            rules.append(self.getRule(line[0]))

        return tuple(rules)

    def getLevels(self, rule_id: int) -> tuple[str]:
        query = """
            SELECT penalty
            FROM OffenceLevels
            WHERE offence = %s
        """

        values = (rule_id,)
        self.dbHandler.cursor.execute(query, values)

        results = self.dbHandler.cursor.fetchall()

        levels = []
        for line in results:
            levels.append(line[0])

        return tuple(levels)

    def getColor(self, penalty: str) -> int:
        query = """
            SELECT color
            From OffenceLevels
            WHERE penalty = %s 
            GROUP BY color
        """

        values = (penalty,)
        self.dbHandler.cursor.execute(query, values)

        result = self.dbHandler.cursor.fetchall()

        if len(result) == 0:
            return 0xFFFFFF

        return result[0][0]


class ReportDAO:
    def __init__(self, bot: MikeyBotInterface, dbHandler: Database) -> None:
        self.dbHandler = dbHandler
        self.bot = bot

    async def getReport(self, id: int) -> Report:
        report = self.getReportSync(id)

        await report.init(bot=self.bot)

        return report

    def getReportSync(self, id: int) -> Report:
        query = """
            SELECT id, sender, offender, race, description, rule, proof, penalty, aggravated, notes, active, timestamp, message_id
            FROM Reports
            WHERE `id` = %s
        """

        values = (id,)
        self.dbHandler.cursor.execute(query, values)

        result = self.dbHandler.cursor.fetchall()

        if len(result) == 0:
            return None

        result = result[0]

        report = Report(
            id=result[0],
            senderId=result[1],
            offenderId=result[2],
            race=RaceDAO(self.dbHandler).getRaceById(id=result[3]),
            description=result[4],
            rule=RuleDAO(self.dbHandler).getRule(result[5]),
            proof=result[6],
            penalty=result[7],
            aggravated=result[8],
            notes=result[9],
            active=result[10],
            timestamp=result[11],
            messageId=result[12],
        )

        return report

    async def getActiveReports(self, user: discord.Member = None) -> tuple[Report]:
        query = """
            SELECT `id`
            FROM Reports
            WHERE `active` = TRUE AND (%s OR sender = %s)
        """

        if user == None:
            values = (True, None)
        else:
            values = (False, user.id)

        self.dbHandler.cursor.execute(query, values)

        results = self.dbHandler.cursor.fetchall()

        reports = []
        for line in results:
            reports.append(await self.getReport(line[0]))

        return tuple(reports)

    async def insertReport(
        self,
        sender: discord.Member,
        offender: discord.Member,
        race: Race,
        description: str,
        proof: str,
    ) -> Report:
        id = self.getNewId()
        timestamp = datetime.datetime.now(datetime.timezone.utc)

        query = """
            INSERT INTO Reports (id, sender, offender, race, description, proof, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            id,
            sender.id,
            offender.id,
            race.id,
            description,
            proof,
            timestamp,
        )

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()

        return await self.getReport(id)

    def closeReport(self, report: Report) -> None:
        query = """
            UPDATE Reports
            SET rule = %s, penalty = %s, aggravated = %s, notes = %s, active = %s
            WHERE id = %s;
        """
        values = (
            report.rule.id if report.rule != None else None,
            report.penalty,
            report.aggravated,
            report.notes,
            report.active,
            report.id,
        )

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()

    def searchReports(
        self,
        offender: discord.Member,
        rule: Rule,
        race: Race,
    ) -> tuple[Report]:
        query = """
            SELECT id
            FROM Reports
            WHERE offender = %s AND rule = %s AND race = %s AND active = FALSE
        """

        values = (offender.id, rule.id, race.id)
        self.dbHandler.cursor.execute(query, values)

        results = self.dbHandler.cursor.fetchall()

        reports = []
        for line in results:
            reports.append(self.getReportSync(line[0]))

        return tuple(reports)

    def getNewId(self) -> str:
        query = """
            SELECT id
            FROM Reports
        """

        values = ()
        self.dbHandler.cursor.execute(query, values)

        results = self.dbHandler.cursor.fetchall()

        ids = []
        for line in results:
            ids.append(line[0])

        newId = utils.randomString(4)

        while newId in ids:
            newId = utils.randomString(4)

        return newId

    def setMessageId(self, report: Report, message: discord.Message) -> Report:
        report.messageId = message.id
        report.message = message

        query = """
            UPDATE Reports
            SET message_id = %s
            WHERE id = %s
        """
        values = (message.id, report.id)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()

        return report


class VotesDAO:
    def __init__(self, dbHandler: Database) -> None:
        self.dbHandler = dbHandler

    def updateVote(
        self, user: discord.Member, report: Report, type: VoteType, in_favor: bool
    ) -> None:
        query = """
            UPDATE Votes
            SET in_favor = %s
            WHERE user = %s AND report = %s AND type = %s
        """

        values = (in_favor, user.id, report.id, type.value)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()

    def insertVote(
        self, user: discord.Member, report: Report, type: VoteType, in_favor: bool
    ) -> None:
        if self.voteExists(user=user, report=report, type=type):
            self.updateVote(user=user, report=report, type=type, in_favor=in_favor)
            return

        query = """
            INSERT INTO Votes (user, report, type, in_favor)
            VALUES (%s, %s, %s, %s)
        """

        values = (user.id, report.id, type.value, in_favor)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()

    def voteExists(self, user: discord.Member, report: Report, type: VoteType) -> bool:
        query = """
            SELECT *
            FROM Votes
            WHERE user = %s AND report = %s AND type = %s
        """

        values = (user.id, report.id, type.value)
        self.dbHandler.cursor.execute(query, values)

        return len(self.dbHandler.cursor.fetchall()) > 0

    def getVotesCount(self, report: Report, type: VoteType, in_favor: bool) -> int:
        query = """
            SELECT COUNT(*)
            FROM Votes
            WHERE report = %s AND type = %s AND in_favor = %s 
        """

        values = (report.id, type.value, in_favor)
        self.dbHandler.cursor.execute(query, values)

        result = self.dbHandler.cursor.fetchall()[0][0]

        return result

    def getVotesUsers(
        self, report: Report, type: VoteType, in_favor: bool
    ) -> tuple[str]:
        query = """
            SELECT user
            FROM Votes
            WHERE report = %s AND type = %s AND in_favor = %s 
        """

        values = (report.id, type.value, in_favor)
        self.dbHandler.cursor.execute(query, values)

        results = self.dbHandler.cursor.fetchall()

        users = []
        for line in results:
            users.append(line[0])

        return tuple(users)

    def deleteVotes(self, report: Report) -> None:
        query = """
            DELETE
            FROM Votes
            WHERE report = %s
        """

        values = (report.id,)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()


class RaceDAO:
    def __init__(self, dbHandler: Database) -> None:
        self.dbHandler = dbHandler

    def getRaceById(self, id: int) -> Race:
        query = """
            SELECT *
            FROM Races
            WHERE id = %s
        """

        values = (id,)

        self.dbHandler.cursor.execute(query, values)
        result = self.dbHandler.cursor.fetchall()[0]

        return Race(
            id=int(result[0]),
            league=result[1],
            season=result[2],
            round=int(result[3]),
            date=result[4],
        )

    def getCurrentRace(self, league: League, date: datetime.datetime) -> Race:
        query = """
            SELECT id
            FROM Races AS s
            WHERE s.date = (
                    SELECT MAX(t.date)
                    FROM Races AS t
                    WHERE t.league = %s AND t.date <= %s
                )
        """

        values = (str(league), date)

        self.dbHandler.cursor.execute(query, values)
        result = self.dbHandler.cursor.fetchall()[0][0]

        return self.getRaceById(id=result)


class AttendanceDAO:
    def __init__(self, dbHandler: Database) -> None:
        self.dbHandler = dbHandler

    def attendanceExists(self, user_id: discord.Member, race: Race) -> bool:
        query = """
            SELECT *
            FROM Attendance
            WHERE user = %s AND race = %s
        """

        values = (user_id, race.id)

        self.dbHandler.cursor.execute(query, values)
        results = self.dbHandler.cursor.fetchall()

        return len(results) > 0

    def getAttendances(
        self, user: discord.Member, league: League
    ) -> tuple[tuple[Race, bool]]:
        query = """
            SELECT R.id, IF(A.race = R.id, 1, 0), R.season, R.round
            FROM Races AS R
            LEFT JOIN Attendance AS A ON A.race = R.id AND A.user = %s
            WHERE R.league = %s
            ORDER BY R.season, R.round
        """

        values = (user.id, str(league))

        self.dbHandler.cursor.execute(query, values)
        results = self.dbHandler.cursor.fetchall()

        races = []
        for line in results:
            races.append(
                (
                    RaceDAO(self.dbHandler).getRaceById(id=line[0]),
                    True if line[1] == 1 else False,
                )
            )

        return tuple(races)

    def deleteAttendance(self, user: discord.Member, race: Race) -> None:
        """
        Deletes an attendance of a specific round.

        Parameters
        -----------
        - user : `discord.Member`
            The user to delete its attendance.
        - race : `Race`
            The object describing the round to delete its attendance.
        """

        if not self.attendanceExists(user_id=user.id, race=race):
            return

        query = """
            DELETE
            FROM Attendance
            WHERE user = %s AND race = %s
        """

        values = (user.id, race.id)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()

    def insertAttendance(self, user_id: int, race: Race) -> None:
        if self.attendanceExists(user_id=user_id, race=race):
            return

        query = """
            INSERT INTO Attendance (user, race) 
            VALUES (%s, %s)
        """

        values = (user_id, race.id)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()


class MessagesDAO:
    def __init__(self, dbHandler: Database) -> None:
        self.dbHandler = dbHandler

    def existsMessage(self, id: str | int) -> bool:
        query = """
            SELECT *
            FROM Messages
            WHERE id = %s
        """

        values = (id,)

        self.dbHandler.cursor.execute(query, values)
        result = self.dbHandler.cursor.fetchall()

        return len(result) > 0

    def getMessage(self, id: str | int, checkReply: bool = True) -> ChatMessage:
        if not self.existsMessage(id=id):
            return None

        query = """
            SELECT M.id AS id, U.id AS authorId, U.nick AS authorName, C.id AS channelId, C.name AS channelName, content, date, reference
            FROM Messages AS M 
                JOIN Users AS U ON M.author = U.id
                JOIN Channels AS C ON M.channel = C.id
            WHERE M.id = %s
        """
        values = (id,)

        self.dbHandler.cursor.execute(query, values)
        result = self.dbHandler.cursor.fetchall()[0]

        reference = result[7]
        if reference and checkReply:
            reference = self.getMessage(id=reference, checkReply=False)

        return ChatMessage(
            id=result[0],
            author_id=result[1],
            author_name=result[2],
            channel_id=result[3],
            channel_name=result[4],
            content=result[5],
            date=result[6],
            reference=reference,
        )

    def getMessages(self, guild: discord.Guild) -> tuple[ChatMessage]:
        query = """
            SELECT M.id AS id, U.id AS authorId, U.nick AS authorName, C.id AS channelId, C.name AS channelName, content, date, reference
            FROM Messages AS M 
                JOIN Users AS U ON M.author = U.id
                JOIN Channels AS C ON M.channel = C.id
            WHERE guild = %s
            ORDER BY date
        """
        values = (guild.id,)

        self.dbHandler.cursor.execute(query, values)
        results = self.dbHandler.cursor.fetchall()

        messages = []
        for line in results:
            reference = self.getMessage(id=line[7], checkReply=False)
            messages.append(
                ChatMessage(
                    id=line[0],
                    author_id=line[1],
                    author_name=line[2],
                    channel_id=line[3],
                    channel_name=line[4],
                    content=line[5],
                    date=line[6],
                    reference=reference,
                )
            )

        return tuple(messages)

    def insertMessage(self, message: discord.Message) -> None:
        userDAO = UserDAO(dbHandler=self.dbHandler)

        if not userDAO.userExists(id=message.author.id):
            userDAO.insertUser(id=message.author.id, nick=message.author.name)

        if self.existsMessage(id=message.id):
            return self.getMessage(id=message.id)

        if not self.existsChannel(id=message.channel.id):
            self.insertChannel(id=message.channel.id, name=message.channel.name)

        reference = None
        if message.reference:
            reference = message.reference.message_id

        query = """
            INSERT INTO Messages (id, guild, author, channel, content, date, reference)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            message.id,
            message.guild.id,
            message.author.id,
            message.channel.id,
            utils.convertMentions(message),
            message.created_at,
            reference,
        )

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()

    def deleteMessage(self, message: ChatMessage) -> None:
        query = """
            DELETE
            FROM Messages
            WHERE id = %s
        """

        values = (message.id,)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()

    def existsChannel(self, id: int) -> bool:
        query = """
            SELECT *
            FROM Channels
            WHERE id = %s
        """

        values = (id,)

        self.dbHandler.cursor.execute(query, values)
        result = self.dbHandler.cursor.fetchall()

        return len(result) > 0

    def insertChannel(self, id: int | str, name: str) -> None:
        query = """
            INSERT INTO Channels (id, name)
            VALUES (%s, %s)
        """

        values = (id, name)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()


class SummaryDAO:
    def __init__(self, dbHandler: Database) -> None:
        self.dbHandler = dbHandler

    def existsSummary(self, guild: discord.Guild) -> bool:
        query = """
            SELECT *
            FROM Summaries
            WHERE guild = %s
        """

        values = (guild.id,)

        self.dbHandler.cursor.execute(query, values)
        result = self.dbHandler.cursor.fetchall()

        return len(result) > 0

    def insertSummary(self, guild: discord.Guild, summary: str) -> None:
        query = """
            INSERT INTO Summaries (guild, summary)
            VALUES (%s, %s)
        """

        values = (guild.id, summary)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()

    def getSummary(self, guild: discord.Guild) -> str | None:
        if not self.existsSummary(guild):
            return None

        query = """
            SELECT summary
            FROM Summaries
            WHERE guild = %s
        """

        values = (guild.id,)

        self.dbHandler.cursor.execute(query, values)
        result = self.dbHandler.cursor.fetchall()

        return result[0][0]

    def updateSummary(self, guild: discord.Guild, summary: str) -> None:
        if not self.existsSummary(guild):
            self.insertSummary(guild, summary)
            return

        query = """
            UPDATE Summaries
            SET summary = %s
            WHERE guild = %s
        """

        values = (summary, guild.id)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()
