from typing import Any, List, Optional, Union
import discord
from discord.components import SelectOption
from discord.emoji import Emoji
from discord.enums import ButtonStyle
from discord.interactions import Interaction
from discord.partial_emoji import PartialEmoji
from discord.utils import MISSING
import moderation.moderation as moderation
import asyncio
import random
import utils
import config
import logging


# Views
class ReportMessageView(discord.ui.View):
    def __init__(
        self,
        message: discord.Message,
        creator: discord.Member,
        disabled=False,
    ):
        super().__init__()
        self.timeout = config.defaultTimeout

        self.data = moderation.WarningData(
            offender=message.author,
            rule="S.4",
            creator=creator,
            proof=f'"{moderation.formatSwearWords(message.content)}" on {message.channel.mention}\n',
        )

        moderation.addToHistory(self.data)

        self.embed = ViolationReportEmbed(self.data)
        self.add_item(DeleteMsgButton(message, creator, disabled))

    @discord.ui.button(
        label="It isn't a swear word",
        custom_id=f"{random.randint(0, 100)}",
        style=discord.ButtonStyle.green,
    )
    async def removeWord(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        moderation.removeSwearWords(self.message.content)
        self.data.verdict = (
            "No offence, this word/s will no more be detected as swear words"
        )
        self.data.creators.append(interaction.user)

        moderation.addToHistory(self.data)

        newEmbed = ViolationReportEmbed(data=self.data)
        await interaction.response.edit_message(embed=newEmbed, view=discord.ui.View())

    @discord.ui.button(
        label="Warn",
        custom_id=f"{random.randint(0, 100)}",
        style=discord.ButtonStyle.red,
    )
    async def warn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        modal = WarningModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        if modal.notes.value == "":
            self.data.verdict = "The driver was warned"
        else:
            self.data.verdict = modal.notes.value

        self.data.creators.append(interaction.user)

        moderation.addToHistory(self.data)

        newEmbed = ViolationReportEmbed(self.data)

        await modal.interaction.delete_original_response()
        await interaction.followup.edit_message(
            interaction.message.id, embed=newEmbed, view=discord.ui.View()
        )
        await self.bot.sendWarning(self.data)

    async def on_timeout(self) -> None:
        # self.clear_items()  # TODO make it work
        self.data.verdict = "No offence (timeout)"
        moderation.addToHistory(self.data)
        print("No offence (timeout)")


class DeleteMsgButton(discord.ui.Button):
    def __init__(
        self,
        message: discord.Message,
        creator: discord.Member,
        disabled: bool,
    ):
        super().__init__(
            label="Delete message",
            custom_id=f"{random.randint(0, 100)}",
            style=discord.ButtonStyle.secondary,
            disabled=disabled,
        )
        self.message = message
        self.creator = creator

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.message.delete()
        newView = ReportMessageView(self.message, self.creator, True)
        await interaction.response.edit_message(embed=newView.embed, view=newView)
        await interaction.followup.send("Message deleted", ephemeral=True)


class AppealView(discord.ui.View):
    def __init__(
        self,
        bot,
        data: list[moderation.WarningData],
        disabled=False,
    ):
        super().__init__()
        self.bot = bot
        self.data = data
        self.timeout = config.defaultTimeout

        self.embed = ViolationReportEmbed(self.data, title="Warning")
        self.add_item(AppealButton(self.bot, self.data, disabled))

    async def on_timeout(self) -> None:
        # self.clear_items()  # TODO make it work
        print("Appeal timeout")


class AppealButton(discord.ui.Button):
    def __init__(
        self,
        bot,
        data: list[moderation.WarningData],
        disabled: bool,
    ):
        super().__init__(
            label="Appeal",
            custom_id=f"{random.randint(0, 100)}",
            style=discord.ButtonStyle.secondary,
            disabled=disabled,
        )
        self.bot = bot
        self.data = data

    async def callback(self, interaction: discord.Interaction) -> None:
        modal = WarningModal()
        modal.notes.required = True
        await interaction.response.send_modal(modal)
        await modal.wait()

        await modal.interaction.delete_original_response()

        view = AppealRequestView(self.bot, self.data, modal.notes.value)
        await self.bot.warningChannel.send(embed=view.embed, view=view)

        newView = AppealView(self.bot, self.data, disabled=True)
        await interaction.followup.edit_message(
            message_id=interaction.message.id, embed=newView.embed, view=newView
        )

        await interaction.followup.send("Appeal sent", ephemeral=True)


class AppealRequestView(discord.ui.View):
    def __init__(
        self,
        bot,
        data: list[moderation.WarningData],
        notes: str,
        accepted: list[int] = [],
    ):
        super().__init__()
        self.bot = bot
        self.data = data
        self.notes = notes
        self.accepted = accepted
        self.timeout = config.defaultTimeout

        self.embed = AppealRequestEmbed(self.data, notes, accepted)

    @discord.ui.button(
        label="Accept appeal",
        custom_id=f"{random.randint(0, 100)}",
        style=discord.ButtonStyle.green,
    )
    async def acceptAppeal(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if interaction.user.id in self.accepted:
            await interaction.response.send_message(
                "You have already voted", ephemeral=True
            )
        elif len(self.accepted) + 1 < 3:
            self.accepted.append(interaction.user.id)
            newView = AppealRequestView(
                bot=self.bot, data=self.data, notes=self.notes, accepted=self.accepted
            )
            await interaction.response.edit_message(embed=newView.embed, view=newView)
        else:
            self.accepted.append(interaction.user.id)
            newEmbed = AppealRequestEmbed(
                data=self.data, appealNotes=self.notes, accepted=self.accepted
            )
            await interaction.response.edit_message(
                embed=newEmbed, view=discord.ui.View()
            )

            moderation.addToHistory(self.data)

    async def on_timeout(self) -> None:
        print("Request of appeal timeout")


class ReportView(discord.ui.View):
    def __init__(
        self,
        bot,
        data: moderation.ReportData,
        rule_selected: moderation.Rule = moderation.Rule(),
    ):
        super().__init__()
        self.bot = bot
        self.timeout = config.defaultTimeout
        self.data = data
        self.rule_selected = rule_selected

        self.embed = ReportEmbed(self.data)
        self.add_item(ReportRuleSelect(self))

        if not self.rule_selected.isNone():
            self.add_item(RemindButton(self, False))
        else:
            self.add_item(RemindButton(self, True))

    @discord.ui.button(
        label="No offence",
        custom_id=f"{random.randint(0, 100)}",
        style=discord.ButtonStyle.green,
        row=1,
    )
    async def no_offence(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.data.verdict = "No offence"

        moderation.addToHistory(self.data)  # TODO add creators

        newEmbed = ReportEmbed(self.data)

        await interaction.response.edit_message(embed=newEmbed, view=discord.ui.View())

    async def on_timeout(self) -> None:
        self.clear_items()
        self.data.verdict = "No offence (timeout)"
        moderation.addToHistory(self.data)


class ReportRuleSelect(discord.ui.Select):
    def __init__(self, view: ReportView) -> None:
        super().__init__(
            placeholder="Select a Rule",
            max_values=1,
            options=self.getRuleSelectOptions(view.rule_selected),
            row=0,
        )
        self._view = view

    def getRuleSelectOptions(
        self,
        selected: moderation.Rule = moderation.Rule(),
    ) -> list[discord.SelectOption]:
        options = []

        rules = [moderation.Rule("1"), moderation.Rule("2"), moderation.Rule("3")]

        for rule in rules:
            if rule.code == selected.code:
                options.append(
                    discord.SelectOption(
                        label=rule.name,
                        description=rule.description,
                        value=rule.code,
                        default=True,
                    )
                )
            else:
                options.append(
                    discord.SelectOption(
                        label=rule.name, description=rule.description, value=rule.code
                    )
                )

        return options

    async def callback(self, interaction: discord.Interaction) -> None:
        newView = ReportView(
            self._view.bot, self._view.data, moderation.Rule(self.values[0])
        )

        await interaction.response.edit_message(view=newView, embed=newView.embed)


class RemindButton(discord.ui.Button):
    def __init__(self, view: ReportView, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.red, label="Remind", disabled=disabled, row=1
        )
        self._view = view

    async def callback(self, interaction: Interaction) -> None:
        modal = ReminderModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        self._view.data.verdict = modal.verdict.value
        self._view.data.rule = self._view.rule_selected

        moderation.addToHistory(self._view.data)  # TODO add creators

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
        custom_id=f"{random.randint(0, 100)}",
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


class LeftButton(discord.ui.Button):
    def __init__(self, bot, data: [moderation.ReportData], index: int, disabled: bool):
        super().__init__(
            label="⇦",
            custom_id=f"{random.randint(0, 100)}",
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
            custom_id=f"{random.randint(0, 100)}",
            style=discord.ButtonStyle.secondary,
            disabled=disabled,
        )
        self.bot = bot
        self.data = data
        self.index = index

    async def callback(self, interaction: discord.Interaction) -> None:
        newView = ReportListDetailedView(self.bot, self.data, self.index + 1)
        await interaction.response.edit_message(embed=newView.embed, view=newView)


# Embeds
class ViolationReportEmbed(discord.Embed):
    def __init__(self, data: moderation.WarningData, title: str = "Violation Report"):
        super().__init__(title=title, color=0xFFFFFF)
        self.description = f"**ID:** `{data.id}`\n"
        self.description += (
            f"**User:** {data.offender.name} ({data.offender.mention})\n"
        )
        self.description += (
            f"**Rule:** `{data.rule}`\n> {moderation.getRule(data.rule)}\n"
        )

        if data.proof != "":
            if utils.isLink(data.proof):
                self.description += f"**Proof:** [link to proof]({data.proof})\n"
            else:
                self.description += f"**Proof:** {data.proof}"

        if data.verdict != "":
            self.description += f"\n**Verdict:** {data.verdict}\n"

        self.set_thumbnail(url=data.offender.avatar.url)
        self.timestamp = data.timestamp

        footer = f"Created by {data.creators[0].name}"
        self.set_footer(text=footer, icon_url=data.creators[0].avatar.url)
        for i in range(1, len(data.creators)):
            footer += f" & {data.creators[i].name}"


class AppealRequestEmbed(ViolationReportEmbed):
    def __init__(
        self, data: moderation.WarningData, appealNotes: str, accepted: list[int] = []
    ):
        super().__init__(data, title="Appeal Request")
        self.description += f"\n**Appeal reason:** {appealNotes}\n"

        self.description += f"Appeal accepted: `{len(accepted)}/3`"


class ViolationListEmbed(discord.Embed):
    def __init__(self, data: list[moderation.WarningData]):
        super().__init__(title=f"History", color=0xFFFFFF)
        self.description = f"**Name**:{data[0].offender.mention}\n"

        for violation in data:
            self.description += f'- <t:{round(violation.timestamp.timestamp())}:d>`-{violation.rule}-"{violation.verdict}"`\n'

        self.set_thumbnail(url=data[0].offender.avatar.url)


class ReportEmbed(discord.Embed):
    def __init__(self, data: moderation.ReportData, title: str = "Report"):
        super().__init__(title=title, color=0xFFFFFF)
        self.description = f"**ID:** `{data.id}`\n"

        self.description += (
            f"**User:** {data.offender.name} ({data.offender.mention})\n"
        )
        self.description += f"**Round:** `{data.league} R{data.round}`\n"

        if not data.rule.isNone():
            self.description += (
                f"**Rule:** {data.rule.name}\n> {data.rule.description}\n"
            )

        self.description += f"**Proof:** [Link to proof]({data.proof})\n"

        self.description += f"**Description:**\n> {data.notes}\n"

        if data.verdict != "":
            self.description += f"**Verdict:**\n> {data.verdict}\n"

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
        super().__init__(title=title, color=0xFF0000)
        self.description = f"**ID:** `{data.id}`\n"

        self.description += (
            f"**User:** {data.offender.name} ({data.offender.mention})\n"
        )
        self.description += f"**Round:** `{data.league} R{data.round}`\n"

        self.description += f"**Rule:** {data.rule.name}\n> {data.rule.description}\n"

        self.description += f"**Proof:** [link to proof]({data.proof})\n"

        if data.verdict != "":
            self.description += f"**Verdict:**\n> {data.verdict}\n"

        try:
            self.set_thumbnail(url=data.offender.avatar.url)
        except:
            logging.error("Thumbnail non caricata")

        self.timestamp = data.timestamp


class ReportListEmbed(discord.Embed):
    def __init__(self, data: list[moderation.ReportData]):
        super().__init__(title=f"Report History", color=0xFFFFFF)
        self.description = f"**Name**:{data[0].offender.mention}\n```"

        for violation in data:
            self.description += (
                f"{violation.id} {violation.timestamp.date()} violation.rule\n"
            )

        self.description += "```\n"
        self.set_thumbnail(url=data[0].offender.avatar.url)


# Modals
class ViolationModal(discord.ui.Modal, title="Details"):
    def __init__(self):
        super().__init__()
        self.notes = discord.ui.TextInput(
            label="Notes",
            required=False,
            placeholder="Enter additional details",
            style=discord.TextStyle.paragraph,
        )
        self.link = discord.ui.TextInput(
            label="Proof link",
            required=False,
            placeholder='ex. "youtube.com/watch?v=dQw4w9WgXcQ"',
        )
        self.add_item(self.notes)
        self.add_item(self.link)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        self.interaction = interaction
        self.stop()


class WarningModal(discord.ui.Modal, title="Details"):
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
            placeholder='ex. "https://youtu.be/dQw4w9WgXcQ?si=Yoyp5Zztw6mI_AsG&t=0"',  # TODO check if he inserted a link
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
        self.verdict = discord.ui.TextInput(
            label="Verdict",
            required=True,
            placeholder="Enter additional details",
            style=discord.TextStyle.paragraph,
        )
        self.add_item(self.verdict)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        self.interaction = interaction
        self.stop()
