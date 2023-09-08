# Mikey Discord Bot
This is a Discord bot that serves two primary functions:
- **Message Moderation**
- **User Verification**

## Message Moderation
### Automatic Moderation
The bot will automatically detect swear words in messages and report them in a designated private moderation channel. 

![Screenshot 2023-09-07 165940](https://github.com/xteog/MikeyBot/assets/72068040/2883a52d-ef39-41f5-b655-617f96a46eb2)

Moderators will have three options:
- **`It isn't a swear word`**: Selecting this option will prevent the bot from flagging that word as offensive in the future.
- **`Delete Message`**: This choice deletes the offending message.
- **`Warn`**: The bot sends a private message to the user to issue a warning.

If the bot doesn't detect a swear word, you can manually add it to the list of detected words using the command `\add_swear_word`.

### Manual Moderation
In cases where the bot doesn't detect an offense or a violation of the rules, you can use the command `\issue_warning`.

![Screenshot 2023-09-07 170152](https://github.com/xteog/MikeyBot/assets/72068040/d60d8489-d22d-46a4-82e4-6b6d67d96c16)

After cosing the offender, chose the rule that he broke by searching from the ones proposed.

### Violation History

To review past violations, you can use the `\search_violation` command. This command has two parameters, but you should choose only one of them:
- **Search by ID**: If you want to find a specific violation with all its details, opt for this choice.
- **Search by User**: Select a user, and the command will return a list of all their past violations.
