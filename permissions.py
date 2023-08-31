import discord

fia_id = 1144694517455396984

def reset(interaction : discord.Interaction):
    for role in interaction.user.roles:
        if role.id == fia_id:
            return True
    return False