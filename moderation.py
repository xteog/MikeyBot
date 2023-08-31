import utils
import config
import discord

SWEAR_WORD_PATH = ""
HISTORY_PATH = ""


def setPaths(swearWordsPath: str, historyPath: str):
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


"""
@param msg
@param badWords
@return 
"""


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
                    if msg[i + j] == " ":
                        j += 1
                    else:
                        if msg[i + j] != word[k]:
                            flag = False
                        j += 1
                        k += 1

                if flag:
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


def getRule(rule: str) -> str:
    return "Keep it clean. No excessive swearing- We would like this chat to be positive and fairly family friendly."


def addToHistory(id=str, user=discord.Member, rule=str, proof=str, verdict=str) -> None:
    history = utils.read(HISTORY_PATH)

    if history == None:
        history = {}

    if user.id in history.keys:
        history[user.id]["name"] = user.name
    else:
        history[user.id] = {}

    if "history" in history[user.id].keys:
        history[user.id]["history"][id]({"rule": str, "proof": proof, "verdict": verdict})
    else:
        history[user.id]["history"] = {id: {"rule": str, "proof": proof, "verdict": verdict}}

    utils.write(HISTORY_PATH, history)
