from typing import Optional
import discord
import utils
import config
import logging


class VerificationView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(custom_id="VerificationView", timeout=None)
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
        #TODO clear dms
        embed = discord.Embed(title="Verify", description="Send a screenshot of the results given by this site:\nThe pic should be like something like this:")
        await self.bot.dmsChannel.send(embed=embed)

        setVerificationStatus(userId=interaction.user.id, connection="on_going")

    @discord.ui.button(
        label="Verify Steam Account",
        custom_id="VerificationViewButton2",
        style=discord.ButtonStyle.green,
    )
    async def verifySteam(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        embed = discord.Embed(title="Verify", description="Send a screenshot of the results given by this site:\nThe pic should be like something like this:")
        await self.bot.dmsChannel.send(embed=embed)

        setVerificationStatus(userId=interaction.user.id, steamId="on_going")



def setVerificationStatus(userId: int, connection: str = None, steamId: str = None):
    history = utils.read(config.historyPath)
    userId = str(userId)

    if userId in history.keys():
        history[userId] = {"connection": "no", "steamId": "no"}

    if connection != None:
        if history[userId]["steamId"] == "on_going" and connection == "on_going":
            history[userId]["steamId"] = "no"
        history[userId]["connection"] = connection
    elif steamId != None:
        if history[userId]["connection"] == "on_going" and steamId == "on_going":
            history[userId]["connection"] = "no"
        history[userId]["steamId"] = connection
    else:
        logging.error("setVerificationStatus() parameters missing")
