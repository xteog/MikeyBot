import datetime
from enum import Enum


class League(Enum):
    UL = "UL"
    CL = "CL"
    JL = "JL"
    AL = "AL"
    OT = "Off-Track"

    def __str__(self) -> str:
        return self.value


class Race:
    def __init__(self, league: str, season: int, round: int) -> None:
        self.league = self.getLeague(league)
        self.season = int(season)
        self.round = int(round)

        if self.season < 1:
            raise ValueError("Season not valid")
        
        if self.round < 1 or self.round > 10:
            raise ValueError("Round not valid")

    def getLeague(self, str: str) -> League:
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

    def __str__(self) -> str:
        if self.league == "UL" or self.league == "CL":
            return str(self.league) + str(self.season) + "R" +  str(self.round)

        if self.round <= 5:
            return str(self.league) + str(self.season) + "A" + "R" + str(self.round)

        return str(self.league) + str(self.season) + "B" + "R" + str(self.round) - 5


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
        league: str,
        season: int,
        round: int,
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
        self.race = Race(league=league, season=season, round=round)
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
