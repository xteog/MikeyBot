import random
import utils
import config
import discord
import datetime
import pandas

SWEAR_WORD_PATH = ""
HISTORY_PATH = ""


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
            self.timestamp = datetime.datetime.strptime(
                timestamp, config.Config.timeFormat
            )

    async def setUsers(
        self, bot, offenderId: int = None, creatorsId: list[int] = None
    ) -> None:
        if offenderId != None:
            self.offender = await bot.fetch_user(offenderId)  # TODO gestisci errori

        if creatorsId != None:
            self.creators = []
            for id in creatorsId:
                self.creators.append(await bot.fetch_user(id))


def setPaths(swearWordsPath: str, historyPath: str):  # TODO aggiusta
    global SWEAR_WORD_PATH, HISTORY_PATH
    SWEAR_WORD_PATH = swearWordsPath
    HISTORY_PATH = historyPath


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
    badWords = utils.read(SWEAR_WORD_PATH)
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
                    if msg[i + j] != " ":
                        if msg[i + j] != word[k]:
                            flag = False
                        k += 1
                    j += 1

                if flag and k == wordLen:
                    badWordsSaid.append((i, i + j))

            i += 1

    return badWordsSaid


def addSwearWord(swear_word: str) -> bool:
    badWords = utils.read(SWEAR_WORD_PATH)

    if not (swear_word in badWords):
        badWords.append(swear_word)
        utils.write(SWEAR_WORD_PATH, badWords)
        return True

    return False


def removeSwearWords(swear_frase: str) -> bool:
    badWords = utils.read(SWEAR_WORD_PATH)

    badWordsSaid = findSwearWords(swear_frase)

    for word in badWordsSaid:
        if swear_frase[word[0] : word[1]] in badWords:
            badWords.remove(swear_frase[word[0] : word[1]])
        else:
            print("word not present")

    utils.write(SWEAR_WORD_PATH, badWords)


def loadRules() -> dict:
    rules = utils.read(config.Config.rulesPath)
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


def getRule(rule: str) -> str | None:
    rules = loadRules()

    if rule in rules.keys():
        return rules[rule]

    return None


def addToHistory(data: WarningData) -> None:
    history = utils.read(HISTORY_PATH)

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
        "timestamp": data.timestamp.strftime(config.Config.timeFormat),
    }

    utils.write(HISTORY_PATH, history)


async def getViolations(
    bot, id: int = None, user: discord.Member = None
) -> list[WarningData]:
    history = utils.read(HISTORY_PATH)
    violations = []

    if id != None:
        for member in history.keys():
            for v in history[member]["violations"].keys():
                if v == str(id):
                    report = history[member]["violations"][v]
                    struct = WarningData(
                        id=str(id),
                        rule=report["rule"],
                        proof=report["proof"],
                        verdict=report["verdict"],
                        timestamp=report["timestamp"],
                    )
                    await struct.setUsers(
                        bot, offenderId=member, creatorsId=report["creators"]
                    )

                    violations.append(struct)

    elif user != None and str(user.id) in history.keys():
        data = history[str(user.id)]["violations"]

        for v in data.keys():
            struct = WarningData(
                id=v,
                offender=user,
                rule=data[v]["rule"],
                proof=data[v]["proof"],
                verdict=data[v]["verdict"],
                timestamp=data[v]["timestamp"],
            )

            await struct.setUsers(bot, creatorsId=data[v]["creators"])

            violations.append(struct)

    if len(violations) == 0:
        return None

    return violations
