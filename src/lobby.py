import codecs
import logging
import socket
import discord
import datetime
import lobby


class LobbiesView(discord.ui.View):
    def __init__(self, client, lobbies: dict):
        super().__init__(timeout=None)

        self.client = client
        self.embed = LobbiesEmbed(lobbies=lobbies)

    @discord.ui.button(label="↻", style=discord.ButtonStyle.gray, custom_id="refresh")
    async def refresh(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        logging.info(interaction.user.display_name + " used refresh")
        lobbies = lobby.getLobbiesList()
        view = LobbiesView(self.client, lobbies)

        if len(self.client.lobbies) != len(lobbies):
            await interaction.response.send_message("Lobby list updated", ephemeral=True)
            await interaction.message.delete()
            await self.client.lobbiesChannel.send(view=view, embed=view.embed)
        else:
            await interaction.response.edit_message(view=view, embed=view.embed)

        self.client.lobbies = lobbies

        


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

    max_players = getMessageParameter(data, 3)
    players = getMessageParameter(data, 9)
    status = getMessageParameter(data, 7)
    curr_laps = getMessageParameter(data, 5)
    max_laps = getMessageParameter(data, 6)
    password = getMessageParameter(data, 10)

    if lobbyName != "*0":
        return {
            "name": lobbyName,
            "curr_players": players,
            "max_players": max_players,
            "status": status,
            "curr_laps": curr_laps,
            "max_laps": max_laps,
            "private": password != "",
        }
    else:
        return None


def getLobbiesList() -> list | None:
    lobbies = []
    PORT = 6510
    payload = "39300a300a2d310a"

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
            data, addr = sock.recvfrom(1024)
            data = data.decode()

            if addr[0] == EU:
                EU_ON = True
            elif addr[0] == NA:
                NA_ON = True
            elif addr[0] == AS:
                AS_ON = True
    
            if data.find("*00server") != -1:
                lobby = getLobbyInfo(data)
                if lobby != None:
                    lobbies.append(lobby)
        except:
            run = False

    sock.close()

    if not (EU_ON and NA_ON and AS_ON):
        return None

    return lobbies
