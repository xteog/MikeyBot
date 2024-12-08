import datetime
from enum import Enum


class League(Enum):
    UL = "UL"
    CL = "CL"
    JL = "JL"
    AL = "AL"
    OT = "OT"

    def __str__(self) -> str:
        return self.value


def getLeague(str: str) -> League:
    if str == League.UL.value:
        return League.UL
    elif str == League.CL.value:
        return League.CL
    elif str == League.JL.value:
        return League.JL
    elif str == League.AL.value:
        return League.AL
    elif str == League.OT.value:
        return League.OT

    raise ValueError("League not valid")


class Race:
    def __init__(self, id: int, league: str, season: int, round: int, date: datetime.datetime) -> None:
        self.id = id
        self.league = getLeague(league)
        self.season = season
        self.round = int(round)
        self.date = date

        if self.round < 1 or self.round > 10:
            raise ValueError("Round not valid")

    def __str__(self) -> str:
        return str(self.league) + str(self.season) + "R" + str(self.round)


class Rule:
    def __init__(
        self,
        id: int,
        name: str,
        code: str,
        description: str,
        escalation: int,
        de_escalation: int,
        levels: tuple[str],
    ) -> None:
        self.id = id
        self.name = name
        self.code = code
        self.description = description
        self.escalation = escalation
        self.de_escalation = de_escalation
        self.levels = levels

    def __str__(self) -> str:
        return self.name


class Report:
    def __init__(
        self,
        id: str,
        senderId: int,
        offenderId: int,
        race: Race,
        description: str,
        proof: str,
        timestamp: datetime.datetime,
        rule: Rule | None = None,
        penalty: str | None = None,
        aggravated: bool = False,
        notes: str | None = None,
        active: bool = True,
    ) -> None:
        self.sender = None
        self.offender = None
        self.id = id
        self.senderId = senderId
        self.offenderId = offenderId
        self.race = race
        self.rule = rule
        self.proof = proof
        self.description = description
        self.penalty = penalty
        self.aggravated = aggravated
        self.notes = notes
        self.active = active
        self.timestamp = timestamp

    async def init(self, bot) -> None:
        self.sender = await bot.getUser(self.senderId)
        self.offender = await bot.getUser(self.offenderId)


class VoteType(Enum):
    OFFENCE = 0
    AGGRAVATED = 1
