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
        self.rules = moderation.loadRules()  # TODO togli
        """
        client.tree.add_command(
            discord.app_commands.ContextMenu(
                name="Report Message",
                callback=report,  # set the callback of the context menu to "my_cool_context_menu"
            )
        )
        """

    @discord.app_commands.command(
        name="issue_warning",
        description="Warns a user of a violation",
    )
    @discord.app_commands.describe(user="The user that you want to warn")
    @discord.app_commands.describe(rule="The rule violated (ex. G.1.4)")
    @discord.app_commands.autocomplete(rule=rules_autocomplete)
    async def issue_warning(
        self, interaction: discord.Interaction, user: discord.Member, rule: str
    ):
        logging.info(f'"\\issue_warning" used by {interaction.user.name}')
        modal = views.ViolationModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        data = moderation.WarningData(
            offender=user,
            rule=rule,
            creator=interaction.user,
            proof=modal.link.value,
            verdict=modal.notes.value,
        )

        await self.client.sendWarning(data)

        moderation.addToHistory(data)

        await modal.interaction.delete_original_response()
        await interaction.followup.send(f"Warning `{data.id}` sent", ephemeral=True)

    @discord.app_commands.command(
        name="add_swear_word",
        description="Adds a a word that it is considered to violate the rules",
    )
    @discord.app_commands.describe(swear_word="The word you want to add")
    async def add_swear_word(self, interaction: discord.Interaction, swear_word: str):
        logging.info(f'"\\add_swear_word" used by {interaction.user.name}')

        if moderation.addSwearWord(swear_word):
            await interaction.response.send_message(
                f'Swear word "{swear_word}" added', ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f'Swear word "{swear_word}" already present', ephemeral=True
            )

    @discord.app_commands.command(
        name="search_reports",
        description="Search a report from the penalty log by id or by user",
    )
    @discord.app_commands.describe(id="The report's ID composed by 4 digits")
    @discord.app_commands.describe(user="Returns a list of the user's reports")
    async def search_reports(
        self,
        interaction: discord.Interaction,
        id: int = None,
        user: discord.Member = None,
    ):
        logging.info(f'"\\search_violation" used by {interaction.user.name} (id = {id}, user = {user}')

        if not utils.check_permissions(interaction.user, config.fiaRole):
            if not interaction.user.id == user.id:
                await interaction.followup.send(
                    "The link provided is not a Youtube link", ephemeral=True
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
                await interaction.response.send_message(embed=embed)

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
    @discord.app_commands.describe(round="The driver you want to report")
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

        if not utils.isLink(modal.link.value):
            await modal.interaction.delete_original_response()
            await interaction.followup.send(
                "The link provided is not a Youtube link", ephemeral=True
            )
            return

        if not utils.linkHasTimestamp(modal.link.value):
            await modal.interaction.delete_original_response()
            await interaction.followup.send(
                f"The link provided doesn't have a timestamp", ephemeral=True
            )
            return

        data = moderation.ReportData(
            offender=user,
            league=league,
            round=round,
            creator=interaction.user,
            proof=modal.link.value,
            notes=modal.notes.value,
        )

        moderation.addToHistory(data)

        await self.client.sendReport(data)

        await modal.interaction.delete_original_response()
        await interaction.followup.send(f"Report `{data.id}` created", ephemeral=True)

    @discord.app_commands.command(
        name="help",
        description="Shows the documentation of the bot",
    )
    async def help(self, interaction: discord.Interaction):
        logging.info(f'"\\help" used by {interaction.user.name}')

        with open("README.md") as f:
            text = f.read()

        await interaction.response.send_message(text, ephemeral=True)

    @discord.app_commands.command(
        name="reset",
        description="Resets the bot. Use it if there is a bug or it stopped working. (todo)",
    )
    async def reset(self, interaction: discord.Interaction):
        logging.info(f'"\\reset" used by {interaction.user.name}')
        # TODO finisci
        await self.client.change_presence(status=discord.Status.offline)

        main.reconnect(self.client)

    @reset.error
    @report.error
    @search_reports.error
    async def error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("Error: " + str(error), ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("Error: " + str(error), ephemeral=True)


def setup(bot):
    global cog
    cog = CommandsCog(bot)
    return cog
