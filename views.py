from typing import Any
from discord.interactions import Interaction
from discord.ui.item import Item
import defs
import discord
import moderation
import asyncio
import datetime
import random
import utils


class ViolationReportView(discord.ui.View):
    def __init__(
        self,
        bot,
        message: discord.Message,
        creator: discord.Member,
        disabled=False,
    ):
        super().__init__()
        self.bot = bot
        self.rule = "S.4"
        self.user = message.author
        self.message = message
        self.creator = creator
        self.timeout = self.bot.config.defaultTimeout

        self.embed = ViolationReportEmbed(
            rule=self.rule, user=self.user, message=message, creators=[creator]
        )

        self.add_item(DeleteMsgButton(bot, message, creator, disabled))

    @discord.ui.button(
        label="It isn't a swear word",
        custom_id=f"{random.randint(0, 100)}",
        style=discord.ButtonStyle.green,
    )
    async def removeWord(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        moderation.removeSwearWords(self.message.content)
        newEmbed = ViolationReportEmbed(
            rule=self.rule,
            user=self.user,
            message=self.message,
            creators=[self.creator, interaction.user],
            verdict="No offence, this word/s will no more be detected as swear words",
        )
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
            verdict = "The driver was warned"
        else:
            verdict = modal.notes.value
        proof = f'"{moderation.formatSwearWords(self.message.content)}" on {self.message.channel.mention}\n'

        moderation.addToHistory("op", self.user, self.rule, proof, verdict)

        newEmbed = ViolationReportEmbed(
            rule=self.rule,
            user=self.user,
            message=self.message,
            creators=[self.creator, interaction.user],
            verdict=verdict,
        )

        await modal.interaction.delete_original_response()
        await interaction.followup.edit_message(
            interaction.message.id, embed=newEmbed, view=discord.ui.View()
        )
        await self.bot.sendWarning(
            rule=self.rule,
            user=self.user,
            creators=[self.creator, interaction.user],
            notes=verdict,
            proof=proof,
        )

    async def on_timeout(self) -> None:
        # self.clear_items()  # TODO make it work
        moderation.addToHistory(
            id="None",
            user=self.user,
            rule="S.4",
            proof=f'"{moderation.formatSwearWords(self.message.content)}" on {self.message.channel.mention}\n',
            verdict="No offence (timeout)",
        )
        print("No offence (timeout)")


class DeleteMsgButton(discord.ui.Button):  # TODO add creator
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
        newView = ViolationReportView(self.bot, self.message, self.creator, True)
        await interaction.response.edit_message(embed=newView.embed, view=newView)
        await interaction.followup.send("Message deleted", ephemeral=True)


class ViolationReportEmbed(discord.Embed):
    def __init__(
        self,
        rule: str,
        creators: list[discord.Member],
        user: discord.Member,
        message: discord.Message | None = None,  # TODO sostituisci con link/proof
        link: str = "",
        verdict: str = "",
        title: str = "Violation Report",
    ):
        super().__init__(title=title, color=0xFFFFFF)
        self.description = f"**ID:** `None`\n"
        self.description += f"**User:** {user.name} (<@{user.id}>)\n"
        self.description += f"**Rule:** `{rule}`\n> {moderation.getRule(rule)}\n"
        self.set_thumbnail(url=user.avatar.url)

        if message != None:
            self.description += f'**Proof:** "{moderation.formatSwearWords(message.content)}" on #{message.channel.mention}\n'

        if link != "":
            if len(link) > 6 and link[0:5] == "https":
                self.description += f"**Proof:** [link to proof]({link})\n"
            else:
                self.description += f"**Proof:** {link}"

        if verdict != "":
            self.description += f"\n**Verdict:** {verdict}\n"

        self.timestamp = datetime.datetime.utcnow()

        footer = f"Created by {creators[0].name}"
        for i in range(1, len(creators)):
            footer += f" & {creators[i].name}"
        self.set_footer(text=footer, icon_url=creators[0].avatar.url)


class RegionFilterSelect(discord.ui.View):
    def __init__(self, database, client, elements):
        self.database = database
        self.client = client
        self.elements = elements
        self.closed = False
        options = []
        for map in self.elements:
            desc = ""
            data = utils.read(defs.DB["mapData"].format(map))
            for i in data["mapItems"]:
                if i["flags"] == 41:
                    if i["teamId"] == "COLONIALS":
                        desc = "Colonials"
                        icon = discord.PartialEmoji(
                            name=defs.DB["emojis"]["ColonialLogo"][0],
                            id=defs.DB["emojis"]["ColonialLogo"][1],
                        )
                    elif i["teamId"] == "WARDENS":
                        desc = "Wardens"
                        icon = discord.PartialEmoji(
                            name=defs.DB["emojis"]["WardenLogo"][0],
                            id=defs.DB["emojis"]["WardenLogo"][1],
                        )
                    else:
                        icon = None
            options.append(
                discord.SelectOption(label=map, description=desc, emoji=icon)
            )
        super().__init__(
            placeholder="Regioni",
            min_values=0,
            max_values=len(options),
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        self.closed = True
        await interaction.response.defer()


class EventFilterView(discord.ui.View):
    def __init__(self, database, client):
        super().__init__()
        self.database = database
        self.client = client
        self.select1 = RegionFilterSelect(database, client, defs.MAP_NAME[0:24])
        self.select2 = RegionFilterSelect(database, client, defs.MAP_NAME[24:])
        self.add_item(self.select1)
        self.add_item(self.select2)

    async def wait(self):
        while not (self.select1.closed and self.select2.closed):
            await asyncio.sleep(1)

        return self.select1.values + self.select2.values


class DepotModal(discord.ui.Modal, title="Dati Deposito"):
    def __init__(self):
        super().__init__()
        self.group = discord.ui.TextInput(
            label="Gruppo",
            required=False,
            placeholder="Inserisci il nome del gruppo del deposito",
        )
        self.name = discord.ui.TextInput(
            label="Nome", placeholder="Inserisci il nome del deposito"
        )
        self.passcode = discord.ui.TextInput(
            label="Passcode",
            placeholder="Inserisci il codice del deposito del deposito",
        )
        self.desc = discord.ui.TextInput(
            label="Descrizione",
            required=False,
            placeholder="Inserisci la descrizione del deposito",
            style=discord.TextStyle.paragraph,
        )
        self.add_item(self.group)
        self.add_item(self.name)
        self.add_item(self.passcode)
        self.add_item(self.desc)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        self.interaction = interaction
        self.stop()


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

        if self.notes == " ":
            print("vuoto")  # TODO risolvi
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


class ReminderModal(discord.ui.Modal, title="Info ordine"):
    def __init__(self):
        super().__init__()
        self.name = discord.ui.TextInput(
            label="Item", placeholder="Inserisci l'item da ritirare"
        )
        self.quantity = discord.ui.TextInput(
            label="Quantità",
            required=False,
            placeholder="Inserisci la quantità dell'item da ritirare",
        )
        self.expiry = discord.ui.TextInput(
            label="Tempo rimanente", placeholder="'mm', 'hh:mm' oppure 'dd:hh:mm'"
        )
        self.desc = discord.ui.TextInput(
            label="Nota",
            required=False,
            placeholder="Inserisci una nota opzionale",
            style=discord.TextStyle.paragraph,
        )
        self.add_item(self.name)
        self.add_item(self.quantity)
        self.add_item(self.expiry)
        self.add_item(self.desc)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        self.interaction = interaction
        self.stop()


class DepotEmbed(discord.Embed):
    def __init__(self, group, depots, callback):
        super().__init__(
            title="Lista Depositi",
            description="Prima di interagire guardare la descrizione di questo canale.",
        )
        for d in depots:
            if d["group"] == group:
                emoji = defs.DB["emojis"][str(d["iconType"])]
                self.add_field(
                    name=f"<:{emoji[0]}:{emoji[1]}> {defs.ICON_ID[d['iconType']]} a {d['location']}({d['map']})",
                    value=f"Nome: `{d['name']}`\nPasscode: `{d['passcode']}`\n{d['desc']}",
                    inline=False,
                )
        self.fileMap = discord.File(defs.PATH + "/data/tempDepotMap.png")
        self.set_image(url="attachment://tempDepotMap.png")


class ReminderEmbed(discord.Embed):
    def __init__(self, reminder, user, expired=False):
        r = reminder
        emoji = defs.DB["emojis"][str(r["iconType"])]

        if not expired:
            expiry = datetime.datetime.now()
            expiry = expiry.replace(
                day=r["expiry"]["d"], hour=r["expiry"]["h"], minute=r["expiry"]["m"]
            )
            timestamp = int(datetime.datetime.timestamp(expiry))
            super().__init__(
                title=f"{r['item']} da ritirare",
                description=f"Luogo: <:{emoji[0]}:{emoji[1]}> {defs.ICON_ID[r['iconType']]} a {r['location']}({r['map']})\nQuantità: {r['quantity']}\nScadenza: <t:{timestamp}:R> (<t:{timestamp}:t>)\n{r['desc']}",
                color=0x5865F2,
            )
            self.fileMap = discord.File(defs.PATH + "/data/tempCropMap.png")
            self.set_thumbnail(url="attachment://tempCropMap.png")
        else:
            expiry = datetime.datetime.now()
            expiry = expiry.replace(
                day=r["expiry"]["d"], hour=r["expiry"]["h"], minute=r["expiry"]["m"]
            )
            timestamp = int(datetime.datetime.timestamp(expiry))
            super().__init__(
                title=f"{r['item']} ritirato da {r['pickedUp']}",
                description=f"Luogo: <:{emoji[0]}:{emoji[1]}> {defs.ICON_ID[r['iconType']]} a {r['location']}({r['map']})\nQuantità: {r['quantity']}\nScadenza: <t:{timestamp}:R>\n{r['desc']}",
            )
            self.fileMap = discord.File(defs.PATH + "/data/tempCropMap.png")
            self.set_thumbnail(url="attachment://tempCropMap.png")
        self.set_author(name=user.name, icon_url=user.avatar.url)


class DepotButton(discord.ui.Button):
    def __init__(self, group, depots, disabled=True):
        self.group = group
        self.depots = depots
        super().__init__(
            label=self.group,
            custom_id=self.group,
            style=discord.ButtonStyle.secondary,
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction):
        embed, view = view_depots(self.group, self.depots, True)
        await interaction.response.edit_message(embed=embed, view=view)


class ReminderButton(discord.ui.Button):
    def __init__(self, reminder, user, disabled=False):
        self.id = reminder["item"] + "".join(reminder["expiry"]) + reminder["location"]
        self.reminder = reminder
        self.user = user
        super().__init__(
            label="Remind Me",
            custom_id=self.id,
            style=discord.ButtonStyle.primary,
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction):
        if not (str(interaction.user.id) in self.reminder["last_reminder"]):
            self.reminder["last_reminder"][str(interaction.user.id)] = {
                "d": datetime.datetime.now().day,
                "h": datetime.datetime.now().hour,
                "m": datetime.datetime.now().minute,
            }
            await interaction.response.defer()
            data = utils.read(defs.DB["database"])
            data["reminders"][self.id] = self.reminder
            utils.write(defs.DB["database"], data)

            # await interaction.response.send_message("Aggiunta notifica", ephemeral=True)

            expiry = datetime.datetime.now()
            expiry = expiry.replace(
                day=self.reminder["expiry"]["d"],
                hour=self.reminder["expiry"]["h"],
                minute=self.reminder["expiry"]["m"],
            )
            while expiry > datetime.datetime.now():
                if await send_reminder(interaction.user.id, self.reminder):
                    await interaction.followup.send(
                        f"<@!{interaction.user.id}> Mancano 10 minuti per {self.reminder['item']} a {self.reminder['location']}",
                        ephemeral=True,
                    )
                await asyncio.sleep(30)

            await interaction.followup.send(
                f"<@!{interaction.user.id}> {self.reminder['item']} pronto a {self.reminder['location']}!",
                ephemeral=True,
            )
            embed, view = view_reminder(self.reminder, self.user, True)
            await interaction.edit_original_response(embed=embed, view=view)
        else:
            await interaction.response.send_message("User già presente", ephemeral=True)


class PickUpButton(discord.ui.Button):
    def __init__(self, reminder, user, disabled=False):
        self.id = reminder["item"] + "".join(reminder["expiry"]) + reminder["location"]
        self.reminder = reminder
        self.user = user
        super().__init__(
            label="<:ItalicaRana1:881194507863986177>Ritirato",
            custom_id=self.id,
            style=discord.ButtonStyle.primary,
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction):
        data = utils.read(defs.DB["database"])
        data["reminders"][self.id]["pickedUp"] = interaction.user.name
        utils.write(defs.DB["database"], data)
        embed, view = view_reminder(data["reminders"][self.id], self.user, True)
        await interaction.response.edit_message(embed=embed, view=view)


async def send_reminder(id, reminder):
    r = reminder
    expiry = datetime.datetime.now()
    expiry = expiry.replace(
        day=r["expiry"]["d"], hour=r["expiry"]["h"], minute=r["expiry"]["m"]
    )

    last_reminder = datetime.datetime.now()
    last_reminder = last_reminder.replace(
        day=r["last_reminder"][str(id)]["d"],
        hour=r["last_reminder"][str(id)]["h"],
        minute=r["last_reminder"][str(id)]["m"],
    )

    if (
        expiry - datetime.timedelta(minutes=10) < datetime.datetime.now()
        and expiry - datetime.timedelta(minutes=10) > last_reminder
    ):
        reminder["last_reminder"][str(id)] = {
            "d": datetime.datetime.now().day,
            "h": datetime.datetime.now().hour,
            "m": datetime.datetime.now().minute,
        }
        data = utils.read(defs.DB["database"])
        data["reminders"][r["item"] + "dhm" + r["location"]] = r

        utils.write(defs.DB["database"], data)

        return True
    return False


def view_depots(group, depots, callback=False):
    embed = DepotEmbed(group, depots, callback)
    view = discord.ui.View(timeout=None)
    groups = []
    for d in depots:
        if not (d["group"] in groups):
            if d["group"] == group:
                disabled = True
            else:
                disabled = False
            groups.append(d["group"])
            view.add_item(DepotButton(d["group"], depots, disabled))

    return (embed, view)


def view_reminder(reminder, user, expired=False):
    if expired:
        if reminder["pickedUp"] == None:
            view = discord.ui.View(timeout=None)
            view.add_item(PickUpButton(reminder, user))
            embed = ReminderEmbed(reminder, user)
        else:
            view = discord.ui.View()
            embed = ReminderEmbed(reminder, user, expired)

    else:
        view = discord.ui.View(timeout=None)
        embed = ReminderEmbed(reminder, user)
        view.add_item(ReminderButton(reminder, user))

    return (embed, view)


def make_view(map, region):
    data = utils.read(defs.DB["mapData"].format(map))
    for i in data["mapItems"]:
        if i["flags"] == 41:
            if i["teamId"] == "COLONIALS":
                desc = "Colonials"
                icon = discord.PartialEmoji(
                    name=defs.DB["emojis"]["ColonialLogo"][0],
                    id=defs.DB["emojis"]["ColonialLogo"][1],
                )
            elif i["teamId"] == "WARDENS":
                desc = "Wardens"
                icon = discord.PartialEmoji(
                    name=defs.DB["emojis"]["WardenLogo"][0],
                    id=defs.DB["emojis"]["WardenLogo"][1],
                )
    view = discord.ui.View()
    view.add_item(
        discord.ui.Select(
            options=[discord.SelectOption(label=map, emoji=icon, default=True)],
            disabled=True,
        )
    )
    for name in data["mapTextItems"]:
        if name["text"] == region:
            item = data["mapItems"][name["location"]]
            icon = item["iconType"]
            if item["teamId"] == "COLONIALS":
                str = f"{icon}C"
            elif item["teamId"] == "WARDENS":
                str = f"{icon}W"
            else:
                str = f"{icon}"
            icon = discord.PartialEmoji(
                name=defs.DB["emojis"][str][0], id=defs.DB["emojis"][str][1]
            )
    view.add_item(
        discord.ui.Select(
            options=[discord.SelectOption(label=region, emoji=icon, default=True)],
            disabled=True,
        )
    )
    return view
