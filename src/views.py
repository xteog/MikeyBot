import discord
from discord.interactions import Interaction
from database.beans import Report, Rule
import utils
import config
from discord.ext import commands
import logging


""" Views """


class ReportView(discord.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        data: Report,
        rule_selected: Rule | None = None,
    ):
        super().__init__(timeout=None)
        self.bot = bot
        self.data = data
        self.rule_selected = rule_selected

        self.embed = ReportEmbed(self.data)
        self.add_item(ReportRuleSelect(self))
        self.add_item(AggravatedButton(self))
        self.add_item(NoOffenceButton(self))
        if not self.rule_selected == None:
            self.add_item(
                RemindButton(view=self, disabled=False)
            )
        else:
            self.add_item(RemindButton(view=self, disabled=True))


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
        data: Report,
        permission: bool = True,
    ):
        super().__init__(title="Report", color=0xFFFFFF)

        season, round = utils.formatLeagueRounds(
            league=data.league, season=data.season, round=data.round
        )

        if data.penalty != None:
            self.title = data.penalty

        self.description = f"**ID:** `{data.id}`\n"

        self.description += f"**User:** {data.offender.display_name} "

        if data.offender != None:
            self.description += f"({data.offender.mention})\n"

        if not data.active:
            if data.aggravated:
                self.description += f"**Aggravated:** ☑\n"
            else:
                self.description += f"**Aggravated:** ☐\n"

        self.description += f"**Round:** `{data.league}{season}R{round}`\n"

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
            footer = f"Created by {data.sender.display_name}"

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
    def __init__(self, view: ReportView) -> None:
        self.reportView = view
        super().__init__(
            placeholder="Select a Rule",
            max_values=1,
            options=self.getRuleSelectOptions(view.rule_selected, view.data.league),
            row=0,
            custom_id=f"{view.data.id}_0",
        )

    def getRuleSelectOptions(
        self, selected: Rule | None, league: str = ""
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
        newView = ReportView(self.reportView.bot, self.reportView.data, rule)

        await interaction.response.edit_message(view=newView, embed=newView.embed)


class NoOffenceButton(discord.ui.Button):
    def __init__(self, view: ReportView):
        super().__init__(
            style=discord.ButtonStyle.green,
            label="No offence",
            row=2,
            custom_id=f"{view.data.id}_1",
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

        newEmbed = ReportEmbed(report, permission=True)

        await modal.interaction.delete_original_response()
        await interaction.followup.edit_message(
            interaction.message.id, embed=newEmbed, view=discord.ui.View()
        )


class RemindButton(discord.ui.Button):
    def __init__(self, view: ReportView, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.red,
            label="Remind",
            disabled=disabled,
            row=2,
            custom_id=f"{view.data.id}_2",
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
        self.reportView.data.rule = self.reportView.rule_selected

        report = await self.reportView.bot.closeReport(
            report=self.reportView.data, offence=True
        )

        newEmbed = ReportEmbed(self.reportView.data, permission=True)

        await modal.interaction.delete_original_response()
        await interaction.followup.edit_message(
            interaction.message.id, embed=newEmbed, view=discord.ui.View()
        )

        await interaction.followup.send(
            f"{report.penalty} `{self.reportView.data.id}` sent to {self.reportView.bot.getNick(self.reportView.data.offender)}",
            ephemeral=True,
        )


class AggravatedButton(discord.ui.Button):
    def __init__(self, view: ReportView):
        super().__init__(
            style=discord.ButtonStyle.gray,
            label="☐ Aggravated",
            row=1,
            custom_id=f"{view.data.id}_3",
        )

        self.reportView = view

        if self.reportView.data.aggravated:
            self.label = "☑ Aggravated"
            self.style = discord.ButtonStyle.red

    async def callback(self, interaction: discord.Interaction) -> None:
        self.reportView.data.aggravated = not self.reportView.data.aggravated

        newView = ReportView(
            self.reportView.bot,
            self.reportView.data,
            rule_selected=self.reportView.rule_selected,
        )

        await interaction.response.edit_message(view=newView, embed=newView.embed)
