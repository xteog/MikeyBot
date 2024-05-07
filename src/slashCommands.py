import discord
import logging
import config
import moderation.violations as violation
import moderation.views as views
import utils
from datetime import datetime
from datetime import timedelta
import role_assign.views
import role_assign.objects


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
        discord.app_commands.Choice(name="Apprentice League", value="AL"),
        discord.app_commands.Choice(name="Formula E", value="FE"),
        discord.app_commands.Choice(name="Off-Track", value="Off-Track"),
    ]


async def availableNumbers(interaction: discord.Interaction, current: str) -> list:
    choices = []

    if len(current) == 0:
        current = "1"

    if not (current.isdigit() and int(current) >= 1 and int(current) <= 99):
        return choices

    numbers = utils.read(config.numbersListPath)

    searched = int(current)

    start = max(0, searched - 7)
    end = min(99, searched + 7)

    for n in range(start, end):
        if str(n) in numbers.keys():
            choices.append(
                discord.app_commands.Choice(name=f"{n}: {numbers[str(n)]}", value=n)
            )
        else:
            choices.append(discord.app_commands.Choice(name=f"{n}: Available", value=n))

    return choices


def isWindowOpen(league: str, round: int) -> bool:
    schedule = utils.load_schedule()

    if league in schedule.keys():
        return (
            datetime.now() > schedule[league]["rounds"][round - 1]
            and datetime.now()
            < schedule[league]["rounds"][round - 1] + config.reportWindowDelta[league]
        )

    return False


class CommandsCog(discord.ext.commands.Cog):
    def __init__(self, client):
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

        league = league.value
        round = self.client.getCurrentRound(league)

        if (
            (not isWindowOpen(league, round))
            and (not utils.hasPermissions(interaction.user, config.stewardsRole))
            and league != "Off-Track"
        ):
            try:
                open_date = self.client.schedule[league]["rounds"][round]
            except:
                open_date = datetime().now() + timedelta(days=100)

            await interaction.response.send_message(
                f"Report window will open <t:{int(open_date.timestamp())}:R>",
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

        data = violation.ReportData(
            offender=user,
            league=league
            + (
                ""
                if not league in self.client.schedule.keys()
                else self.client.schedule[league]["season"]
            ),
            round=round if round > 0 else None,
            creator=interaction.user,
            proof=modal.link.value,
            desc=modal.notes.value,
            active=True,
        )

        violation.addToHistory(data)

        await self.client.sendReport(data)

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

        if not (number >= 0 and number <= 99):
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

        matrix = [[0, 0] for i in range(100)]
        for i in range(100):
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
        name="role_assign",
        description="Create a View to self-assign roles",
    )
    @discord.app_commands.describe(
        message_id="If you want to edit an existing View insert here its message id"
    )
    async def role_assign(
        self, interaction: discord.Interaction, message_id: str = None
    ):
        logging.info(f'"\\role_assign" used by {interaction.user.name}')

        if not utils.hasPermissions(
            interaction.user, roles=[config.devRole, config.URARole]
        ):
            await interaction.response.send_message(
                "You dont't have the permissions", ephemeral=True
            )
            return

        if message_id == None:
            view = role_assign.views.RoleAssignEditView(
                self.client,
                role_assign.objects.RoleAssignData(
                    utils.randomString(8), interaction.channel_id, "No text"
                ),
            )
            await interaction.response.send_message(
                view=view, embed=view.embed, ephemeral=True
            )
        else:
            try:
                message_id = int(message_id)
            except Exception as e:
                await interaction.response.send_message(
                    "Message id not valid", ephemeral=True
                )
                return

            data = role_assign.objects.loadData(message_id)

            if data == None:
                await interaction.response.send_message(
                    "Message id not valid", ephemeral=True
                )
                return

            view = role_assign.views.RoleAssignEditView(self.client, data)
            await interaction.response.send_message(
                view=view, embed=view.embed, ephemeral=True
            )

    @discord.app_commands.command(
        name="help",
        description="Shows the documentation of the bot (todo)",
    )
    async def help(self, interaction: discord.Interaction):
        logging.info(f'"\\help" used by {interaction.user.name}')

        """
        with open("README.md") as f:
            text = f.read()
        """

        await interaction.response.send_message(
            "Not done yet. Dm me if you need help", ephemeral=True
        )

    @report.error
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
