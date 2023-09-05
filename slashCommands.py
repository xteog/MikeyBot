import discord
import math
import logging
import main
import sys
import config
import moderation
import defs
import traceback
import utils
import json
import views
import datetime
import permissions


async def rules_autocomplete(interaction: discord.Interaction, current: str) -> list:
    global cog
    
    codes = cog.rules.keys()
    list = []
    current = current.upper()


    for code in codes:
        if (len(code) >= len(current) and current == code[0:len(current)]) or current == code:
            name = f"{code}: {cog.rules[code]}"

            if len(name) >= 100:
                name = name[0:96] + "..."
            
            list.append(
                discord.app_commands.Choice(
                    name= name,
                    value=code,
                )
            )

    if len(list) == 0:
        #TODO lev_dist
        print("non trovato")

    return list[0:25]

async def location_autocomplete(interaction: discord.Interaction, current: str):
    global cog

    for i in range(len(cog.list_locations)):
        cog.list_locations[i][2] = utils.lev_dist(
            current.lower(),
            cog.list_locations[i][0][
                0 : min(len(current), len(cog.list_locations[i][0]))
            ].lower(),
        )

    list_f = []
    for i in range(5):
        minimum = 0
        for j in range(len(cog.list_locations)):
            if cog.list_locations[minimum][2] > cog.list_locations[j][2]:
                minimum = j
        cog.list_locations[minimum][2] = 100
        list_f.append(
            discord.app_commands.Choice(
                name=f"{cog.list_locations[minimum][0]} ({defs.ICON_ID[cog.list_locations[minimum][3]]})",
                value=json.dumps(cog.list_locations[minimum]),
            )
        )

    return list_f


async def factory_autocomplete(interaction: discord.Interaction, current: str):
    global cog

    for i in range(len(cog.list_factory)):
        cog.list_factory[i][2] = utils.lev_dist(
            current.lower(),
            cog.list_factory[i][0][
                0 : min(len(current), len(cog.list_factory[i][0]))
            ].lower(),
        )

    list_f = []
    for i in range(5):
        minimum = 0
        for j in range(len(cog.list_factory)):
            if cog.list_factory[minimum][2] > cog.list_factory[j][2]:
                minimum = j
        cog.list_factory[minimum][2] = 100
        list_f.append(
            discord.app_commands.Choice(
                name=f"{cog.list_factory[minimum][0]} ({defs.ICON_ID[cog.list_factory[minimum][3]]})",
                value=json.dumps(cog.list_factory[minimum]),
            )
        )

    return list_f


def check_expiry(expiry):
    dict = {}

    if (
        len(expiry) == 8
        and expiry[0:1].isdigit()
        and expiry[3:4].isdigit()
        and expiry[6:7].isdigit()
        and expiry[2] == ":"
        and expiry[5] == ":"
    ):
        d = int(expiry[0:2])
        h = int(expiry[3:5])
        m = int(expiry[6:8])
    elif (
        len(expiry) == 5
        and expiry[0:1].isdigit()
        and expiry[3:4].isdigit()
        and expiry[2] == ":"
    ):
        d = 0
        h = int(expiry[0:2])
        m = int(expiry[3:5])
    elif len(expiry) == 2 and expiry[0:1].isdigit():
        d = 0
        h = 0
        m = int(expiry[0:2])
    else:
        return (False, dict)

    if d >= 0 and h >= 0 and m >= 0 and h <= 60 and m <= 60:
        delta = datetime.timedelta(days=d, hours=h, minutes=m)
        expiry = datetime.datetime.now() + delta
        dict = {"d": expiry.day, "h": expiry.hour, "m": expiry.minute}
        return (True, dict)
    else:
        return (False, dict)


async def list_depots(interaction: discord.Interaction, current: str):
    l = []
    data = utils.read(defs.DB["database"])
    for i in range(len(data["depots"])):
        l.append(
            discord.app_commands.Choice(
                name=f"{data['depots'][i]['name']} a {data['depots'][i]['location']}({data['depots'][i]['map']})",
                value=i,
            )
        )
    return l


class CommandsCog(discord.ext.commands.Cog):
    def __init__(self, client: main.MyBot):
        self.client = client
        self.list_locations = None#self.create_list_locations()
        self.list_factory = None#self.create_list_factory()
        self.rules = moderation.loadRules() #TODO togli
        client.tree.add_command(
            discord.app_commands.ContextMenu(
                name="Report Message",
                callback=self.report,  # set the callback of the context menu to "my_cool_context_menu"
            )
        )
        logging.basicConfig(
            filename="logging.log",
            format="%(asctime)s [%(levelname)s]:%(name)s:%(message)s",
            level=logging.INFO,
        )
                

    def create_list_locations(self):
        list = []
        for map in defs.MAP_NAME:
            data = utils.read(defs.DB["mapData"].format(map))
            for i in range(len(data["mapItems"])):
                if data["mapItems"][i]["iconType"] in [33, 52]:
                    min = 0
                    index = -1
                    for j in range(len(data["mapTextItems"])):
                        if data["mapTextItems"][j]["mapMarkerType"] == "Major":
                            d = math.sqrt(
                                (
                                    data["mapItems"][i]["x"]
                                    - data["mapTextItems"][j]["x"]
                                )
                                ** 2
                                + (
                                    data["mapItems"][i]["y"]
                                    - data["mapTextItems"][j]["y"]
                                )
                                ** 2
                            )
                            if min > d or index == -1:
                                min = d
                                index = j
                    if index != -1:
                        icon = data["mapItems"][i]["iconType"]
                        list.append(
                            [
                                data["mapTextItems"][index]["text"],
                                map,
                                0,
                                icon,
                                (data["mapItems"][i]["x"], data["mapItems"][i]["y"]),
                            ]
                        )
        return list

    def create_list_factory(self):
        list = []

        for map in defs.MAP_NAME:
            data = utils.read(defs.DB["mapData"].format(map))
            for i in range(len(data["mapItems"])):
                if data["mapItems"][i]["iconType"] in [17, 34, 51]:
                    min = 0
                    index = -1
                    for j in range(len(data["mapTextItems"])):
                        if data["mapTextItems"][j]["mapMarkerType"] == "Major":
                            d = math.sqrt(
                                (
                                    data["mapItems"][i]["x"]
                                    - data["mapTextItems"][j]["x"]
                                )
                                ** 2
                                + (
                                    data["mapItems"][i]["y"]
                                    - data["mapTextItems"][j]["y"]
                                )
                                ** 2
                            )
                            if min > d or index == -1:
                                min = d
                                index = j
                    if index != -1:
                        icon = data["mapItems"][i]["iconType"]
                        list.append(
                            [
                                data["mapTextItems"][index]["text"],
                                map,
                                0,
                                icon,
                                (data["mapItems"][i]["x"], data["mapItems"][i]["y"]),
                            ]
                        )

        return list

    @discord.app_commands.command(
        name="event_filter",
        description="Filtra gli eventi per regione",
    )
    async def filter(self, interaction: discord.Interaction):
        logging.info(f'"\\event_filter" used by {interaction.user.name}')

        if interaction.user.id in defs.DB["permission"]:
            data = utils.read(defs.DB["database"])
            view = views.EventFilterView(self.client, data)
            await interaction.response.send_message(
                "Seleziona le regioni di interesse:", view=view, ephemeral=True
            )
            regions = await view.wait()
            with open(defs.DB["mapName"], "w") as f:
                utils.write(defs.DB["mapName"], regions)
                str = "Regioni di interesse:\n" + regions[0]
                for i in range(1, len(regions)):
                    str += ", " + regions[i]
                data["map_filter"] = regions
                utils.write(defs.DB["database"], data)
                await self.client.eventChannel.edit(topic=str)
                await interaction.delete_original_response()
                await interaction.followup.send(str, ephemeral=True)

    @discord.app_commands.command(
        name="depot_add",
        description="Aggiungi i dati di un deposito",
    )
    @discord.app_commands.describe(location="Inserisci la posizione del deposito")
    @discord.app_commands.autocomplete(location=location_autocomplete)
    async def depot_add(self, interaction: discord.Interaction, location: str):
        logging.info(f'"\\depot_add" used by {interaction.user.name}')

        modal = views.DepotModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        data = utils.read(defs.DB["database"])
        location = json.loads(location)
        data["depots"].append(
            {
                "group": "Altro" if modal.group.value == "" else modal.group.value,
                "iconType": location[3],
                "location": location[0],
                "map": location[1],
                "x": location[4][0],
                "y": location[4][1],
                "name": modal.name.value,
                "passcode": modal.passcode.value,
                "desc": modal.desc.value,
            }
        )
        depots = data["depots"]

        embed, view = views.view_depots(depots[0]["group"], depots)

        await self.client.depotChannel.send(file=embed.fileMap, embed=embed, view=view)
        await modal.interaction.delete_original_response()
        await interaction.followup.send(
            f"Deposito a {location[0]} aggiunto", ephemeral=True
        )
        # await client.depotChannel.send(embed=embed)

        async for msg in self.client.depotChannel.history(limit=100):
            if msg.id == data["depotListMsg"]:
                await msg.delete()
        data["depotListMsg"] = self.client.depotChannel.last_message_id

        utils.write(defs.DB["database"], data)

    @discord.app_commands.command(
        name="depot_remove",
        description="Elimina un deposito",
    )
    @discord.app_commands.describe(depot="Seleziona un deposito da eliminare")
    @discord.app_commands.autocomplete(depot=list_depots)
    async def depot_remove(self, interaction: discord.Interaction, depot: int):
        logging.info(f'"\\depot_remove" used by {interaction.user.name}')

        data = utils.read(defs.DB["database"])
        loc = data["depots"][depot]["location"]
        data["depots"].remove(data["depots"][depot])
        depots = data["depots"]

        await interaction.response.defer(thinking=True, ephemeral=True)

        if len(depots) > 0:
            embed, view = views.view_depots(depots[0]["group"], depots)

            await self.client.depotChannel.send(
                file=embed.fileMap, embed=embed, view=view
            )
        await interaction.followup.send(f"Deposito a {loc} rimosso", ephemeral=True)
        # await client.depotChannel.send(embed=embed)

        async for msg in self.client.depotChannel.history(limit=100):
            if msg.id == data["depotListMsg"]:
                await msg.delete()
        if len(depots) > 0:
            data["depotListMsg"] = self.client.depotChannel.last_message_id

        utils.write(defs.DB["database"], data)

    @discord.app_commands.command(
        name="logi_reminder", description="Imposta un sveglia pubblica"
    )
    @discord.app_commands.describe(location="Inserisci la posizione della fabbrica")
    @discord.app_commands.autocomplete(location=factory_autocomplete)
    async def reminder(self, interaction: discord.Interaction, location: str):
        logging.info(f'"\\logi_reminder" used by {interaction.user.name}')

        modal = views.ReminderModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        data = utils.read(defs.DB["database"])
        location = json.loads(location)

        cond, time = check_expiry(modal.expiry.value)

        if not cond:
            await modal.interaction.delete_original_response()
            await interaction.followup.send(f"Format scadenza errato!", ephemeral=True)
        else:
            data["reminders"][modal.name.value + "".join(time) + location[0]] = {
                "author": interaction.user.id,
                "iconType": location[3],
                "location": location[0],
                "map": location[1],
                "x": location[4][0],
                "y": location[4][1],
                "item": modal.name.value,
                "quantity": modal.quantity.value,
                "expiry": time,
                "desc": modal.desc.value,
                "pickedUp": None,
                "last_reminder": {},
            }
            reminder = data["reminders"][modal.name.value + "".join(time) + location[0]]

            embed, view = views.view_reminder(reminder, interaction.user)

            await self.client.reminderChannel.send(
                file=embed.fileMap, embed=embed, view=view
            )
            await modal.interaction.delete_original_response()
            # await client.depotChannel.send(embed=embed)

            utils.write(defs.DB["database"], data)

    @discord.app_commands.command(
        name="issue_warning",
        description="Warns a user of a violation",
    )
    @discord.app_commands.describe(user="The user that you want to warn")
    @discord.app_commands.describe(rule="The rule violated (ex. G.1.4)")
    @discord.app_commands.check(permissions.reset)
    @discord.app_commands.autocomplete(rule=rules_autocomplete)
    async def issue_warning(self, interaction: discord.Interaction, user: discord.Member,  rule: str):
        modal = views.ViolationModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        await self.client.sendWarning(user, rule, [interaction.user], modal.notes.value, modal.link.value)
        #TODO non va
        moderation.addToHistory("ciao", user, rule, modal.link, modal.notes)
        
        await modal.interaction.delete_original_response()

        await interaction.followup.send("Warning sent", ephemeral=True)

    @discord.app_commands.command(
        name="add_swear_word",
        description="Adds a a word that it is considered to violate the rules.",
    )
    @discord.app_commands.describe(swear_word="The word you want to add")
    @discord.app_commands.check(permissions.reset)
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
        name="reset",
        description="Resets the bot. Use it if there is a bug or it stopped working",
    )
    @discord.app_commands.check(permissions.reset)
    async def reset(self, interaction: discord.Interaction):
        logging.info(f'"\\reset" used by {interaction.user.name}')
        # TODO finisci
        await self.client.change_presence(status=discord.Status.offline)

        main.reconnect(self.client)


    async def report(self, interaction: discord.Interaction, message: discord.Message):
        logging.info(f'"\\report" used by {interaction.user.name}')

        await interaction.response.send_message("reportato")

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
