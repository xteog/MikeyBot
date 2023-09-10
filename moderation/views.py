import discord
import moderation.moderation as moderation
import asyncio
import random
import utils
import config


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
        bot,
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
        self.bot = bot
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
