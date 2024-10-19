from database.beans import League, Race, Report, Rule, VoteType
import discord
from discord.ext import commands

# import load_log


class MikeyBotInterface(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def getNick(self, member: discord.Member) -> str:
        pass

    async def openReport(
        self,
        sender: discord.Member,
        offender: discord.Member,
        race: Race,
        description: str,
        proof: str,
    ) -> Report:
        pass

    def getPenalty(self, report: Report) -> str:
        pass

    async def closeReport(self, report: Report, offence: bool) -> Report:
        pass

    async def sendMessage(self, msg: str, channelId: int) -> None:
        channel = self.get_channel(channelId)
        await channel.send(msg)

    async def archiveThread(self, id: str) -> None:
        pass

    def getCurrentRace(self, league: str) -> Race:
        pass

    async def getUser(self, id: int) -> discord.Member | None:
        pass

    def getColor(self, report: Report) -> int:
        pass

    def getOffenceLevel(self, report: Report) -> int:
        pass

    def getRules(self) -> tuple[Rule]:
        pass

    def getRule(self, id: int) -> Rule:
        pass

    def getVotesCount(self, report: Report, type: VoteType, in_favor: bool) -> int:
        pass

    async def getVotesUsers(
        self, report: Report, type: VoteType, in_favor: bool
    ) -> tuple[discord.Member]:
        pass

    async def addVote(
        self, user: discord.Member, report: Report, type: VoteType, in_favor: bool
    ) -> None:
        pass
