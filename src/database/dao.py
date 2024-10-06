import datetime
import logging
import discord
from discord.ext import commands

import config
from database.beans import Report, Rule
from database.databaseHandler import Database
import utils


class UserDAO:
    def __init__(self, bot: commands.Bot, dbHandler: Database) -> None:
        self.dbHandler = dbHandler
        self.bot = bot

    async def userExists(self, id: int) -> bool:
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

    def getNick(self, id: int) -> str | None:
        query = """
            SELECT nick
            FROM Users
            WHERE `id` = %s
        """
        values = (id,)

        self.dbHandler.cursor.execute(query, values)

        result = self.dbHandler.cursor.fetchall()

        if len(result) == 0:
            return None

        return result[0][0]

    async def addUser(self, id: int, nick: str) -> None:
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

    def getRules(self) -> list[Rule]:
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

        return rules

    def getLevels(self, rule_id: int) -> list[str]:
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

        return levels


class ReportDAO:
    def __init__(self, bot: commands.Bot, dbHandler: Database) -> None:
        self.dbHandler = dbHandler
        self.bot = bot

    async def getReport(self, id: int) -> Report:
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

        await report.init(
            bot=self.bot,
            senderId=result[1],
            offenderId=result[2],
        )

        return report

    async def getActiveReports(self) -> list[Report]:
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

        return reports

    async def addReport(
        self,
        sender: discord.Member,
        offender: discord.Member,
        league: str,
        season: int,
        round: int,
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
            league,
            season,
            round,
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
            report.rule.id,
            report.penalty,
            report.aggravated,
            report.notes,
            report.active,
            report.id,
        )

        self.dbHandler.cursor.execute(query, values)
        self.dbHandler.database.commit()

    def getPreviousOffences(self, rule_id: int, league: str) -> list[Report]:
        query = """
            SELECT id
            FROM Reports
            WHERE rule = %s, league = %s
        """

        values = (rule_id, league)
        self.dbHandler.cursor.execute(query, values)

        results = self.dbHandler.cursor.fetchall()

        reports = []
        for line in results:
            reports.append(self.getReport(line[0]))

        return reports


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
