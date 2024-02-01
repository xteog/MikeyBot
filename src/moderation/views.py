from typing import Optional
import discord
from discord.interactions import Interaction
import moderation.violations as violations
import utils
import config as config
import logging


""" Views """


class ReportView(discord.ui.View):
    def __init__(
        self,
        bot,
        data: violations.ReportData,
        rule_selected: violations.Rule = violations.Rule(),
    ):
        super().__init__(timeout=None)
        self.bot = bot
        self.data = data
        self.rule_selected = rule_selected

        self.embed = ReportEmbed(self.data, permission=True)

        self.add_item(ReportRuleSelect(self))
        self.add_item(NoOffenceButton(self))
        if not self.rule_selected.isNone():
            self.add_item(RemindButton(self, False))
        else:
            self.add_item(RemindButton(self, True))


class ReportListView(discord.ui.View):
    def __init__(self, bot, data: [violations.ReportData], permission: bool):
        super().__init__()
        self.bot = bot
        self.timeout = config.defaultTimeout
        self.data = data
        self.permission = permission

        self.embed = ReportListEmbed(self.data)

    @discord.ui.button(
        label="Detailed View",
        style=discord.ButtonStyle.gray,
    )
    async def detailed_view(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        view = ReportListDetailedView(self.bot, self.data, permission=self.permission)
        await interaction.response.send_message(
            view=view, embed=view.embed, ephemeral=True
        )


class ReportListDetailedView(discord.ui.View):
    def __init__(
        self,
        bot,
        data: [violations.ReportData],
        permission: bool,
        index: int = 0,
    ):
        super().__init__()
        self.bot = bot
        self.timeout = config.defaultTimeout
        self.data = data
        self.permission = permission
        self.index = index

        self.embed = ReportEmbed(self.data[self.index], permission=self.permission)
        if self.index <= 0:
            self.add_item(LeftButton(self, True))
        else:
            self.add_item(LeftButton(self, False))
        self.add_item(
            discord.ui.Button(
                label=f"{self.index + 1}/{len(self.data)}",
                style=discord.ButtonStyle.gray,
                disabled=True,
            )
        )
        if self.index >= len(self.data) - 1:
            self.add_item(RightButton(self, True))
        else:
            self.add_item(RightButton(self, False))


class ReminderView(discord.ui.View):
    def __init__(self, bot, data):
        super().__init__()
        self.bot = bot
        self.data = data
        self.embed = ReportEmbed(data, permission=False)
        #self.add_item(AppealButton(self))

class SwitchView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Nintendo Switch Role", custom_id="switch", style=discord.ButtonStyle.danger)
    async def switchRole(self, interaction: Interaction, button):
        logging.info(f"{interaction.user.display_name} used the Switch button")
        guild = await self.bot.fetch_guild(config.serverId)
        role = guild.get_role(1202374974380179499)

        await interaction.user.add_roles(role)
        await interaction.response.send_message("Role added", ephemeral=True)


""" Embeds """


class ReportEmbed(discord.Embed):
    def __init__(
        self,
        data: violations.ReportData,
        permission: bool,
    ):
        super().__init__(title="Report", color=0xFFFFFF)

        if len(data.penalty) > 1:
            self.title = data.penalty

        self.description = f"**ID:** `{data.id}`\n"

        self.description += (
            f"**User:** {data.offender.name} ({data.offender.mention})\n"
        )

        if len(data.severity) > 0:
            self.description += f"**Severity:** {data.severity}\n"

        if data.round != None:
            self.description += f"**Round:** `{data.league}R{data.round}`\n"
        else:
            self.description += f"**Round:** `{data.league}`\n"

        if not data.rule.isNone():
            self.description += f"**Rule:** {data.rule.name}\n{utils.formatBlockQuote(data.rule.description)}\n"

        if len(data.desc) > 0 and permission:
            self.description += (
                f"**Description:**\n{utils.formatBlockQuote(data.desc)}\n"
            )

        isLink, error = utils.isLink(data.proof)
        if isLink:
            self.description += f"**Proof:** [Link to proof]({data.proof})\n"
        else:
            self.description += f"**Proof:** {data.proof}\n"

        if len(data.notes) > 0:
            self.description += f"**Notes:**\n{utils.formatBlockQuote(data.notes)}\n"

        try:
            self.set_thumbnail(url=data.offender.avatar.url)
        except:
            logging.warning("Thumbnail non caricata")

        self.timestamp = data.timestamp

        if permission:
            footer = f"Created by {data.creator.name}"

            try:
                self.set_footer(text=footer, icon_url=data.creator.avatar.url)
            except:
                self.set_footer(text=footer)


class ReportListEmbed(discord.Embed):
    def __init__(self, data: list[violations.ReportData]):
        super().__init__(title=f"Report History", color=0xFFFFFF)
        self.description = (
            f"**Name**: {data[0].offender.name} {data[0].offender.mention}\n```"
        )

        for report in data:
            self.description += f"{report.id}|{report.timestamp.date()}|{report.penalty} {report.rule.name}\n"

        self.description += "```\n"
        try:
            self.set_thumbnail(url=data[0].offender.avatar.url)
        except:
            logging.warning("Thumbnail non caricata")


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
    def __init__(self, offence=True):
        super().__init__()
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

        if offence:
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
            options=self.getRuleSelectOptions(view.rule_selected, view.data.league),
            row=0,
            custom_id=f"{view.data.id}_0",
        )
        self._view = view

    def getRuleSelectOptions(
        self,
        selected: violations.Rule = violations.Rule(),
        league: str = ""
    ) -> list[discord.SelectOption]:
        options = []

        if league != "Off-Track":
            rules = [
                violations.Rule("H.1.1"),
                violations.Rule("H.1.2"),
                violations.Rule("H.1.3"),
                violations.Rule("H.1.4"),
                violations.Rule("H.1.5"),
                violations.Rule("H.1.6"),
                violations.Rule("H.1.7"),
                violations.Rule("H.1.8"),
                violations.Rule("H.1.9"),
            ]
        else:
            rules = [
                violations.Rule("G.3.2.1"),
                violations.Rule("G.3.2.2")
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

        return options

    async def callback(self, interaction: discord.Interaction) -> None:
        newView = ReportView(
            self._view.bot, self._view.data, violations.Rule(self.values[0])
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
        logging.info(f'{interaction.user.name} used the "No offence" Button')

        modal = ReminderModal(offence=False)
        await interaction.response.send_modal(modal)
        await modal.wait()

        self._view.data.penalty = "No offence"
        self._view.data.active = False
        self._view.data.notes = modal.notes.value

        violations.addToHistory(self._view.data)  # TODO add creators

        await self._view.bot.sendReminder(self._view.data, False)

        newEmbed = ReportEmbed(self._view.data, permission=True)

        await modal.interaction.delete_original_response()
        await interaction.followup.edit_message(
            interaction.message.id, embed=newEmbed, view=discord.ui.View()
        )
        await self._view.bot.archiveThread(self._view.data.id)


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
        logging.info(f'{interaction.user.name} used the "Remind" Button')
        modal = ReminderModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        self._view.data.active = False
        self._view.data.penalty = modal.penalty.value
        self._view.data.severity = modal.severity.value
        self._view.data.notes = modal.notes.value
        self._view.data.rule = self._view.rule_selected

        violations.addToHistory(self._view.data)

        await self._view.bot.sendReminder(self._view.data)

        newEmbed = ReportEmbed(self._view.data, permission=True)

        await modal.interaction.delete_original_response()
        await interaction.followup.edit_message(
            interaction.message.id, embed=newEmbed, view=discord.ui.View()
        )

        await self._view.bot.archiveThread(self._view.data.id)

        await interaction.followup.send(
            f"Remider `{self._view.data.id}` sent to {self._view.data.offender.name}",
            ephemeral=True,
        )


class LeftButton(discord.ui.Button):
    def __init__(self, view: ReportListDetailedView, disabled: bool):
        super().__init__(
            label="←",
            style=discord.ButtonStyle.secondary,
            disabled=disabled,
        )
        self._view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        newView = ReportListDetailedView(
            self._view.bot,
            self._view.data,
            permission=self._view.permission,
            index=self._view.index - 1,
        )
        await interaction.response.edit_message(embed=newView.embed, view=newView)


class RightButton(discord.ui.Button):
    def __init__(self, view: ReportListDetailedView, disabled: bool):
        super().__init__(
            label="→",
            style=discord.ButtonStyle.secondary,
            disabled=disabled,
        )
        self._view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        newView = ReportListDetailedView(
            self._view.bot,
            self._view.data,
            permission=self._view.permission,
            index=self._view.index + 1,
        )
        await interaction.response.edit_message(embed=newView.embed, view=newView)


class AppealButton(discord.ui.Button):
    def __init__(self, view: ReminderView, disabled: bool = False):
        super().__init__(
            label="Appeal",
            style=discord.ButtonStyle.secondary,
            disabled=disabled,
        )
        self._view = view

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.edit_message(embed=newView.embed, view=newView)
