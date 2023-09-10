import discord
import logging
import main
import config
import moderation.moderation as moderation
import moderation.views as views


def check_permissions(interaction: discord.Interaction):
    for role in interaction.user.roles:
        if role.id == config.fiaRole or role.id == config.devRole:
            return True
    return False


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


async def report(interaction: discord.Interaction, message: discord.Message):
    logging.info(f'"\\report" used by {interaction.user.name}')

    await interaction.response.send_message("reportato")


class CommandsCog(discord.ext.commands.Cog):
    def __init__(self, client: main.MyBot):
        self.client = client
        self.rules = moderation.loadRules()  # TODO togli
        client.tree.add_command(
            discord.app_commands.ContextMenu(
                name="Report Message",
                callback=report,  # set the callback of the context menu to "my_cool_context_menu"
            )
        )

    @discord.app_commands.command(
        name="issue_warning",
        description="Warns a user of a violation",
    )
    @discord.app_commands.describe(user="The user that you want to warn")
    @discord.app_commands.describe(rule="The rule violated (ex. G.1.4)")
    @discord.app_commands.check(check_permissions)
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
    @discord.app_commands.check(check_permissions)
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
        name="history",
        description="Search a violation in the history by id or user",
    )
    @discord.app_commands.describe(warning_id="The violation's ID composed by 4 digits")
    @discord.app_commands.describe(user="Returns a list of the user's violations")
    @discord.app_commands.check(check_permissions)
    async def history(
        self,
        interaction: discord.Interaction,
        warning_id: int = None,
        user: discord.Member = None,
    ):
        logging.info(f'"\\history" used by {interaction.user.name}')

        if (warning_id == None and user == None) or (warning_id != None and user != None):
            await interaction.response.send_message(
                "You must fill one of the parameters", ephemeral=True
            )
            return

        if warning_id != None:
            violations = await moderation.getViolations(bot=self.client, id=warning_id)
            if violations == None:
                await interaction.response.send_message(
                    f"No violations found with ID `{warning_id}`", ephemeral=True
                )
            else:
                embed = views.ViolationReportEmbed(violations[0])
                await interaction.response.send_message(embed=embed)

        if user != None:
            await interaction.response.defer(ephemeral=True)
            violations = await moderation.getViolations(bot=self.client, user=user)
            await interaction.delete_original_response()
            if violations == None:
                await interaction.followup.send(
                    f"The user {user.mention} doesn't have violations", ephemeral=True
                )
            else:
                embed = views.ViolationListEmbed(violations)
                await interaction.followup.send(embed=embed)

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
    @discord.app_commands.check(check_permissions)
    async def reset(self, interaction: discord.Interaction):
        logging.info(f'"\\reset" used by {interaction.user.name}')
        # TODO finisci
        await self.client.change_presence(status=discord.Status.offline)

        main.reconnect(self.client)

    @reset.error
    @add_swear_word.error
    @issue_warning.error
    async def error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("Error: " + error, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("Error: " + error, ephemeral=True)


def setup(bot):
    global cog
    cog = CommandsCog(bot)
    return cog
