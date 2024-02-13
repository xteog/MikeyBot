import discord
import role_assign.objects as objects
import config


class RoleAssignView(discord.ui.View):
    def __init__(self, bot, data: objects.RoleAssignData):
        super().__init__(timeout=None)
        self.bot = bot
        self.data = data

        self.embed = discord.Embed(title="Role Assign", description=self.data.text)

        for button in self.data.getButtons(self):
            self.add_item(button)


class RoleButton(discord.ui.Button):
    def __init__(self, role: int, label: str, view: RoleAssignView):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=f"roleassign_{view.id}_{role}",
        )
        self.role = role

    async def callback(self, interaction: discord.Interaction) -> None:
        role = interaction.guild.get_role(self.role)

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(
                f"{role.mention} removed", ephemeral=True
            )
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                f"{role.mention} added", ephemeral=True
            )


class RoleAssignEditView(discord.ui.View):
    def __init__(self, bot, data: objects.RoleAssignData):
        super().__init__(timeout=config.defaultTimeout)
        self.bot = bot
        self.data = data

        self.embed = discord.Embed(title="Role Assign Edit", description=self.data.text)

        self.add_item(TextEditButton(self))

        for button in self.data.getEditButtons(self):
            self.add_item(button)

        self.add_item(AddButton(self))
        self.add_item(RemoveButton(self))
        self.add_item(ConfirmButton(self))


class RoleEditButton(discord.ui.Button):
    def __init__(self, role: int, label: str, view: RoleAssignEditView):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=1)
        self.role = role
        self.label = label
        self._view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        modal = EditButtonModal(self.role, self.label)
        await interaction.response.send_modal(modal)
        await modal.wait()

        guild = await self.view.bot.fetch_guild(config.serverId)

        found = False

        try:
            for role in guild.roles:
                if role.id == int(modal.role.value):
                    found = True
        except Exception as e:
            found = False

        if not found:
            await modal.interaction.edit_original_response(content="Role id not valid")
            return

        edited = self._view.data.editButton(
            oldRole=self.role,
            oldLabel=self.label,
            newRole=int(modal.role.value),
            newLabel=modal.label.value,
        )

        if edited:
            newView = RoleAssignEditView(self._view.bot, self._view.data)
            await interaction.followup.edit_message(
                interaction.message.id, view=newView, embed=newView.embed
            )

            await modal.interaction.edit_original_response(content="Button updated")
        else:
            await modal.interaction.edit_original_response(
                content="This button already exists"
            )


class AddButton(discord.ui.Button):
    def __init__(self, view: RoleAssignEditView):
        super().__init__(
            label="Add Button +",
            style=discord.ButtonStyle.green,
            row=4,
        )
        self._view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        added = self._view.data.addButton(role=None, label="No label")

        if added:
            newView = RoleAssignEditView(self._view.bot, self._view.data)
            await interaction.response.edit_message(view=newView, embed=newView.embed)
        else:
            await interaction.response.send_message(
                "Before adding new buttons assign a role to the new one", ephemeral=True
            )


class RemoveButton(discord.ui.Button):
    def __init__(self, view: RoleAssignEditView):
        super().__init__(
            label="Remove Button -",
            style=discord.ButtonStyle.danger,
            row=4,
        )
        self._view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        removed = self._view.data.removeButton()

        if removed:
            newView = RoleAssignEditView(self._view.bot, self._view.data)
            await interaction.response.edit_message(view=newView, embed=newView.embed)
        else:
            await interaction.response.send_message(
                "No buttons left to remove u moron", ephemeral=True
            )


class TextEditButton(discord.ui.Button):
    def __init__(self, view: RoleAssignEditView):
        super().__init__(label="Edit Text", style=discord.ButtonStyle.secondary, row=0)
        self.text = view.data.text
        self._view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        modal = EditTextModal(self.text)
        await interaction.response.send_modal(modal)
        await modal.wait()

        self._view.data.text = modal.text.value

        newView = RoleAssignEditView(self._view.bot, self._view.data)
        await interaction.followup.edit_message(
            interaction.message.id, view=newView, embed=newView.embed
        )
        await modal.interaction.edit_original_response(content="Text updated")


class ConfirmButton(discord.ui.Button):
    def __init__(self, view: RoleAssignEditView):
        super().__init__(
            label="Confirm",
            style=discord.ButtonStyle.blurple,
            row=4,
        )

        self._view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        newView = RoleAssignView(self._view.bot, self._view.data)

        channel = newView.bot.get_channel(self._view.data.channelId)
        if self._view.data.messageId == None:
            msg = await channel.send(view=newView, embed=newView.embed)

            self._view.data.messageId = msg.id
            self._view.data.save()

            await interaction.response.send_message("Embed created", ephemeral=True)
        else:
            self._view.data.save()
            message = await channel.fetch_message(self._view.data.messageId)
            await message.edit(view=newView, embed=newView.embed)
            await interaction.response.send_message("Embed updated", ephemeral=True)


class EditButtonModal(discord.ui.Modal, title="Edit Button"):
    def __init__(self, role, label):
        super().__init__()

        self.role = discord.ui.TextInput(
            label="Role Id",
            required=True,
            placeholder="ex. 1057016848761225327",
            default=role,
            style=discord.TextStyle.short,
        )
        self.label = discord.ui.TextInput(
            label="Label",
            required=True,
            default=label,
            style=discord.TextStyle.short,
        )

        self.add_item(self.role)
        self.add_item(self.label)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        self.interaction = interaction
        self.stop()


class EditTextModal(discord.ui.Modal, title="Edit Text"):
    def __init__(self, text):
        super().__init__()

        self.text = discord.ui.TextInput(
            label="Role Assign Text",
            required=True,
            default=text,
            style=discord.TextStyle.paragraph,
        )

        self.add_item(self.text)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        self.interaction = interaction
        self.stop()
