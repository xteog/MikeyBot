# Mikey: A Discord Bot
This is a Discord bot that serves two primary functions:

- **Message Moderation**
- **User Verification** (demo)

## Message Moderation
### Automatic Moderation
Mikey will automatically detect swear words in messages and report them in a designated private moderation channel. 

![Automatic Moderation Screenshot](https://github.com/xteog/MikeyBot/assets/72068040/2883a52d-ef39-41f5-b655-617f96a46eb2)

Moderators will have three options:

- **`It isn't a swear word`**: Selecting this option will prevent Mikey from flagging that word as offensive in the future.
- **`Delete Message`**: This choice deletes the offending message.
- **`Warn`**: Mikey sends a private message to the user to issue a warning.

If no one interacts with the warning within 1 hour, the message will be considered as not offensive. If Mikey doesn't detect a swear word, you can manually add it to the list of detected words using the command `\add_swear_word`.

### Manual Moderation
In cases where Mikey doesn't detect an offense or a violation of the rules, you can use the command `\issue_warning`.

![Manual Moderation Screenshot](https://github.com/xteog/MikeyBot/assets/72068040/d60d8489-d22d-46a4-82e4-6b6d67d96c16)

After choosing the offender, select the rule that was violated by searching from the options provided. Then, you will be asked to insert a link or a reason as proof, which will be shown to the user.

### Appeals
If a user receives a warning, they can choose to appeal within 24 hours. If so, the user will interact with the warning and Mikey will ask for the reason of the appeal.
Designated members will receive the appeal request, which will need to be accepted by 3 members.

![Appeal Screenshot](https://github.com/xteog/MikeyBot/assets/72068040/fa972495-3bfe-4105-b0a6-983f562416f3)

### Violation History
To review past violations, you can use the `\search_violation` command. This command has two parameters, but you should choose only one of them:

- **Search by User**: Select a user, and the command will return a list of all their past violations.

![Search by User Screenshot](https://github.com/xteog/MikeyBot/assets/72068040/cb0c7473-5212-48c9-bf20-af3483a442d4)

- **Search by ID**: If you want to find a specific violation with all its details, opt for this choice.

## User Verification
If a user needs to verify their identity using their Steam ID or check their connection, they can choose one of the options in this message that will be posted in a dedicated channel.

![User Verification Screenshot](https://github.com/xteog/MikeyBot/assets/72068040/791d911c-ffba-4c20-b040-622d1d01f04e)

After interacting, they will be presented with all the instructions to complete the relative verification. When the user sends the proof for the verification, the designated members will proceed to check if they are eligible for verification. In this case, they will interact with the button shown below. The bot will automatically add the relevant roles to the user.

![Verification Screenshot](https://github.com/xteog/MikeyBot/assets/72068040/ff501cad-4d9b-44ce-95e9-44505f7e366a)
