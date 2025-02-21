from datetime import datetime, timedelta, timezone
import logging
import discord

from MikeyBotInterface import MikeyBotInterface
import config
from database.beans import League, Race, getLeague
from exceptions import ResponseException
import utils


async def executeCommand(bot: MikeyBotInterface, command: dict) -> str:
    if not "command" in command.keys():
        raise ResponseException('Key "command" missing')

    if command["command"] == "get_command_info":
        name = retrieveParameters(command=command, keys=["command"])[0]
        result = getCommandInfo(name)
    elif command["command"] == "set_number":
        authorId, userId, number = retrieveParameters(
            command=command, keys=["author", "user", "number"]
        )

        try:
            author = await bot.getUser(authorId)
        except:
            raise ResponseException(f'"author" not found from the id "{authorId}"')

        try:
            user = await bot.getUser(userId)
        except:
            raise ResponseException(f'"user" not found from the id "{userId}"')

        try:
            number = int(number)
        except:
            raise ResponseException('Parameter "number" must be an integer')

        result = await setNumber(
            channel=await bot.fetch_channel(config.numbersChannelId),
            author=author,
            user=user,
            number=number,
        )
    elif command["command"] == "report":
        senderId, offenderId, league, description, proof = retrieveParameters(
            command=command,
            keys=["sender", "offender", "league", "description", "proof"],
        )

        try:
            sender = await bot.getUser(senderId)
        except Exception as e:
            logging.error(e)
            raise ResponseException(f'"sender" not found from the id "{senderId}"')

        try:
            offender = await bot.getUser(offenderId)
        except Exception as e:
            logging.error(e)
            raise ResponseException(f'"offender" not found from the id "{offenderId}"')

        try:
            league = getLeague(league)
        except:
            raise ResponseException(
                f'League "{league}" not found. It must be "UL", "CL", "JL" or "AL".'
            )

        cond, error = utils.isLink(proof)
        if not cond:
            raise ResponseException(error)

        result = await report(
            bot=bot,
            offender=offender,
            sender=sender,
            league=league,
            proof=proof,
            description=description,
        )
    elif command["command"] == "mute":
        authorId, offenderId = retrieveParameters(
            command=command,
            keys=["author", "offender"],
        )

        try:
            author = await bot.getUser(authorId)
        except Exception as e:
            logging.error(e)
            raise ResponseException(f'"sender" not found from the id "{senderId}"')

        try:
            offender = await bot.getUser(offenderId)
        except Exception as e:
            logging.error(e)
            raise ResponseException(f'"offender" not found from the id "{offenderId}"')

        result = await mute(author=author, offender=offender)

    else:
        raise ResponseException(f'Command {command["command"]} not found')

    return result


def retrieveParameters(command: dict, keys: list[str]) -> tuple[str]:
    if "params" in command.keys():
        data = command["params"]
    else:
        raise ResponseException('Key "params" missing')

    params = []
    for param in keys:
        if param in data.keys():
            params.append(data[param])
        else:
            raise ResponseException(f'Parameter "{param}" missing')

    return tuple(params)


def getCommandInfo(name: str) -> str:
    try:
        with open(f"{name}.txt", "r") as file:
            doc = file.read()
    except:
        raise ResponseException('Command "{name}" not found')

    return f'Here it is the command "{name}" definition\n{doc}'


async def setNumber(
    channel: discord.TextChannel,
    author: discord.Member,
    user: discord.Member,
    number: int,
) -> str:
    if not (number >= 0 and number <= 999):
        raise Exception("Number not valid. It has to be between 0 and 999")

    permission = utils.hasPermissions(
        author, roles=[config.devRole, config.URARole, config.devRole]
    )

    numbers = utils.read(config.numbersListPath)
    ids = utils.read("../data/numbersIds.json")

    if (not permission) and (user != author or (str(number) in numbers.keys())):
        raise Exception("You can't set someone else number")

    delete = []
    if user != None:
        numbers[str(number)] = user.name
        ids[str(number)] = user.id

        desc = f"The number of {user.mention} is now changed into {number}"

        for key in numbers.keys():
            if numbers[key] == numbers[str(number)] and key != str(number):
                delete.append(key)
    elif permission:
        numbers.pop(str(number), None)

        desc = f"The number {number} is now available"
    else:
        numbers[str(number)] = user.display_name
        ids[str(number)] = user.id

        desc = f"The number of {user.mention} is now changed into {number}"
        for key in numbers.keys():
            if numbers[key] == numbers[str(number)] and key != str(number):
                delete.append(key)

    for key in delete:
        numbers.pop(key, None)

    utils.write(config.numbersListPath, numbers)
    utils.write("../data/numbersIds.json", ids)

    utils.createNumbersSheet(config.numbersSheetPath, numbers)

    await channel.send(content=desc, file=discord.File(config.numbersSheetPath))

    return desc


async def report(
    bot: MikeyBotInterface,
    sender: discord.Member,
    offender: discord.Member,
    league: League,
    description: str,
    proof: str,
) -> str:
    if league.value == str(League.OT):
        race = Race(
            id=41,
            league=league.value,
            season=1,
            round=1,
            date=datetime.now(timezone.utc),
        )
    else:
        race = bot.getCurrentRace(league=league)

    if (not isWindowOpen(race)) and (
        not utils.hasPermissions(sender, roles=[config.stewardsRole, config.devRole])
    ):
        closeDate = utils.closeWindowDate(race=race)
        return f"Report not created. Report window closed <t:{int(closeDate.timestamp())}:R>"

    data = await bot.openReport(
        sender=sender,
        offender=offender,
        race=race,
        proof=proof,
        description=description,
    )

    return f"Report `{data.id}` created.\n Tired of waiting for a result? Use the comand </remind:1338975422456791152>"


def isWindowOpen(race: Race) -> bool:
    if race.league != League.OT:
        return datetime.now() > race.date and datetime.now() < utils.closeWindowDate(
            race=race
        )

    return True


async def mute(author: discord.Member, offender: discord.Member):
    if (
        not utils.hasPermissions(
            author, [config.devRole, config.stewardsRole, config.URARole]
        )
        and author.id != config.botId
    ):
        return f"User {author}({author.id}) doesn't have permissions to mute."

    await offender.timeout(datetime.now(timezone.utc) + timedelta(minutes=10))
    return f"User {offender}({offender.id}) has been muted for 10minutes."
