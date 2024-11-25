import discord
from discord.interactions import Interaction
from MikeyBotInterface import MikeyBotInterface
from database.beans import League, Report, Rule, VoteType
import utils
import config
import logging

""" Views """


class ReportView(discord.ui.View):
    def __init__(
        self,
        bot: MikeyBotInterface,
        data: Report,
    ):
        super().__init__(timeout=None)
        self.bot = bot
        self.data = data

        self.embed = ReportEmbed(bot=self.bot, data=self.data)

        self.add_item(LabelButton(view=self, type=VoteType.OFFENCE))
        self.add_item(VoteButton(view=self, type=VoteType.OFFENCE, in_favor=False))
        self.add_item(
            BarButton(
                view=self,
                type=VoteType.OFFENCE,
                nos=self.bot.getVotesCount(
                    report=data, type=VoteType.OFFENCE, in_favor=False
                ),
                yes=self.bot.getVotesCount(
                    report=data, type=VoteType.OFFENCE, in_favor=True
                ),
            )
        )
        self.add_item(VoteButton(view=self, type=VoteType.OFFENCE, in_favor=True))

        self.add_item(LabelButton(view=self, type=VoteType.AGGRAVATED))
        self.add_item(VoteButton(view=self, type=VoteType.AGGRAVATED, in_favor=False))
        self.add_item(
            BarButton(
                view=self,
                type=VoteType.AGGRAVATED,
                nos=self.bot.getVotesCount(
                    report=data, type=VoteType.AGGRAVATED, in_favor=False
                ),
                yes=self.bot.getVotesCount(
                    report=data, type=VoteType.AGGRAVATED, in_favor=True
                ),
            )
        )
        self.add_item(VoteButton(view=self, type=VoteType.AGGRAVATED, in_favor=True))

        self.add_item(CloseReportButton(self))


class CloseReportView(discord.ui.View):
    def __init__(
        self,
        bot: MikeyBotInterface,
        data: Report,
        report_interaction: discord.Interaction,
    ):
        super().__init__(timeout=None)
        self.bot = bot
        self.data = data
        self.report_interaction = report_interaction

        if self.data.race.league != League.OT:
            self.add_item(AttendanceSelect(view=self))

        self.add_item(ReportRuleSelect(self))

        self.add_item(AggravatedButton(self))

        self.add_item(NoOffenceButton(self))
        if not self.data.rule == None:
            self.add_item(OffenceButton(view=self, disabled=False))
        else:
            self.add_item(OffenceButton(view=self, disabled=True))


class SwitchView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Nintendo Switch Role",
        custom_id="switch",
        style=discord.ButtonStyle.danger,
    )
    async def switchRole(self, interaction: Interaction, button: discord.ui.Button):
        logging.info(f"{interaction.user.display_name} used the Switch button")
        guild = await self.bot.fetch_guild(config.serverId)
        role = guild.get_role(1202374974380179499)

        await interaction.user.add_roles(role)
        await interaction.response.send_message("Role added", ephemeral=True)


""" Embeds """


class ReportEmbed(discord.Embed):
    def __init__(
        self,
        bot: MikeyBotInterface,
        data: Report,
        permission: bool = True,
    ):
        super().__init__(title="Report")

        self.color = bot.getColor(report=data)

        if data.penalty != None:
            self.title = data.penalty

        self.description = f"**ID:** `{data.id}`\n"

        self.description += f"**User:** {bot.getNick(data.offender)} "

        if data.offender != None:
            self.description += f"({data.offender.mention})\n"

        if not data.active:
            if data.aggravated:
                self.description += f"**Aggravated:** ☑\n"
            else:
                self.description += f"**Aggravated:** ☐\n"

        self.description += f"**Round:** `{data.race}`\n"

        if data.rule != None:
            self.description += f"**Rule:** {data.rule.name}\n{utils.formatBlockQuote(data.rule.description)}\n"

        if permission:
            self.description += (
                f"**Description:**\n{utils.formatBlockQuote(data.description)}\n"
            )

        self.description += f"**Proof:** [Click here]({data.proof})\n"

        if data.notes != None and len(data.notes) > 0:
            self.description += f"**Notes:**\n{utils.formatBlockQuote(data.notes)}\n"

        try:
            self.set_thumbnail(url=data.offender.avatar.url)
        except:
            logging.warning("Thumbnail non caricata")

        self.timestamp = data.timestamp

        if permission:
            footer = f"Created by {bot.getNick(data.sender)}"

            try:
                self.set_footer(text=footer, icon_url=data.sender.avatar.url)
            except:
                self.set_footer(text=footer)


""" Modals """


class ReportModal(discord.ui.Modal, title="Report"):
    def __init__(self):
        super().__init__()
        self.notes = discord.ui.TextInput(
            label="Description",
            required=True,
            placeholder="Describe what happened",
            style=discord.TextStyle.paragraph,
        )
        self.link = discord.ui.TextInput(
            label="Proof link with timestamp",
            required=True,
            placeholder='ex. "https://youtu.be/dQw4w9&t=100"',
        )
        self.add_item(self.notes)
        self.add_item(self.link)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        self.interaction = interaction
        self.stop()


class ReminderModal(discord.ui.Modal, title="Reminder Details"):
    def __init__(self):
        super().__init__()
        self.notes = discord.ui.TextInput(
            label="Notes",
            required=False,
            placeholder="Enter additional details",
            style=discord.TextStyle.paragraph,
        )

        self.add_item(self.notes)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        self.interaction = interaction
        self.stop()


""" Buttons """


class ReportRuleSelect(discord.ui.Select):
    def __init__(self, view: CloseReportView) -> None:
        self.reportView = view

        super().__init__(
            placeholder="Select a Rule",
            max_values=1,
            options=self.getRuleSelectOptions(view.data.rule, view.data.race.league),
            row=1,
            custom_id=f"{view.data.id}_select_rule",
        )

    def getRuleSelectOptions(
        self, selected: Rule | None, league: League = ""
    ) -> list[discord.SelectOption]:
        options = []

        rules = self.reportView.bot.getRules()

        for rule in rules:
            if selected != None and rule.id == selected.id:
                options.append(
                    discord.SelectOption(
                        label=rule.name,
                        description=rule.code,
                        value=str(rule.id),
                        default=True,
                    )
                )
            else:
                options.append(
                    discord.SelectOption(
                        label=rule.name, description=rule.code, value=rule.id
                    )
                )

        return options

    async def callback(self, interaction: discord.Interaction) -> None:
        rule = self.reportView.bot.getRule(self.values[0])
        self.reportView.data.rule = rule
        newView = CloseReportView(
            self.reportView.bot,
            self.reportView.data,
            self.reportView.report_interaction,
        )

        await interaction.response.edit_message(view=newView)


class AttendanceSelect(discord.ui.Select):
    def __init__(self, view: CloseReportView) -> None:
        self.reportView = view

        options = self.getAttendanceOptions()
        super().__init__(
            placeholder="Check attendance",
            options=options,
            min_values=0,
            max_values=len(options),
            row=0,
            custom_id=f"{view.data.id}_select_attendance",
        )

    def getAttendanceOptions(self) -> list[discord.SelectOption]:
        options = []

        attendances = self.reportView.bot.getAttendances(
            user=self.reportView.data.offender, league=self.reportView.data.race.league
        )

        currRace = self.reportView.bot.getCurrentRace(
            league=self.reportView.data.race.league
        )

        i = len(attendances) - 1
        flag = False
        while i >= 0 and len(options) <= 10:

            if flag or attendances[i][0].id == currRace.id:
                options.append(
                    discord.SelectOption(
                        label=str(attendances[i][0]),
                        value=attendances[i][0].id,
                        default=attendances[i][1],
                    )
                )
                flag = True

            i -= 1

        options = options[::-1]
        
        return options

    async def callback(self, interaction: discord.Interaction) -> None:

        bot = self.reportView.bot

        for option in self.options:
            attended = False
            for id in self.values:
                if str(id) == str(option.value):
                    attended = True

            race = bot.getRace(id=option.value)

            bot.updateAttendance(user=interaction.user, race=race, attended=attended)

        newView = CloseReportView(
            bot=bot,
            data=self.reportView.data,
            report_interaction=self.reportView.report_interaction,
        )

        await interaction.response.edit_message(view=newView)


class NoOffenceButton(discord.ui.Button):
    def __init__(self, view: CloseReportView):
        super().__init__(
            style=discord.ButtonStyle.green,
            label="No offence",
            row=3,
            custom_id=f"{view.data.id}_no",
        )
        self.reportView = view

    async def callback(self, interaction: Interaction) -> None:
        logging.info(f'{interaction.user.name} used the "No offence" Button')

        modal = ReminderModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        self.reportView.data.notes = modal.notes.value

        report = await self.reportView.bot.closeReport(
            report=self.reportView.data, offence=False
        )

        newEmbed = ReportEmbed(self.reportView.bot, report, permission=True)

        await modal.interaction.delete_original_response()
        await self.reportView.report_interaction.followup.edit_message(
            message_id=self.reportView.report_interaction.message.id,
            embed=newEmbed,
            view=discord.ui.View(),
        )

        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            content=f"{report.penalty} `{self.reportView.data.id}` sent to {self.reportView.bot.getNick(self.reportView.data.offender)}",
            view=discord.ui.View(),
        )


class OffenceButton(discord.ui.Button):
    def __init__(self, view: CloseReportView, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.red,
            label="Remind",
            disabled=disabled,
            row=3,
            custom_id=f"{view.data.id}_yes",
        )
        self.reportView = view

        if self.reportView.data.rule != None:
            self.label = view.bot.getPenalty(report=view.data)

        if len(self.label) > 50:
            self.label = self.label[:50]

    async def callback(self, interaction: Interaction) -> None:
        logging.info(f'{interaction.user.name} used the "Remind" Button')
        modal = ReminderModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        self.reportView.data.notes = modal.notes.value
        self.reportView.data.rule = self.reportView.data.rule

        report = await self.reportView.bot.closeReport(
            report=self.reportView.data, offence=True
        )

        newEmbed = ReportEmbed(
            self.reportView.bot,
            self.reportView.data,
            permission=True,
        )

        await modal.interaction.delete_original_response()
        await self.reportView.report_interaction.followup.edit_message(
            self.reportView.report_interaction.message.id,
            embed=newEmbed,
            view=discord.ui.View(),
        )

        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            content=f"{report.penalty} `{self.reportView.data.id}` sent to {self.reportView.bot.getNick(self.reportView.data.offender)}",
            view=discord.ui.View(),
        )


class AggravatedButton(discord.ui.Button):
    def __init__(self, view: CloseReportView):
        super().__init__(
            style=discord.ButtonStyle.gray,
            label="☐ Aggravated",
            row=2,
            custom_id=f"{view.data.id}_3",
        )

        self.reportView = view

        if self.reportView.data.aggravated:
            self.label = "☑ Aggravated"
            self.style = discord.ButtonStyle.red

    async def callback(self, interaction: discord.Interaction) -> None:
        self.reportView.data.aggravated = not self.reportView.data.aggravated

        newView = CloseReportView(
            self.reportView.bot,
            self.reportView.data,
            self.reportView.report_interaction,
        )

        await interaction.response.edit_message(view=newView)


class LabelButton(discord.ui.Button):
    def __init__(self, view: ReportView, type: VoteType):
        super().__init__(
            style=discord.ButtonStyle.gray,
            disabled=True,
            row=type.value,
            custom_id=f"{view.data.id}_{type}",
        )

        if type == VoteType.AGGRAVATED:
            self.label = "Aggravated:_"
        else:
            self.label = "Offence:____"


class VoteButton(discord.ui.Button):
    def __init__(self, view: ReportView, type: VoteType, in_favor: bool):
        super().__init__(row=type.value, custom_id=f"{view.data.id}_{type}_{in_favor}")

        if in_favor:
            self.label = "Yes"
            self.style = discord.ButtonStyle.red
        else:
            self.label = "No"
            self.style = discord.ButtonStyle.blurple

        self.reportView = view
        self._type = type
        self.in_favor = in_favor

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.reportView.bot.addVote(
            user=interaction.user,
            report=self.reportView.data,
            type=self._type,
            in_favor=self.in_favor,
        )

        newView = ReportView(
            self.reportView.bot,
            self.reportView.data,
        )

        await interaction.response.edit_message(view=newView, embed=newView.embed)


class BarButton(discord.ui.Button):
    def __init__(self, view: ReportView, type: VoteType, nos: int, yes: int):
        super().__init__(
            style=discord.ButtonStyle.gray,
            row=type.value,
            custom_id=f"{view.data.id}_{type}_bar",
        )

        self.reportView = view
        self.label = self.buildVoteBar(yes=yes, nos=nos)
        self._type = type

    def buildVoteBar(
        self, nos: int, yes: int, n_voters: int = config.stewardsNumber
    ) -> str:
        max_value = n_voters // 2 + 1

        yes = min(yes, max_value)
        nos = min(nos, max_value)

        return (
            nos * "▰"
            + "▱" * (max_value - nos)
            + " ᜵ "
            + "▱" * (max_value - yes)
            + "▰" * yes
        )

    def formatVotesUsers(self, users: list[discord.Member], in_favour: bool) -> str:
        if in_favour:
            str = "Yes:\n"
        else:
            str = "No:\n"

        for user in users:
            str += f"   {self.reportView.bot.getNick(user)}\n"

        return str

    async def callback(self, interaction: discord.Interaction) -> None:
        content = ""

        content += self.formatVotesUsers(
            await self.reportView.bot.getVotesUsers(
                report=self.reportView.data, type=self._type, in_favor=True
            ),
            in_favour=True,
        )
        content += "\n"
        content += self.formatVotesUsers(
            await self.reportView.bot.getVotesUsers(
                report=self.reportView.data, type=self._type, in_favor=False
            ),
            in_favour=False,
        )

        await interaction.response.send_message(content=content, ephemeral=True)


class CloseReportButton(discord.ui.Button):
    def __init__(self, view: ReportView):
        super().__init__(
            style=discord.ButtonStyle.gray,
            label="Close Report",
            row=2,
            custom_id=f"{view.data.id}_close",
        )

        self.reportView = view

    async def callback(self, interaction: discord.Interaction) -> None:
        newView = CloseReportView(
            self.reportView.bot, self.reportView.data, interaction
        )

        await interaction.response.send_message(view=newView, ephemeral=True)
