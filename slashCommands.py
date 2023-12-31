import discord
import logging
import main
import config
import moderation.moderation as moderation
import moderation.views as views
import utils
from datetime import datetime


async def rules_autocomplete(interaction: discord.Interaction, current: str) -> list:
    global cog

    codes = cog.rules.keys()
    list = []
    current = current.upper()

    for code in codes:
        if (
            len(code) >= len(current) and current == code[0 : len(current)]
        ) or current == code:
            name = f"{code}: {cog.rules[code]}"

            if len(name) >= 100:
                name = name[0:96] + "..."

            list.append(
                discord.app_commands.Choice(
                    name=name,
                    value=code,
                )
            )

    """
    if len(list) == 0:
        # TODO lev_dist
    """

    return list[0:25]


def leagueList() -> list:
    return [
        discord.app_commands.Choice(name="Ultimate League", value="UL"),
        discord.app_commands.Choice(name="Challenger League", value="CL"),
        discord.app_commands.Choice(name="Journeyman League", value="JL"),
        discord.app_commands.Choice(name="Formula E", value="FE"),
    ]


async def availableNumbers(interaction: discord.Interaction, current: str) -> list:
    choices = []

    if len(current) == 0:
        current = "1"
    
    if not (current.isdigit() and int(current) >= 1 and int(current) <= 99):
        return choices
    
    numbers = utils.read(config.numbersListPath)

    searched = int(current)

    start = max(1, searched - 7)
    end = min(99, searched + 7)

    for n in range(start, end):
        if str(n) in numbers.keys():
            choices.append(
                discord.app_commands.Choice(name=f"{n}: {numbers[str(n)]}", value=n)
            )
        else:
            choices.append(discord.app_commands.Choice(name=f"{n}: Available", value=n))
            
    return choices


def isWindowOpen(league: str) -> bool:
    return (
        datetime.now() > config.openTime[league]
        and datetime.now() < config.closeTime[league]
    )


class CommandsCog(discord.ext.commands.Cog):
    def __init__(self, client: main.MyBot):
        self.client = client

    @discord.app_commands.command(
        name="search_violation",
        description="Search a report from the penalty log by id or by user",
    )
    @discord.app_commands.describe(id="The report's ID composed by 4 digits")
    @discord.app_commands.describe(user="Returns a list of the user's reports")
    async def search_violation(
        self,
        interaction: discord.Interaction,
        id: int = None,
        user: discord.Member = None,
    ):
        logging.info(
            f'"\\search_violation" used by {interaction.user.name} (id = {id}, user = {user})'
        )

        permission = utils.hasPermissions(interaction.user, config.stewardsRole)

        if not permission:
            if user != None and interaction.user.id != user.id:
                await interaction.response.send_message(
                    "You can't search someone else reports", ephemeral=True
                )
                return

        if (id == None and user == None) or (id != None and user != None):
            await interaction.response.send_message(
                "You must fill only one of the parameters", ephemeral=True
            )
            return

        if id != None:
            violations = await moderation.getReports(bot=self.client, id=id)
            if len(violations) == 0:
                await interaction.response.send_message(
                    f"No reports found with ID `{id}`", ephemeral=True
                )
            else:
                embed = views.ReportEmbed(violations[0], permission=permission)
                await interaction.response.send_message(embed=embed, ephemeral=True)

        if user != None:
            await interaction.response.defer(ephemeral=True)
            violations = await moderation.getReports(bot=self.client, user=user)
            await interaction.delete_original_response()
            if len(violations) == 0:
                await interaction.followup.send(
                    f"The user {user.mention} doesn't have reports", ephemeral=True
                )
            else:
                view = views.ReportListView(
                    self.client, violations, permission=permission
                )
                await interaction.followup.send(
                    view=view, embed=view.embed, ephemeral=True
                )

    @discord.app_commands.command(
        name="report",
        description="Report a driver",
    )
    @discord.app_commands.describe(user="The driver you want to report")
    @discord.app_commands.describe(league="The league where the accident happened")
    @discord.app_commands.describe(round="The round where the accident happened")
    @discord.app_commands.choices(league=leagueList())
    async def report(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        league: discord.app_commands.Choice[str],
        round: int,
    ):
        logging.info(f'"\\report" used by {interaction.user.name}')
        league = league.value

        if not isWindowOpen(league):
            await interaction.response.send_message(
                f"Report window will open <t:{int(config.openTime[league].timestamp())}:R>",
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

        data = moderation.ReportData(
            offender=user,
            league=league,
            round=round,
            creator=interaction.user,
            proof=modal.link.value,
            desc=modal.notes.value,
            active=True,
        )

        moderation.addToHistory(data)

        await self.client.sendReport(data)

        await modal.interaction.delete_original_response()
        await interaction.followup.send(f"Report `{data.id}` created", ephemeral=True)

    @discord.app_commands.command(
        name="lobbies",
        description="Returns the list of lobbies currently active",
    )
    @discord.app_commands.describe(
        ephemeral='If "True" only you can see the list (default True)'
    )
    async def lobbies(self, interaction: discord.Interaction, ephemeral: bool = True):
        logging.info(f'"\\lobbies" used by {interaction.user.name}')

        lobbies = utils.getLobbiesList()

        if len(lobbies) == 0:
            await interaction.response.send_message("No lobbies found", ephemeral=True)
            return

        embed = discord.Embed(
            title="Lobbies online",
            colour=0x00B0F4,
        )

        for lobby in lobbies:
            if lobby["private"]:
                name = ":lock: " + f'**{lobby["name"]}**'
            else:
                name = f'**{lobby["name"]}**'

            if lobby["status"] == "Lobby":
                value = f'**Capacity:** {lobby["curr_players"]}/{lobby["max_players"]}\n**Status:** {lobby["status"]}'
            else:
                value = f'**Capacity:** {lobby["curr_players"]}/{lobby["max_players"]}\n**Status:** {lobby["status"]} {lobby["curr_laps"]}/{lobby["max_laps"]} Laps'

            embed.add_field(
                name=name,
                value=value,
                inline=True,
            )

        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @discord.app_commands.command(
        name="set_number",
        description="Choose the number you want to race with",
    )
    @discord.app_commands.describe(user="The driver to change race number")
    @discord.app_commands.describe(number="The number to set to")
    @discord.app_commands.autocomplete(number=availableNumbers)
    async def report(
        self, interaction: discord.Interaction, number: int, user: discord.Member = None
    ):
        logging.info(f'"\\set_number" used by {interaction.user.name}')

        if interaction.channel.id != 1059998599733321818:
            channel = await self.client.fetch_channel(1059998599733321818)
            await interaction.response.send_message(
                f"Use this command on {channel.mention}", ephemeral=True
            )
            return

        permission = utils.hasPermissions(interaction.user, roles=[config.devRole, config.URARole, config.devRole])
        numbers = utils.read(config.numbersListPath)

        if (not permission) and ((user != None and user.id != interaction.user.id) or (str(number) in numbers.keys())):
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
            numbers[str(number)] = interaction.user.name

            desc = f"The number of {interaction.user.mention} is now changed into {number}"
            for key in numbers.keys():
                if numbers[key] == numbers[str(number)] and key != str(number):
                    delete.append(key)
        
        for key in delete:
            numbers.pop(key, None)

        utils.write(config.numbersListPath, numbers)

        matrix = [[0, 0] for i in range(100)]
        for i in range(100):
            matrix[i][0] = str(i)
            if str(i) in numbers.keys():
                matrix[i][1] = numbers[str(i)]
            else:
                matrix[i][1] = "Available"

        utils.createWorkbook("data/numbers.xlsx", matrix)
        await interaction.response.send_message(content=desc, file=discord.File("data/numbers.xlsx"))

    @discord.app_commands.command(
        name="help",
        description="Shows the documentation of the bot (todo)",
    )
    async def help(self, interaction: discord.Interaction):
        logging.info(f'"\\help" used by {interaction.user.name}')

        with open("README.md") as f:
            text = f.read()

        await interaction.response.send_message("Not done yet", ephemeral=True)

    @discord.app_commands.command(
        name="reset",
        description="Resets the bot. Use it if there is a bug or it stopped working. (todo)",
    )
    async def reset(self, interaction: discord.Interaction):
        logging.info(f'"\\reset" used by {interaction.user.name}')
        # TODO finisci
        await self.client.change_presence(status=discord.Status.offline)

        # main.reconnect(self.client)
        await interaction.response.send_message("Not done yet", ephemeral=True)

    @reset.error
    @report.error
    @search_violation.error
    async def error(self, interaction: discord.Interaction, error):
        try:
            await interaction.followup.send("Error: " + str(error), ephemeral=True)
        except:
            await interaction.response.send_message(
                "Error: " + str(error), ephemeral=True
            )
        await self.client.errorChannel.send("Error: " + str(error))

    async def on_error(self, interaction: discord.Interaction, error):
        try:
            await interaction.followup.send("Error: " + str(error), ephemeral=True)
        except:
            await interaction.response.send_message(
                "Error: " + str(error), ephemeral=True
            )
        await self.client.errorChannel.send("Error: " + str(error))


def setup(bot):
    global cog
    cog = CommandsCog(bot)
    return cog
