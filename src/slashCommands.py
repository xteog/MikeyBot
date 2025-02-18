import discord
import logging
from MikeyBotInterface import MikeyBotInterface
import commands
import config
from database.beans import League, Race, getLeague
import views
import utils
from datetime import datetime
import os


def leagueList() -> list:
    return [
        discord.app_commands.Choice(name="Ultimate League", value="UL"),
        discord.app_commands.Choice(name="Challenger League", value="CL"),
        discord.app_commands.Choice(name="Journeyman League", value="JL"),
        discord.app_commands.Choice(name="Apprentice League", value="AL"),
        discord.app_commands.Choice(name="Off-Track", value="OT"),
    ]


async def availableNumbers(interaction: discord.Interaction, current: str) -> list:
    choices = []

    if len(current) == 0:
        current = "1"

    if not (current.isdigit() and int(current) >= 1 and int(current) <= 999):
        return choices

    numbers = utils.read(config.numbersListPath)

    searched = int(current)

    start = max(0, searched - 7)
    end = min(999, searched + 7)

    for n in range(start, end):
        if str(n) in numbers.keys():
            choices.append(
                discord.app_commands.Choice(name=f"{n}: {numbers[str(n)]}", value=n)
            )
        else:
            choices.append(discord.app_commands.Choice(name=f"{n}: Available", value=n))

    return choices


class CommandsCog(discord.ext.commands.Cog):
    def __init__(self, client: MikeyBotInterface):
        self.client = client

    @discord.app_commands.command(
        name="report",
        description="Report a driver",
    )
    @discord.app_commands.describe(user="The driver you want to report")
    @discord.app_commands.describe(league="The league where the accident happened")
    @discord.app_commands.choices(league=leagueList())
    async def report(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        league: discord.app_commands.Choice[str],
    ):
        logging.info(f'"\\report" used by {interaction.user.name}')

        league = getLeague(league.value)

        modal = views.ReportModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        cond, error = utils.isLink(modal.link.value)
        if not cond:
            await modal.interaction.delete_original_response()
            await interaction.followup.send(error, ephemeral=True)
            return

        try:
            result = await commands.report(
                bot=self.client,
                sender=interaction.user,
                offender=user,
                league=league,
                proof=modal.link.value,
                description=modal.notes.value,
            )
        except Exception as e:
            await modal.interaction.delete_original_response()
            await interaction.followup.send(e)

        await modal.interaction.delete_original_response()
        await interaction.followup.send(result, ephemeral=True)

    @discord.app_commands.command(
        name="set_number",
        description="Choose the number you want to race with",
    )
    @discord.app_commands.describe(user="The driver to change race number")
    @discord.app_commands.describe(number="The number to set to")
    @discord.app_commands.autocomplete(number=availableNumbers)
    async def set_number(
        self, interaction: discord.Interaction, number: int, user: discord.Member = None
    ):
        logging.info(f'"\\set_number" used by {interaction.user.name}')

        channel = await self.client.fetch_channel(config.numbersChannelId)
        if interaction.channel != channel:
            await interaction.response.send_message(
                f"Use this command on {channel.mention}", ephemeral=True
            )
            return

        try:
            await commands.setNumber(
                channel=channel, author=interaction.user, user=user, number=number
            )
        except Exception as e:
            await interaction.response.send_message(e)

        await interaction.response.send_message("Number updated", ephemeral=True)

    @discord.app_commands.command(
        name="remind",
        description="Sends a reminder to the stewards",
    )
    async def remind(self, interaction: discord.Interaction):
        reports = await self.client.getActiveReports(user=interaction.user)

        view = views.ActiveReportsView(bot=self.client, reports=reports)

        await interaction.response.send_message(
            content="The result takes too much to arrive? Let me care of those mentally challenged stewards.\n Choose the reports you want to send the reminder of",
            view=view,
            ephemeral=True,
        )

    @discord.app_commands.command(
        name="restart",
        description="Restarts the bot",
    )
    async def restart(self, interaction: discord.Interaction):
        permission = utils.hasPermissions(
            interaction.user, roles=[config.devRole, config.URARole]
        )

        if not permission:
            await interaction.response.send_message(
                "You can't use this command", ephemeral=True
            )
            return

        await interaction.response.send_message("Mikey is restarting", ephemeral=True)

        os.system("sudo reboot")

    @report.error
    async def on_error(self, interaction: discord.Interaction, error):
        logging.error(error)
        await self.client.errorChannel.send("Error: " + str(error))

        try:
            await interaction.edit_original_response(
                "Error: " + str(error), ephemeral=True
            )
        except:
            await interaction.followup.send("Error: " + str(error), ephemeral=True)


def setup(bot):
    global cog
    cog = CommandsCog(bot)
    return cog
