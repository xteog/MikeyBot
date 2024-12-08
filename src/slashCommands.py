import discord
import logging
from MikeyBotInterface import MikeyBotInterface
import config
from database.beans import League, Race, getLeague
import views
import utils
from datetime import datetime
from datetime import timedelta
import os


def leagueList() -> list:
    return [
        discord.app_commands.Choice(name="Ultimate League", value="UL"),
        discord.app_commands.Choice(name="Challenger League", value="CL"),
        discord.app_commands.Choice(name="Journeyman League", value="JL"),
        discord.app_commands.Choice(name="Apprentice League", value="AL"),
        discord.app_commands.Choice(name="Off-Track", value="Off-Track"),
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


def isWindowOpen(race: Race) -> bool:
    if race.league != League.OT:
        return datetime.now() > race.date and datetime.now() < utils.closeWindowDate(
            race=race
        )

    return True


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

        if league.value == str(League.OT):
            race = Race(id=41, league=league.value, season=1, round=1, date=datetime.now())
        else:
            race = self.client.getCurrentRace(league=league)

        if (not isWindowOpen(race)) and (
            not utils.hasPermissions(
                interaction.user, roles=[config.stewardsRole, config.devRole]
            )
        ):
            closeDate = utils.closeWindowDate(race=race)

            await interaction.response.send_message(
                f"Report window closed <t:{int(closeDate.timestamp())}:R>",
                ephemeral=True,
            )
            return

        modal = views.ReportModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        cond, error = utils.isLink(modal.link.value)
        if not cond:
            await modal.interaction.delete_original_response()
            await interaction.followup.send(error, ephemeral=True)
            return
        
        data = await self.client.openReport(
            sender=interaction.user,
            offender=user,
            race=race,
            proof=modal.link.value,
            description=modal.notes.value,
        )

        await modal.interaction.delete_original_response()
        await interaction.followup.send(f"Report `{data.id}` created", ephemeral=True)

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

        if interaction.channel.id != 990229907479076914:
            channel = await self.client.fetch_channel(990229907479076914)
            await interaction.response.send_message(
                f"Use this command on {channel.mention}", ephemeral=True
            )
            return

        if not (number >= 0 and number <= 999):
            await interaction.response.send_message(f"Number not valid", ephemeral=True)
            return

        permission = utils.hasPermissions(
            interaction.user, roles=[config.devRole, config.URARole, config.devRole]
        )

        numbers = utils.read(config.numbersListPath)

        if (not permission) and (
            (user != None and user.id != interaction.user.id)
            or (str(number) in numbers.keys())
        ):
            await interaction.response.send_message(
                "You can't set someone else number", ephemeral=True
            )
            return

        delete = []
        if user != None:
            numbers[str(number)] = user.name

            desc = f"The number of {user.mention} is now changed into {number}"

            for key in numbers.keys():
                if numbers[key] == numbers[str(number)] and key != str(number):
                    delete.append(key)
        elif permission:
            numbers.pop(str(number), None)

            desc = f"The number {number} is now available"
        else:
            numbers[str(number)] = interaction.user.display_name

            desc = (
                f"The number of {interaction.user.mention} is now changed into {number}"
            )
            for key in numbers.keys():
                if numbers[key] == numbers[str(number)] and key != str(number):
                    delete.append(key)

        for key in delete:
            numbers.pop(key, None)

        utils.write(config.numbersListPath, numbers)

        matrix = [[0, 0] for i in range(1000)]
        for i in range(1000):
            matrix[i][0] = str(i)
            if str(i) in numbers.keys():
                matrix[i][1] = numbers[str(i)]
            else:
                matrix[i][1] = "Available"

        utils.createWorkbook(config.numbersSheetPath, matrix)
        await interaction.response.send_message(
            content=desc, file=discord.File(config.numbersSheetPath)
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
