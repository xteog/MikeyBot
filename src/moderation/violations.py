import logging
import utils
import config
import discord
import datetime


def loadRules() -> dict:
    rules = utils.read(config.rulesPath)
    rulesFormatted = {}

    for i in rules.keys():
        if isinstance(rules[i], dict):
            for j in rules[i].keys():
                if isinstance(rules[i][j], dict):
                    for m in rules[i][j].keys():
                        if isinstance(rules[i][j][m], dict):
                            for n in rules[i][j][m].keys():
                                rulesFormatted[f"{i}.{j}.{m}.{n}"] = rules[i][j][m][n]
                        else:
                            rulesFormatted[f"{i}.{j}.{m}"] = rules[i][j][m]
                else:
                    rulesFormatted[f"{i}.{j}"] = rules[i][j]
        else:
            rulesFormatted[f"{i}"] = rules[i]

    return rulesFormatted


class Rule:
    def __init__(self, code: str = "") -> None:
        rules = loadRules()

        self.name = ""
        self.description = ""
        self.code = code

        if code in rules.keys():
            if isinstance(rules[code], list):
                self.name = rules[code][0]
                self.description = rules[code][1]
            else:
                self.description = rules[code]
        else:
            self.name = self.code
            self.description = "Rule not found or belonging to old rulebook"

    def isNone(self) -> bool:
        return self.code == ""
    
    def __str__(self) -> str:
        return self.name


class ReportData:  # TODO rule è una struttura
    def __init__(
        self,
        league: str,
        round: int,
        proof: str,
        desc: str,
        rule: Rule = Rule(),
        offender: discord.Member = None,
        creator: discord.Member = None,
        id: str = None,
        penalty: str = "",
        severity: str = "",
        notes: str = "",
        active: bool = False,
        timestamp: str = None,
    ) -> None:
        if id == None:
            self.id = self.getNewId()
        else:
            self.id = id
        self.offender = offender
        self.creator = creator
        self.league = league
        self.round = round
        self.rule = rule
        self.proof = proof
        self.desc = desc
        self.penalty = penalty
        self.severity = severity
        self.notes = notes
        self.active = active
        if timestamp == None:
            self.timestamp = datetime.datetime.utcnow()
        else:
            self.timestamp = datetime.datetime.strptime(timestamp, config.timeFormat)

    async def setUsers(
        self, bot, offenderId: int = None, creatorId: int = None
    ) -> None:
        if offenderId != None:
            try:
                self.offender = await bot.fetch_user(offenderId)
            except:
                logging.warning("user not found")

        if creatorId != None:
            try:
                self.creator = await bot.fetch_user(creatorId)
            except:
                logging.warning("user not found")

    def getNewId(self):
        id = utils.randomString(4)

        while isReportExist(id):
            id = utils.randomString(4)

        return id

    def isActive(self) -> bool:
        return self.active


def getRule(rule: str) -> str:
    rules = loadRules()

    if rule in rules.keys():
        return rules[rule]

    return None


def addToHistory(data: ReportData) -> None:
    history = utils.read(config.historyPath)
    if history == None:
        history = {}

    if str(data.offender.id) in history.keys():
        history[str(data.offender.id)]["name"] = data.offender.name
    else:
        history[str(data.offender.id)] = {"name": data.offender.name, "violations": {}}

    history[str(data.offender.id)]["violations"][data.id] = {
        "creator": data.creator.id,
        "league": data.league,
        "round": data.round,
        "description": data.desc,
        "rule": data.rule.code,
        "proof": data.proof,
        "penalty": data.penalty,
        "severity": data.severity,
        "notes": data.notes,
        "active": data.active,
        "timestamp": data.timestamp.strftime(config.timeFormat),
    }

    utils.write(config.historyPath, history)
    
    if not data.active:
        utils.updateSpreadSheet(data)


async def getReports(
    bot, id: int = None, user: discord.Member = None
) -> list[ReportData]:
    history = utils.read(config.historyPath)
    violations = []

    if id != None:
        for member in history.keys():
            for v in history[member]["violations"].keys():
                if v == str(id):
                    report = history[member]["violations"][v]
                    struct = ReportData(
                        id=str(id),
                        league=report["league"],
                        round=report["round"],
                        rule=Rule(report["rule"]),
                        desc=report["description"],
                        proof=report["proof"],
                        penalty=report["penalty"],
                        severity=report["severity"],
                        notes=report["notes"],
                        active=report["active"],
                        timestamp=report["timestamp"],
                    )
                    await struct.setUsers(
                        bot, offenderId=member, creatorId=report["creator"]
                    )

                    violations.append(struct)

    elif user != None and str(user.id) in history.keys():
        data = history[str(user.id)]["violations"]

        for v in data.keys():
            struct = ReportData(
                id=v,
                offender=user,
                league=data[v]["league"],
                round=data[v]["round"],
                rule=Rule(data[v]["rule"]),
                desc=data[v]["description"],
                proof=data[v]["proof"],
                penalty=data[v]["penalty"],
                severity=data[v]["severity"],
                notes=data[v]["notes"],
                active=data[v]["active"],
                timestamp=data[v]["timestamp"],
            )

            await struct.setUsers(
                bot, creatorId=data[v]["creator"]
            )  # TODO controlla se necessario

            if not struct.isActive():
                violations.append(struct)

    return violations


async def getActive(bot) -> list[ReportData]:
    history = utils.read(config.historyPath)
    violations = []

    for member in history.keys():
        for v in history[member]["violations"].keys():
            report = history[member]["violations"][v]
            if report["active"] == True:
                violations.append((await getReports(bot, id=v))[0])

    return violations


def isReportExist(id: int) -> bool:
    history = utils.read(config.historyPath)

    for member in history.keys():
        for v in history[member]["violations"].keys():
            if v == str(id):
                return True

    return False
