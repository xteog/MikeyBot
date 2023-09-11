from typing import Optional
import discord
import utils
import config
import logging


class VerificationView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

        self.embed = discord.Embed(
            title="Verification",
            description="Hi fellow driver, wanna join the leagues? You first have to verify your steam account and your internet connection *other instructions*",
        )

    @discord.ui.button(
        label="Verify Connection",
        custom_id="VerificationViewButton1",
        style=discord.ButtonStyle.green,
    )
    async def verifyConnection(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        # TODO clear dms
        embed = discord.Embed(
            title="Verify",
            description="Send a screenshot of the results given by this site:\nThe pic should be like something like this:",
        )
        await self.bot.dmsChannel.send(content=f"dms of {interaction.user.name}", embed=embed)

        setVerificationStatus(userId=interaction.user.id, connection="on_going")

        await interaction.response.send_message("Verication sent, check your dms", ephemeral=True)

    @discord.ui.button(
        label="Verify Steam Account",
        custom_id="VerificationViewButton2",
        style=discord.ButtonStyle.green,
    )
    async def verifySteam(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        embed = discord.Embed(
            title="Verify",
            description="Send a screenshot of the results given by this site:\nThe pic should be like something like this:",
        )
        await self.bot.dmsChannel.send(content=f"dms of {interaction.user.name}", embed=embed)

        setVerificationStatus(userId=interaction.user.id, steamId="on_going")

        await interaction.response.send_message("Verication sent, check your dms", ephemeral=True)


class VerifyView(discord.ui.View):
    def __init__(self, bot, user: discord.Member, file = str, connection: bool = False, steamId: bool = False):
        super().__init__(timeout=config.defaultTimeout)
        self.bot = bot
        self.user = user

        self.embed = discord.Embed(
            title="Verification"
        )
        self.connection = connection
        self.steamId = steamId

        if connection:
            self.embed.description = f"Is {user.name}'s connection verified?"
        elif steamId:
            self.embed.description = f"Is {user.name}'s steamId verified?"
        else:
            logging.error("VerifyView parameters missing")

        self.embed.set_image(url=file)

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.green,
    )
    async def verify(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if self.connection:
            setVerificationStatus(userId=self.user.id, connection="done")
            self.embed.description = f"Is {self.user.name}'s connection verified?"
        elif self.steamId:
            setVerificationStatus(userId=self.user.id, steamId="done")
            self.embed.description = f"Is {self.user.name}'s steamId verified?"

        await self.user.add_roles(discord.utils.get(self.user.guild.roles, id=config.connectionRole))
        await self.user.send("You are now verified! something else like 'join our leagues'")

        await interaction.response.send_message("User Verified", ephemeral=True)

    async def on_timeout(self) -> None:
        print("todo") #TODO da fare


def setVerificationStatus(
    userId: int, connection: str = None, steamId: str = None
) -> None:
    history = utils.read(config.historyPath)
    userId = str(userId)

    if not (userId in history.keys()):
        history[userId] = {}
    
    if not ("connection" in history[userId].keys()):
        history[userId]["connection"] = "no"
    if not ("steamId" in history[userId].keys()):
        history[userId]["steamId"] = "no"

    if connection != None:
        if history[userId]["steamId"] == "on_going" and connection == "on_going":
            history[userId]["steamId"] = "no"
        history[userId]["connection"] = connection
    elif steamId != None:
        if history[userId]["connection"] == "on_going" and steamId == "on_going":
            history[userId]["connection"] = "no"
        history[userId]["steamId"] = steamId
    else:
        logging.error("setVerificationStatus() parameters missing")

    utils.write(config.historyPath, history)


def isVerifying(
    userId: int, checkConnection: bool = False, checkSteamId: bool = False
) -> bool:
    return getVerificationStatus(userId, checkConnection, checkSteamId) == "on_going"


def isVerified(
    userId: int, checkConnection: bool = False, checkSteamId: bool = False
) -> bool:
    return getVerificationStatus(userId, checkConnection, checkSteamId) == "done"


def getVerificationStatus(
    userId: int, checkConnection: bool = False, checkSteamId: bool = False
) -> str:
    history = utils.read(config.historyPath)
    userId = str(userId)

    if not (userId in history.keys()):
        history[userId] = {"connection": "no", "steamId": "no"}

    if not ("connection" in history[userId].keys()):
        history[userId]["connection"] = "no"
    if not ("steamId" in history[userId].keys()):
        history[userId]["steamId"] = "no"

    if checkConnection:
        return history[userId]["connection"]
    elif checkSteamId:
        return history[userId]["steamId"]
    else:
        logging.error("isVerifing() parameters missing")
