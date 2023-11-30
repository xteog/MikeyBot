import logging
import utils
import config
import discord
import datetime


class WarningData:  # TODO rule è una struttura
    def __init__(
        self,
        rule: str,
        id: str = None,
        offender: discord.Member = None,
        creator: discord.Member = None,
        proof: str = "",
        verdict: str = "",
        timestamp: str = None,
    ) -> None:
        if id == None:
            self.id = utils.randomString(4)
        else:
            self.id = id
        self.offender = offender
        self.rule = rule
        self.creators = [creator]
        self.proof = proof
        self.verdict = verdict
        if timestamp == None:
            self.timestamp = datetime.datetime.utcnow()
        else:
            self.timestamp = datetime.datetime.strptime(timestamp, config.timeFormat)

    async def setUsers(
        self, bot, offenderId: int = None, creatorsId: list[int] = None
    ) -> None:
        if offenderId != None:
            try:
                self.offender = await bot.fetch_user(offenderId)  # TODO handle errors
            except:
                logging.error("user not found")

        if creatorsId != None:
            self.creators = []
            for id in creatorsId:
                self.creators.append(await bot.fetch_user(id))


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

        self.name = "None"
        self.description = "None"
        self.code = code

        if code in rules.keys():
            self.name = rules[code]["name"]
            self.description = rules[code]["description"]

    def isNone(self) -> bool:
        return self.code == ""


class ReportData:  # TODO rule è una struttura
    def __init__(
        self,
        league: str,
        round: int,
        proof: str,
        notes: str,
        rule: Rule = Rule(),
        offender: discord.Member = None,
        creator: discord.Member = None,
        id: str = None,
        verdict: str = "",
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
        self.notes = notes
        self.verdict = verdict
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
                logging.error("user not found")

        if creatorId != None:
            try:
                self.creator = await bot.fetch_user(creatorId)
            except:
                logging.error("user not found")

    async def getNewId():
        id = utils.randomString(4)

        while len(getReports(id)) > 0:
            id = utils.randomString(4)

        return id



def formatSwearWords(msg: str) -> str:  # TODO cut the message if too long
    badWordsSaid = findSwearWords(msg)

    if len(badWordsSaid) > 0:
        formattedMsg = f"{msg[0: badWordsSaid[0][0]]}||{msg[badWordsSaid[0][0]: badWordsSaid[0][1]]}||"
        for i in range(1, len(badWordsSaid)):
            formattedMsg += f"{msg[badWordsSaid[i - 1][1]: badWordsSaid[i][0] - 1]}||{msg[badWordsSaid[i][0]: badWordsSaid[i][0]]}||"

        formattedMsg += f"{msg[badWordsSaid[len(badWordsSaid) - 1][1]: len(msg)]}"
    else:
        formattedMsg = msg

    return formattedMsg


def findSwearWords(msg: str) -> list:
    badWords = utils.read(config.swearWordsPath)
    badWordsSaid = []
    msg = msg.lower()

    for word in badWords:
        word = word.lower()
        wordLen = len(word)
        msgLen = len(msg)
        i = 0
        while i < msgLen:
            j = 0
            k = 0
            flag = True
            if msg[i] != " ":
                while i + j < msgLen and k < wordLen:
                    if msg[i + j] != " " or wordLen <= 3:
                        if msg[i + j] != word[k]:
                            flag = False
                        k += 1
                    j += 1

                if flag and k == wordLen:
                    badWordsSaid.append((i, i + j))

            i += 1

    return badWordsSaid


def addSwearWord(swear_word: str) -> bool:
    badWords = utils.read(config.swearWordsPath)

    if not (swear_word in badWords):
        badWords.append(swear_word)
        utils.write(config.swearWordsPath, badWords)
        return True

    return False


def removeSwearWords(swear_frase: str) -> bool:
    badWords = utils.read(config.swearWordsPath)

    badWordsSaid = findSwearWords(swear_frase)

    for word in badWordsSaid:
        if swear_frase[word[0] : word[1]] in badWords:
            badWords.remove(swear_frase[word[0] : word[1]])
        else:
            print("word not present")

    utils.write(config.swearWordsPath, badWords)


def getRule(rule: str) -> str | None:
    rules = loadRules()

    if rule in rules.keys():
        return rules[rule]

    return None


"""
def addToHistory(data: WarningData) -> None:
    history = utils.read(config.historyPath)

    if history == None:
        history = {}

    if str(data.offender.id) in history.keys():
        history[str(data.offender.id)]["name"] = data.offender.name
    else:
        history[str(data.offender.id)] = {"name": data.offender.name, "violations": {}}

    creators = []
    for c in data.creators:
        creators.append(c.id)

    history[str(data.offender.id)]["violations"][data.id] = {
        "rule": data.rule,
        "creators": creators,
        "proof": data.proof,
        "verdict": data.verdict,
        "timestamp": data.timestamp.strftime(config.timeFormat),
    }

    utils.write(config.historyPath, history)
"""


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
        "rule": data.rule.code,
        "proof": data.proof,
        "notes": data.notes,
        "verdict": data.verdict,
        "timestamp": data.timestamp.strftime(config.timeFormat),
    }

    utils.write(config.historyPath, history)


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
                        notes=report["notes"],
                        proof=report["proof"],
                        verdict=report["verdict"],
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
                notes=data[v]["notes"],
                proof=data[v]["proof"],
                verdict=data[v]["verdict"],
                timestamp=data[v]["timestamp"],
            )

            await struct.setUsers(
                bot, creatorId=data[v]["creator"]
            )  # TODO controlla se necessario

            violations.append(struct)

    return violations
