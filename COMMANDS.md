# 📋 Command List
This is a list of all **Commie** commands, a description, and their usage.

By default commands are slash commands, and use `!`. You can customize this using `/setprefix`.

**Command Count:** `94`

## ⚖️ Roles

The "role required" in the tables below shows the lowest role required to ***use*** the command, for example, if it lists "Member" as the **Role Required**, then everyone with "Member" role and above (Helpers, Moderators and Admins) can use the role.

| Role Name |
|-----------|
| Admin     |
| Moderator |
| Helper    |
| Member    |

## 📌 General
Command | Description | Usage | Role Required
--- | --- | --- | ---
help | Public help menu displaying commands | `help` | Member
info | Shows information about **Commie** and your server | `info` | Member
about | Shows more information about **Commie** | `about` | Member
setup | Shows a user how to setup **Commie** | `setup` | Moderator
donate | Sends **Commie's** donation link | `donate` | Member
vote | Sends **Commie's** voting links | `vote` | Member
test | Tests if the bot is up | `test` | Member
ping | Shows a users ping | `ping` | Member
suggest | Lets users make a suggestion for the server | `suggest <suggestion>` | Member
poll | Creates a poll | `poll <question> <option1> <option2> <option3> <option4> <option5>` | Moderator

## 🎉 Fun
Command | Description | Usage | Role Required
--- | --- | --- | ---
coinflip | Flips a coin | `coinflip` | Member
ask | Gives an answer to your question | `ask` | Member
reverse | Reverses a users text | `reverse <text>` | Member
say | Says the users input text | `say <text>` | Member
lovetest | Gives a love percentage between two users | `lovetest <user1> <user2>` | Member
cute | Sends a picture of a cute animal | `cute` | Member

## 🎯 Action
Command | Description | Usage | Role Required
--- | --- | --- | ---
highfive | Highfives another user | `highfive @user` | Member
poke | Pokes another user | `poke @user` | Member
pat | Pats another user | `pat @user` | Member
hug | Hugs another user | `hug @user` | Member
kiss | Kisses another user | `kiss @user` | Member
cuddle | Cuddles another user | `cuddle @user` | Member
bite | Bites another user | `bite @user` | Member
bonk | Bonks another user | `bonk @user` | Member
slap | Slaps another user | `slap @user` | Member
punch | Punches another user | `punch @user` | Member
throw | Throws another user off a cliff | `throw @user` | Member
punt | Punts another user | `punt @user` | Member

## 🧮 Misc
Command | Description | Usage | Role Required
--- | --- | --- | ---
whois | Sends information about a user's account | `whois @user` | Member
snipe | Shows a recently deleted message and who sent it | `snipe` | Member
remind | Sets a reminder for a user about a task | `remind <number><abbreviated time length> <task>` | Member
remindlist | Shows a users reminder list | `remindlist` | Member
afk | Sets a user into "AFK Mode" | `afk <message>` | Member
climateclock | Shows the [ClimateClock](https://climateclock.world) countdown | `climateclock` | Member
card | Shows a user's user card | `card @user` | Member
cardnickname | Sets a user's nickname on their user card | `cardnickname <nickname>` | Member
cardbio | Sets a user's bio on their user card | `cardbio <bio>` | Member
cardage | Sets a user's age on their user card | `cardage <age>` | Member
cardpronouns | Sets a user's pronouns on their user card | `cardpronouns <pronouns>` | Member
cardbirthday | Sets a user's birthday on their user card | `cardbirthday <month> <day> <year>` | Member
cardideology | Sets a user's ideology on their user card | `cardideology <ideology>` | Member
cardcolor | Sets a user's user card embed color | `cardcolor <choice>` | Member
cardcolorchoices | Shows the color choices for user cards | `cardcolorchoices` | Member
todoadd | Adds a task to a user's "todo list" | `todoadd <task>` | Member
tododel | Removes a task from a user's "todo list" | `tdoodel <task number>` | Member
todolist | Shows a user's "todo list" | `todolist` | Member
todoclear | Clears a user's "todo list" | `todoclear` | Member
giveaway | Starts a giveaway | `giveaway <time> <winners> <prize>` | Moderator
reroll | Rerolls the giveaway | `reroll` | Moderator
emojisteal | Grabs and sends the file link from a custom emoji | `emojisteal :emoji:` | Member
emojiadd | Adds an emoji to the server | `emojiadd <name>` | Admin
emojidel | Deletes an emoji from the server | `emojidel <name> <id>` | Admin
emojiinfo | Sends information about an emoji | `emojiinfo <name> <id>` | Member
emojirename | Renames an emoji | `emojirename <id> <new_name>` | Admin
stickeradd | Adds a sticker to the server | `stickeradd` | Admin
stickerdel | Deletes a sticker from the server | `stickerdel <name> <id>` | Admin
stickerinfo | Shows information about a sticker | `stickerinfo <name> <id>` | Member
stickerrename | Renames a sticker | `stickerrename <id> <new_name>` | Admin

## 🔰 Staff
Command | Description | Usage | Role Required
--- | --- | --- | ---
purge | Mass deletes messages | `purge <number of messages>` | Admin
ban | Bans a user from the server | `ban @user` | Moderator
unban | Unbans a user from the server | `unban @user` | Admin
kick | Kicks a user from the server | `kick @user` | Helper
gulag | Puts a user in "timeout" | `gulag @user <number><abbreviated time length> <reason>` | Helper
warn | Warns a user | `warn @user <reason>` | Helper
warnlist | Checks the warns of a user | `warnlist @user` | Helper
delwarn | Deletes a specified warn from a users warn list | `delwarn @user <warn number>` | Admin
clearwarns | Clears all a user's warns | `clearwarns @user` | Admin
highlighthelp | Sends the Highlight Help Menu | `highlighthelp` | Helper
higlightshow | Shows a user's highlight menu | `highlightshow` | Helper
highlightadd | Adds a word to a moderator's highlight list | `highlightadd <word>` | Helper
hightlightremove | Removes a word from a moderator's highlight list | `highlightremove <word>` | Helper
highlightclear | Clears a moderator's word highlight list | `highlightclear` | Helper
highlightblock | Blocks a user or channel on a moderator's highlight list | `highlightblock @user` / `highlightblock #channel` | Helper
highllightunblock | Unblocks a user or channel from a moderator's highlight list | `highlightunblock @user` / `highlightunblock #channel` | Helper
defaulthighlights | Adds a default list of slurs to a moderator's highlight list | `defaulthighlights` | Helper
highlightignore | Adds a word to a moderator's ignore list | `highlightignore <word>` | Helper
highlightunignore | Removes a word from a moderator's ignore list | `highlightunignore <word>` | Helper

## ⚙️ Config
Command | Description | Usage | Role Required
--- | --- | --- | ---
configs | Sends the Config Menu for a server | `configs` | Admin
togglelog | Toggles the logging feature for a server | `togglelog` | Admin
togglesuggest | Toggles the suggestion feature for a server | `togglesuggest` | Admin
togglestar | Toggles the starboard feature for a server | `togglestar` | Admin
togglewelcome | Toggles the welcome message feature for a server | `togglewelcome` | Admin
toggleleave | Toggles the leave message feature for a server | `toggleleave` | Admin
toggleboost | Toggles the boost message feature for a server | `toggleboost` | Admin
setprefix | Sets server prefix | `setprefix <prefix>` | Admin
setlog | Sets server logging channel | `setlog <channel mention>` | Admin
setstaff | Sets the staff roles for a server | `setstaff` | Admin
setsuggest | Sets server suggestion channel | `setsuggest <channel mention>` | Admin
setstar | Sets server starboard channel | `setstar <channel mention>` | Admin
setwelcome | Sets the welcome message for a server | `setwelcome` | Admin
setleave | Sets the leave message for a server | `setleave` | Admin
setboost | Sets the boost message for a server | `setboost` | Admin
testwelcome | Sends the welcome message for a server | `testwelcome` | Admin
testleave | Sends the leave message for a server | `testleave` | Admin
testboost | Sends the boost embed for a server | `testboost` Admin
