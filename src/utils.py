import datetime
import json
import random
import discord
import config
import openpyxl

from database.beans import League, Race
from database.databaseHandler import Database


def lev_dist(s: str, t: str) -> int:
    """
    Calculates the lev distance between two strings.

    Parameters
    -----------
    - s : `str`\n
        First string to confront.
    - t : `str`\n
        Second string to confront.

    Returns
    ----------
    A `int` value representing the lev distance between the two strings.
    """
    v0 = [i for i in range(len(t) + 1)]
    v1 = [0] * (len(t) + 1)

    for i in range(len(s)):
        v1[0] = i + 1
        for j in range(len(t)):
            deletionCost = v0[j + 1] + 1
            insertionCost = v1[j] + 1
            if s[i] == t[j]:
                substitutionCost = v0[j]
            else:
                substitutionCost = v0[j] + 1

            v1[j + 1] = min(deletionCost, insertionCost, substitutionCost)

        temp = v0
        v0 = v1
        v1 = temp
    return v0[-1]


def loading(i, len):
    j = 0
    str = "|"
    perc = round(i / len * 20, 1)
    while j < 20:
        if perc > j:
            str += "█"
        else:
            str += "   "
        j += 1
    str += f"| {round(i/len*100, 1)}%"
    return str


def createNumbersSheet(path: str, numbers: list[list]):
    workbook = openpyxl.load_workbook(filename=path)
    sheet = workbook.active

    ids = read("../data/numbersIds.json")

    data = [[0, 0, 0] for i in range(1000)]
    for i in range(1000):
        data[i][0] = str(i)
        if str(i) in numbers.keys():
            data[i][1] = numbers[str(i)]
            if str(i) in ids.keys():
                data[i][2] = ids[str(i)]
            else:
                data[i][2] = ""
        else:
            data[i][1] = "Available"

    for i in range(len(data)):
        for j in range(len(data[0])):
            sheet.cell(row=i + 1, column=j + 1).value = data[i][j]

    workbook.save(filename=path)


def write(path: str, data: dict) -> None:
    data = json.dumps(data, indent=2)
    with open(path, "w+") as f:
        f.write(data)


def read(path: str) -> dict:
    try:
        with open(path, "r") as f:
            file = f.read()
        return json.loads(file)
    except:
        return None


def randomString(len: int) -> str:
    alphabet = "0123456789"

    return random.choices(alphabet[1:])[0] + "".join(
        random.choices(alphabet, k=len - 1)
    )


def isLink(str: str) -> dict[bool, str]:
    """
    Checks if the string provided is a YouTube or Discord link.

    Parameters
    -----------
    - str : `str`\n
        The string to check.

    Returns
    ----------
    - `bool` value representing the outcome of the check.

    - `str` containing the reason why the check failed.
    """
    cond = len(str) > 5 and str.find(" ") == -1

    yt = cond and (
        str.startswith("https://youtube.com")
        or str.startswith("https://www.youtube.com")
        or str.startswith("youtube.com")
        or str.startswith("https://youtu.be")
        or str.startswith("https://www.youtu.be")
        or str.startswith("youtu.be")
    )

    discord = cond and (
        str.startswith("https://discord.com")
        or str.startswith("discord.com")
        or str.startswith("https://cdn.discordapp.com")
        or str.startswith("cdn.discordapp.com")
    )

    if yt:
        if linkHasTimestamp(str):
            return True, None
        else:
            return False, "The YouTube link provided doesn't have a timestamp"
    elif discord:
        return True, None

    return False, "The link provided ain't a YouTube or Discord link"


def linkHasTimestamp(str: str) -> bool:
    start = str.find("t=")

    if start == -1:
        return False

    return str[start + 2 :].isdigit() or str[len(str) - 1] == "s"


def hasPermissions(
    user: discord.Member, role: int = None, roles: list[int] = None
) -> bool:
    """
    Checks if the provided `Member` has a set of roles.

    Only one of the parameters `role` or `roles` should be given.

    Args:
        user (`discord.Member`): User to check if has permissions.
        role (`Optional[int]`): The role code that the user should have.
        roles (`Optional[list[int]]`):The roles codes that the user should have.

    Returns:
        `bool`: The outcome of the check.
    """
    if role != None:
        roles = [role]

    for i in roles:
        for j in user.roles:
            if j.id == i:
                return True

    return False


def formatBlockQuote(str: str) -> str:
    str = "> " + str

    for i in range(len(str)):
        if str[i] == "\n":
            str = str[: i + 1] + "> " + str[i + 1 :]

    return str


def load_reportWindowNotice() -> dict[str, datetime.datetime]:
    data = read(config.reportWindowNoticePath)

    if data == None:
        data = {}

    for league in data.keys():
        data[league] = datetime.datetime.strptime(data[league], config.timeFormat)

    for league in League:
        if not str(league) in data.keys() and league != League.OT:
            data[str(league)] = datetime.datetime.strptime(
                "2001-11-09 8:09", config.timeFormat
            )

    return data


def update_reportWindowNotice(data: dict):
    leagues = {}
    
    for league in data.keys():
        leagues[league] = datetime.datetime.strftime(data[league], config.timeFormat)

    write(config.reportWindowNoticePath, leagues)


def formatDateTime(str: str) -> datetime.datetime:
    return datetime.datetime.strptime(str, config.timeFormat)


def loadSchedule(dbHandler: Database):
    data = read(config.schedulePath)

    for league in data.keys():
        for i in range(len(data[league]["rounds"])):
            query = """
                INSERT INTO Races (league, season, round, date) 
                VALUES (%s, %s, %s, %s)
            """

            values = (league, data[league]["season"], i + 1, data[league]["rounds"][i])

            dbHandler.cursor.execute(query, values)
            dbHandler.database.commit()


def closeWindowDate(race: Race) -> datetime.datetime:
    closeDate = race.date + datetime.timedelta(days=config.reportWindowDelta)
    closeDate = closeDate.replace(hour=23, minute=59, second=0, microsecond=0)
    return closeDate

def listInsert(list: list, value, index:int) -> list:
    prev = value

    for i in range(index, len(list)):
        next = list[i]
        list[i] = prev
        prev = next

    list.append(prev)


def convertMentions(message: discord.Message) -> str:
    msg = message.content

    for user in message.mentions:
        msg = msg.replace(user.mention, f"@{user.name}({user.id})")

    return msg
