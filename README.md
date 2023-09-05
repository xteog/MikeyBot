# Mikey Discord Bot
This is a discord bot with two main reasons:
- Message Moderation
- Users Verification
## Moderation
### Automatic moderation
The bot will automaticaly detect swear words by the messages sent and report them in a designed private channel for moderation
The bot will give the moderators 3 choises:
- `It isn't a swear word`: in this case the bot will remove the word from the ones detected.
- `Delete Message`: deletes the offender message.
- `Warn`: It will send a private warning to the user to warn him.

If the bot doesn't detect a swear word you can add a word to the list of words detected using the comand `\add_swear_word`

### Manual moderation
If the bot doesn't detect a offence or infringement of the rules, you can use the comand `\issue_warning`
