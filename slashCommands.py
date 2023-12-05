import discord
import logging
import main
import config
import moderation.moderation as moderation
import moderation.views as views
import utils


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


async def league_autocomplete(interaction: discord.Interaction, current: str) -> list:
    return [
        discord.app_commands.Choice(name="Ultimate League", value="UL"),
        discord.app_commands.Choice(name="Challenger League", value="CL"),
        discord.app_commands.Choice(name="Journeyman League", value="JL"),
    ]


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

        if not utils.hasPermissions(interaction.user, config.stewardsRole):
            if user != None and interaction.user.id != user.id:
                await interaction.followup.send(
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
                embed = views.ReportEmbed(violations[0])
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
                view = views.ReportListView(self.client, violations)
                await interaction.followup.send(
                    view=view, embed=view.embed, ephemeral=True
                )

    @discord.app_commands.command(
        name="report",
        description="Report a driver",
    )
    @discord.app_commands.describe(user="The driver you want to report")
    @discord.app_commands.describe(league="The league where the accident happened")
    @discord.app_commands.describe(round="The league where the accident happened")
    @discord.app_commands.autocomplete(league=league_autocomplete)
    async def report(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        league: str,
        round: int,
    ):
        logging.info(f'"\\report" used by {interaction.user.name}')

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
    async def lobbies(self, interaction: discord.Interaction):
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

        await interaction.response.send_message(embed=embed)

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
        await interaction.followup.send("Error: " + str(error), ephemeral=True)
        await self.client.errorChannel.send("Error: " + str(error))

    async def on_error(self, interaction: discord.Interaction, error):
        await interaction.followup.send("Error: " + str(error), ephemeral=True)
        await self.client.errorChannel.send("Error: " + str(error))


def setup(bot):
    global cog
    cog = CommandsCog(bot)
    return cog
