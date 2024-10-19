import datetime
import discord
from MikeyBotInterface import MikeyBotInterface
from database.beans import League, Race, Report, Rule, VoteType
from database.databaseHandler import Database
import utils


class UserDAO:
    def __init__(self, bot: MikeyBotInterface, dbHandler: Database) -> None:
        self.dbHandler = dbHandler
        self.bot = bot

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

    def setNumber(self, id_user: int, number: int) -> None:
        query = """
            UPDATE Users
            SET number = %s
            WHERE id = %s
        """

        values = (number, id_user)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()

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
            SELECT *
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
            league=result[3],
            season=result[4],
            round=result[5],
            description=result[6],
            rule=RuleDAO(self.dbHandler).getRule(result[7]),
            proof=result[8],
            penalty=result[9],
            aggravated=result[10],
            notes=result[11],
            active=result[12],
            timestamp=result[13],
        )

        return report

    async def getActiveReports(self) -> tuple[Report]:
        query = """
            SELECT `id`
            FROM Reports
            WHERE `active` = TRUE
        """

        values = ()
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
        timestamp = datetime.datetime.utcnow()

        query = """
            INSERT INTO Reports (id, sender, offender, league, season, round, description, proof, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            id,
            sender.id,
            offender.id,
            str(race.league),
            race.season,
            race.round,
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
            WHERE offender = %s AND rule = %s AND league = %s AND season = %s AND round = %s AND active = FALSE 
        """

        values = (offender.id, rule.id, str(race.league), race.season, race.round)
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


class AttendanceDAO:
    def __init__(self, dbHandler: Database) -> None:
        self.dbHandler = dbHandler

    def getAttendances(self, user: discord.Member, league: League) -> tuple[Race]:
        query = """
            SELECT league, season, round
            FROM Attendance
            WHERE user = %s AND league = %s
            ORDER BY season, round
        """

        values = (user.id, str(league))

        self.dbHandler.cursor.execute(query, values)
        results = self.dbHandler.cursor.fetchall()

        races = []
        for line in results:
            races.append(Race(league=line[0], season=line[1], round=line[2]))

        return tuple(races)

    def deleteAttendances(self, race: Race) -> None:
        """
        Deletes all attendances of a specific round.

        Parameters
        -----------
        - race : `Race`
            The object describing the round to teh delete its attendance.
        """

        query = """
            DELETE
            FROM Attendance
            WHERE league = %s AND season = %s AND round = %s
        """

        values = (str(race.league), race.season, race.round)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()

    def insertAttendance(self, user_id: int, race: Race) -> None:
        query = """
            INSERT INTO Attendance (user, league, season, round) 
            VALUES (%s, %s, %s, %s)
        """

        values = (user_id, str(race.league), race.season, race.round)

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()
