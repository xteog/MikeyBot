import role_assign.views as views
import discord
import utils
import config


class RoleAssignData:
    def __init__(self, id: int, channelId: int, text: str) -> None:
        self.id = id
        self.text = text
        self.buttons = []
        self.messageId = None
        self.channelId = channelId

    def addButton(self, role: int, label: str) -> bool:
        found = False
        for button in self.buttons:
            if button["role"] == role:
                found = True

        if not found:
            self.buttons.append({"role": role, "label": label})
            return True

        return False

    def removeButton(self) -> bool:
        length = len(self.buttons)

        if length > 0:
            self.buttons.pop(length - 1)
            return True

        return False

    def editButton(
        self, oldRole: int, oldLabel: str, newRole: int, newLabel: str
    ) -> bool:
        found = False
        for button in self.buttons:
            if button["role"] == newRole and button["label"] == newLabel:
                found = True

        if found:
            return False

        for button in self.buttons:
            if button["role"] == oldRole and button["label"] == oldLabel:
                button["role"] = newRole
                button["label"] = newLabel

        return True

    def getButtons(self, view) -> list[discord.ui.Button]:
        uiButtons = []

        for button in self.buttons:
            uiButtons.append(views.RoleButton(button["role"], button["label"], view))

        return uiButtons

    def getEditButtons(self, view) -> list[discord.ui.Button]:
        uiButtons = []

        for button in self.buttons:
            uiButtons.append(
                views.RoleEditButton(button["role"], button["label"], view)
            )

        return uiButtons

    def save(self) -> None:
        dict = utils.read(config.roleAssignPath)

        if dict == None:
            dict = []

        for i in range(len(dict)):
            if dict[i]["id"] == self.id:
                dict.pop(i)

        dict.append(
            {
                "id": self.id,
                "message_id": self.messageId,
                "channel_id": self.channelId,
                "text": self.text,
                "buttons": self.buttons,
            }
        )

        utils.write(config.roleAssignPath, dict)


def loadData(messageId: int) -> RoleAssignData:
    dict = utils.read(config.roleAssignPath)

    if dict == None:
        return None

    for i in range(len(dict)):
        if dict[i]["message_id"] == messageId:
            data = RoleAssignData(dict[i]["id"], dict[i]["channel_id"], dict[i]["text"])
            data["message_id"] = messageId
            
            for button in data.buttons:
                data.addButton(button["role"], button["label"])

            return data

    return None
