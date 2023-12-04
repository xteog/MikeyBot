import discord
from discord.interactions import Interaction
import moderation.moderation as moderation
import utils
import config
import logging


""" Views """


class ReportView(discord.ui.View):
    def __init__(
        self,
        bot,
        data: moderation.ReportData,
        rule_selected: moderation.Rule = moderation.Rule(),
    ):
        super().__init__(timeout=None)
        self.bot = bot
        self.data = data
        self.rule_selected = rule_selected

        self.embed = ReportEmbed(self.data)

        self.add_item(ReportRuleSelect(self))
        self.add_item(NoOffenceButton(self))
        if not self.rule_selected.isNone():
            self.add_item(RemindButton(self, False))
        else:
            self.add_item(RemindButton(self, True))

    async def on_timeout(self) -> None:
        self.clear_items()
        self.data.notes = "No offence (timeout)"
        self.data.active = False
        moderation.addToHistory(self.data)


class ReportListView(discord.ui.View):
    def __init__(
        self,
        bot,
        data: [moderation.ReportData],
        disabled=False,
    ):
        super().__init__()
        self.bot = bot
        self.timeout = config.defaultTimeout
        self.data = data

        self.embed = ReportListEmbed(self.data)

    @discord.ui.button(
        label="Detailed View",
        style=discord.ButtonStyle.gray,
    )
    async def detailed_view(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        view = ReportListDetailedView(self.bot, self.data)
        await interaction.response.send_message(
            view=view, embed=view.embed, ephemeral=True
        )


class ReportListDetailedView(discord.ui.View):
    def __init__(
        self,
        bot,
        data: [moderation.ReportData],
        index: int = 0,
        disabled=False,
    ):
        super().__init__()
        self.bot = bot
        self.timeout = config.defaultTimeout
        self.data = data
        self.index = index
        self.embed = ReportEmbed(self.data[self.index])
        if self.index <= 0:
            self.add_item(LeftButton(self.bot, self.data, self.index, True))
        else:
            self.add_item(LeftButton(self.bot, self.data, self.index, False))
        self.add_item(
            discord.ui.Button(
                label=f"{self.index + 1}/{len(self.data)}",
                style=discord.ButtonStyle.gray,
                disabled=True,
            )
        )
        if self.index >= len(self.data) - 1:
            self.add_item(RightButton(self.bot, self.data, self.index, True))
        else:
            self.add_item(RightButton(self.bot, self.data, self.index, False))


""" Embeds """


class ReportEmbed(discord.Embed):
    def __init__(self, data: moderation.ReportData, title: str = "Report"):
        super().__init__(color=0xFFFFFF)
        if data.penalty == "":
            self.title = title
        else:
            self.title = data.penalty

        self.description = f"**ID:** `{data.id}`\n"

        self.description += (
            f"**User:** {data.offender.name} ({data.offender.mention})\n"
        )

        if len(data.severity) > 0:
            self.description += f"**Severity:** {data.severity}\n"

        self.description += f"**Round:** `{data.league} R{data.round}`\n"

        if not data.rule.isNone():
            self.description += (
                f"**Rule:** {data.rule.name}\n> {data.rule.description}\n"
            )

        if len(data.desc) > 0:
            self.description += f"**Description:**\n> {data.desc}\n"

        isLink, error = utils.isLink(data.proof)
        if isLink:
            self.description += f"**Proof:** [link to proof]({data.proof})\n"
        else:
            self.description += f"**Proof:** {data.proof}"

        if len(data.notes) > 0:
            self.description += f"**Notes:**\n> {data.notes}\n"

        try:
            self.set_thumbnail(url=data.offender.avatar.url)
        except:
            logging.error("Thumbnail non caricata")

        self.timestamp = data.timestamp

        footer = f"Created by {data.creator.name}"

        try:
            self.set_footer(text=footer, icon_url=data.creator.avatar.url)
        except:
            self.set_footer(text=footer)
            logging.error("Thumbnail non caricata")


class ReminderEmbed(discord.Embed):
    def __init__(self, data: moderation.ReportData, title: str = "Reminder"):
        super().__init__(title=data.penalty, color=0xFF0000)
        self.description = f"**ID:** `{data.id}`\n"

        self.description += (
            f"**User:** {data.offender.name} ({data.offender.mention})\n"
        )
        self.description += f"**Round:** `{data.league} R{data.round}`\n"

        self.description += f"**Rule:** {data.rule.name}\n> {data.rule.description}\n"

        isLink, error = utils.isLink(data.proof)
        if isLink:
            self.description += f"**Proof:** [Link to proof]({data.proof})\n"
        else:
            self.description += f"**Proof:** {data.proof}\n"

        if data.notes != "":
            self.description += f"**Notes:**\n> {data.notes}\n"

        try:
            self.set_thumbnail(url=data.offender.avatar.url)
        except:
            logging.error("Thumbnail non caricata")

        self.timestamp = data.timestamp


class ReportListEmbed(discord.Embed):
    def __init__(self, data: list[moderation.ReportData]):
        super().__init__(title=f"Report History", color=0xFFFFFF)
        self.description = f"**Name**:{data[0].offender.mention}\n```"

        for report in data:
            self.description += f"{report.id}|{report.timestamp.date()}|{report.penalty} {report.rule.name}\n"

        self.description += "```\n"
        self.set_thumbnail(url=data[0].offender.avatar.url)


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
    def __init__(self, choose_rule=False):
        super().__init__()
        self.rule = discord.ui.TextInput(
            label="Custom Rule",
            required=True,
            placeholder="ex. Leaving Open Lanes",
            style=discord.TextStyle.short,
        )
        self.penalty = discord.ui.TextInput(
            label="Penalty (temp)",
            required=True,
            placeholder="ex. Reminder/Warning",
            style=discord.TextStyle.short,
        )
        self.severity = discord.ui.TextInput(
            label="Severity (temp)",
            required=True,
            placeholder="ex. 1 (Minor)",
            style=discord.TextStyle.short,
        )
        self.notes = discord.ui.TextInput(
            label="Notes",
            required=False,
            placeholder="Enter additional details",
            style=discord.TextStyle.paragraph,
        )

        if choose_rule:
            self.add_item(self.rule)
        self.add_item(self.penalty)
        self.add_item(self.severity)
        self.add_item(self.notes)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        self.interaction = interaction
        self.stop()


""" Buttons """


class ReportRuleSelect(discord.ui.Select):
    def __init__(self, view: ReportView) -> None:
        super().__init__(
            placeholder="Select a Rule",
            max_values=1,
            options=self.getRuleSelectOptions(view.rule_selected),
            row=0,
            custom_id=f"{view.data.id}_0",
        )
        self._view = view

    def getRuleSelectOptions(
        self,
        selected: moderation.Rule = moderation.Rule(),
    ) -> list[discord.SelectOption]:
        options = []

        rules = [
            moderation.Rule("G.1.5.1"),
            moderation.Rule("G.1.5.4"),
            moderation.Rule("G.1.5.5"),
            moderation.Rule("G.1.5.6"),
            moderation.Rule("G.3.3"),
        ]

        for rule in rules:
            if rule.code == selected.code:
                options.append(
                    discord.SelectOption(
                        label=rule.name,
                        description=rule.code,
                        value=rule.code,
                        default=True,
                    )
                )
            else:
                options.append(
                    discord.SelectOption(
                        label=rule.name, description=rule.code, value=rule.code
                    )
                )

        if selected.code == "other":
            options.append(
                discord.SelectOption(label="Other", value="other", default=True)
            )
        else:
            options.append(discord.SelectOption(label="Other", value="other"))

        return options

    async def callback(self, interaction: discord.Interaction) -> None:
        newView = ReportView(
            self._view.bot, self._view.data, moderation.Rule(self.values[0])
        )

        await interaction.response.edit_message(view=newView, embed=newView.embed)


class NoOffenceButton(discord.ui.Button):
    def __init__(self, view: ReportView):
        super().__init__(
            style=discord.ButtonStyle.green,
            label="No offence",
            row=1,
            custom_id=f"{view.data.id}_1",
        )
        self._view = view

    async def callback(self, interaction: Interaction) -> None:
        self._view.data.penalty = "No offence"
        self._view.data.active = False

        moderation.addToHistory(self._view.data)  # TODO add creators

        newEmbed = ReportEmbed(self._view.data)

        await interaction.response.edit_message(embed=newEmbed, view=discord.ui.View())


class RemindButton(discord.ui.Button):
    def __init__(self, view: ReportView, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.red,
            label="Remind",
            disabled=disabled,
            row=1,
            custom_id=f"{view.data.id}_2",
        )
        self._view = view

    async def callback(self, interaction: Interaction) -> None:
        if not self._view.rule_selected.isNone():
            modal = ReminderModal()
        else:
            modal = ReminderModal(choose_rule=True)
        await interaction.response.send_modal(modal)
        await modal.wait()

        self._view.data.active = False
        self._view.data.penalty = modal.penalty.value
        self._view.data.severity = modal.severity.value
        if not self._view.rule_selected.isNone():
            self._view.data.rule = self._view.rule_selected
        else:
            rule = moderation.Rule()
            rule.name = modal.rule.value
            self._view.data.rule = rule

        moderation.addToHistory(self._view.data)

        await self._view.bot.sendReminder(self._view.data)

        newEmbed = ReportEmbed(self._view.data)

        await modal.interaction.delete_original_response()
        await interaction.followup.edit_message(
            interaction.message.id, embed=newEmbed, view=discord.ui.View()
        )

        await interaction.followup.send(
            f"Remider `{self._view.data.id}` sent to {self._view.data.offender.name}",
            ephemeral=True,
        )


class LeftButton(discord.ui.Button):
    def __init__(self, bot, data: [moderation.ReportData], index: int, disabled: bool):
        super().__init__(
            label="⇦",
            style=discord.ButtonStyle.secondary,
            disabled=disabled,
        )
        self.bot = bot
        self.data = data
        self.index = index

    async def callback(self, interaction: discord.Interaction) -> None:
        newView = ReportListDetailedView(self.bot, self.data, self.index - 1)
        await interaction.response.edit_message(embed=newView.embed, view=newView)


class RightButton(discord.ui.Button):
    def __init__(self, bot, data: [moderation.ReportData], index: int, disabled: bool):
        super().__init__(
            label="⇨",
            style=discord.ButtonStyle.secondary,
            disabled=disabled,
        )
        self.bot = bot
        self.data = data
        self.index = index

    async def callback(self, interaction: discord.Interaction) -> None:
        newView = ReportListDetailedView(self.bot, self.data, self.index + 1)
        await interaction.response.edit_message(embed=newView.embed, view=newView)
