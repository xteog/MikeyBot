import codecs
import logging
import socket
import discord
import datetime
import lobby

class LobbiesList():
    def __init__(self, id, client, channelId, platform):
        self.id = id
        self.client = client
        self.channelId = channelId
        self.lobbies = {}
        self.view = LobbiesView(id, client, self.lobbies)
        self.platform = platform
        client.add_view(self.view)

    async def ping(self):
        channel = self.client.get_channel(self.channelId)

        async for msg in channel.history(limit=100):
            if msg.author == self.client.user:
                await msg.delete()

        await channel.send(view=self.view, embed=self.view.embed)

    async def update(self):
        channel = self.client.get_channel(self.channelId)
        self.lobbies = getLobbiesList(self.platform)

        if self.lobbies == None:
            return

        self.view = LobbiesView(self.id, self.client, self.lobbies)

        oldMessage = None
        async for message in channel.history(limit=100):
            if message.author.id == self.client.user.id:
                if oldMessage == None:
                    oldMessage = message
                else:
                    await message.delete()

        if oldMessage == None:
            await channel.send(view=self.view, embed=self.view.embed)
        else:
            await oldMessage.edit(view=self.view, embed=self.view.embed)

class LobbiesView(discord.ui.View):
    def __init__(self, id, client, lobbies: dict):
        super().__init__(timeout=None)
        self.id = id
        self.client = client
        self.embed = LobbiesEmbed(lobbies=lobbies)

    @discord.ui.button(label="↻", style=discord.ButtonStyle.gray, custom_id="refresh", disabled=True)
    async def refresh(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        logging.info(interaction.user.display_name + " used refresh")
        await self.client.lobbiesLists[self.id].update()
        await interaction.response.send_message("Lobby list updated", ephemeral=True)


class LobbiesEmbed(discord.Embed):
    def __init__(self, lobbies: dict):
        super().__init__(colour=0x00B0F4, title="Lobbies online")

        self.set_footer(text="Last update")
        self.timestamp = datetime.datetime.utcnow()

        if len(lobbies) == 0:
            self.description = "No lobbies found"
            return

        for lobby in lobbies:
            if lobby["private"]:
                name = ":lock: " + f'**{lobby["name"]}**'
            else:
                name = f'**{lobby["name"]}**'

            if lobby["status"] == "Lobby":
                value = f'**Capacity:** {lobby["curr_players"]}/{lobby["max_players"]}\n**Status:** {lobby["status"]}'
            else:
                value = f'**Capacity:** {lobby["curr_players"]}/{lobby["max_players"]}\n**Status:** {lobby["status"]} {lobby["curr_laps"]}/{lobby["max_laps"]} Laps'

            self.add_field(
                name=name,
                value=value,
                inline=True,
            )


def getMessageParameter(data: str, n: int) -> str:
    """
    Gets a specific parameter from a payload.

    Parameters
    -----------
    - data : `str`\n
        The payload as a string.
    - n : `int`
        In which position the parameter appears in the payload.

    Returns
    ----------
    `str`
        The parameter fetched.
    """

    start, end, cont = 0, 0, 0
    for i in range(len(data)):
        if data[i] == "|":
            if start == 0:
                cont += 1
            else:
                end = i
                break

        if data[i] == "|" and cont == n:
            start = i + 1

    return data[start:end]


def getLobbyInfo(data: str) -> dict:
    """
    This is a reST style.

    :param str: this is a first param
    :returns: this is a description of what is returned
    """
    start, end = 0, 0
    for i in range(len(data)):
        if data[i] == "#":
            start = i + 1
        if data[i] == "|":
            end = i
            break
    lobbyName = data[start:end]

    try:
        platform = getMessageParameter(data, 2).split("#")[-1]
        cross_play = getMessageParameter(data, 2).split("#")[-2]
    except:
        platform = None
        cross_play = None

    max_players = getMessageParameter(data, 3)
    players = getMessageParameter(data, 9)
    status = getMessageParameter(data, 7)
    curr_laps = getMessageParameter(data, 5)
    max_laps = getMessageParameter(data, 6)
    password = getMessageParameter(data, 10)
    ack = getMessageParameter(data, 15)

    if lobbyName != "*0":
        return {
            "name": lobbyName,
            "platform": platform,
            "cross_play": True if cross_play == "on" else False,
            "curr_players": players,
            "max_players": max_players,
            "status": status,
            "curr_laps": curr_laps,
            "max_laps": max_laps,
            "private": password != ""
        }, ack
    else:
        return None, ack

def sendAck(sock, addr, ack) -> None:
    response = f"61636b0a00320a00{ack.encode('ascii').hex()}0a00"
    sock.sendto(bytes.fromhex(response), addr)

def getLobbiesList(platform) -> list | None:
    lobbies = []
    PORT = 6510
    payload = "39300a00310a00300a00"

    EU = "64.226.118.45"
    NA = "138.197.70.132"
    AS = "159.223.89.233"

    EU_ON = False
    NA_ON = False
    AS_ON = False

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", PORT))

    data = codecs.decode(payload, "hex_codec")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.sendto(data, (EU, PORT))
    sock.sendto(data, (NA, PORT))
    sock.sendto(data, (AS, PORT))

    run = True
    sock.settimeout(2)
    while run:
        try:
            data, addr = sock.recvfrom(2048)
            data = data.decode()

            if addr[0] == EU:
                EU_ON = True
            elif addr[0] == NA:
                NA_ON = True
            elif addr[0] == AS:
                AS_ON = True
    
            if data.find("*0") != -1:
                lobby, ack = getLobbyInfo(data)
                if lobby != None and (lobby["platform"] == platform or lobby["cross_play"]):
                    lobbies.append(lobby)

                sendAck(sock, addr, ack)
        except Exception as e:
            run = False

    sock.close()

    """
    if not (EU_ON and NA_ON and AS_ON):
        return None
    """

    return lobbies
