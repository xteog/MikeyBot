import datetime
from discord.ext import commands


class Rule:
    def __init__(
        self,
        id: int,
        name: str,
        code: str,
        description: str,
        escalation: int,
        de_escalation: int,
        levels: list,
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
        self.league = league
        self.season = season
        self.round = round
        self.rule = rule
        self.proof = proof
        self.description = description
        self.penalty = penalty
        self.aggravated = aggravated
        self.notes = notes
        self.active = active
        self.timestamp = timestamp

    async def init(self, bot: commands.Bot, offenderId: int, senderId: int) -> None:
        self.sender = await bot.getUser(senderId)
        self.offender = await bot.getUser(offenderId)
