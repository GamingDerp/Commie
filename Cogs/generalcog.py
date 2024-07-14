import os
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import time
import aiosqlite
import random
import asyncio

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.launch_time = datetime.utcnow()

commie_logo = "https://media.discordapp.net/attachments/1257979868784758854/1258026914816331807/CommieLogo.png?ex=66868c5d&is=66853add&hm=36c6a57e62eca6ec2954f76efc6d20add7ea2ab786380aab1f1994e55513ef05&=&format=webp&quality=lossless"
commie_color = 0xd40001
owner_id = 532706491438727169

ge = discord.Embed(color=commie_color)
ge.set_author(name="Commie Commands", icon_url=commie_logo)
ge.set_thumbnail(url=commie_logo)
ge.add_field(
    name="📌 __General Commands__",
    value=f"> `Help`, `Info`, `About`, `Setup`, `Donate`, `Vote`, `Test`, `Ping`, `Suggest`, `Poll`",
)

fe = discord.Embed(color=commie_color)
fe.set_author(name="Commie Commands", icon_url=commie_logo)
fe.set_thumbnail(url=commie_logo)
fe.add_field(
    name="🎉 __Fun Commands__",
    value=f"> `Coinflip`, `Ask`, `Reverse`, `Say`, `Lovetest`, `Cute`",
)

ae = discord.Embed(color=commie_color)
ae.set_author(name="Commie Commands", icon_url=commie_logo)
ae.set_thumbnail(url=commie_logo)
ae.add_field(
    name="🎯 __Action Commands__",
    value=f"> `Highfive`, `Poke`, `Pat`, `Hug`, `Kiss`, `Cuddle`, `Bite`, `Bonk`, `Slap`, `Punch`, `Throw`, `Punt`",
)

me = discord.Embed(color=commie_color)
me.set_author(name="Commie Commands", icon_url=commie_logo)
me.set_thumbnail(url=commie_logo)
me.add_field(
    name="🧮 __Misc Commands__",
    value=f"> `Whois`, `Snipe`, `Remind`, `RemindList` `Afk`, `ClimateClock`, `Card`, `CardNickname`, `CardBio`, `CardAge`, `CardPronouns`, `CardBirthday`, `CardIdeology`, `CardColor`, `CardColorChoices`, `Todoadd`, `Tododel`, `Todolist`, `Todoclear`, `Giveaway`, `Reroll`, `EmojiSteal`, `EmojiAdd`, `EmojiDel`, `EmojiInfo`, `EmojiRename`, `StickerSteal`, `StickerAdd`, `StickerDel`, `StickerInfo`, `StickerRename`",
)

se = discord.Embed(color=commie_color)
se.set_author(name="Commie Commands", icon_url=commie_logo)
se.set_thumbnail(url=commie_logo)
se.add_field(
    name="🔰 __Staff Commands__",
    value=f"> `Purge`, `Ban`, `Unban`, `Kick`, `Gulag`, `Warn`, `WarnList`, `DelWarn`, `ClearWarns`, `Highlightadd`, `Highlightremove`, `Highlightclear`, `Highlightblock`, `Highlightunblock`, `Defaulthighlights`, `Highlightignore`, `Highlightunignore`, `Highlighthelp`",
)

ce = discord.Embed(color=commie_color)
ce.set_author(name="Commie Commands", icon_url=commie_logo)
ce.set_thumbnail(url=commie_logo)
ce.add_field(
    name="⚙️ __Config Commands__",
    value=f"> `SetPrefix`, `SetStaff`, `SetLog`, `SetSuggest`, `SetStar`, `SetWelcome`, `SetLeave`, `SetBoost`, `SetAutoRole`, `ToggleLog`, `ToggleSuggest`, `ToggleStar`, `ToggleWelcome`, `ToggleLeave`, `ToggleBoost`, `ToggleAutoRole`, `TestWelcome`, `TestLeave`, `TestBoost`, `Configs`",
)

class Dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Commands",description="Help, Info, Test, Ping, Suggest +3 More", emoji="📌"),
            discord.SelectOption(label="Fun Commands", description="Coinflip, Ask, Reverse, Say, Lovetest +1 More", emoji="🎉"),
            discord.SelectOption(label="Action Commands", description="Highfive, Poke, Pat, Hug, Kiss +7 More", emoji="🎯"),
            discord.SelectOption(label="Misc Commands", description="Whois, Snipe Remind, Afk, ClimateClock +16 More", emoji="🧮"),
            discord.SelectOption(label="Staff Commands", description="Purge, Ban, Unban, Kick, Gulag +13 More", emoji="🔰"),
            discord.SelectOption(label="Config Commands", description="SetPrefix, SetStaff, SetLog, SetSuggest, SetStar +15 More", emoji="⚙️"),
        ]
        super().__init__(min_values=1, max_values=1, options=options)

    async def callback(self,interaction:discord.Interaction):
        if self.values[0] == "General Commands":
            await interaction.response.edit_message(embed=ge)
        if self.values[0] == "Fun Commands":
            await interaction.response.edit_message(embed=fe)
        if self.values[0] == "Action Commands":
            await interaction.response.edit_message(embed=ae)
        if self.values[0] == "Misc Commands":
            await interaction.response.edit_message(embed=me)
        if self.values[0] == "Staff Commands":
            await interaction.response.edit_message(embed=se)
        if self.values[0] == "Config Commands":
            await interaction.response.edit_message(embed=ce)   
    
class DropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(Dropdown())      
        
class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_config(self, guild_id):
        try:
            async with aiosqlite.connect("dbs/configs.db") as db:
                async with db.execute("SELECT * FROM server_configs WHERE server_id = ?", (guild_id,)) as cursor:
                    result = await cursor.fetchone()
                    if result:
                        keys = ["server_id", "prefix", "admin", "moderator", "helper", "toggle_logging", "logging_channel", "toggle_welcome", "welcome_channel", "welcome_message", "toggle_leave", "leave_channel", "leave_message", "toggle_starboard", "starboard_channel", "star_count", "toggle_suggest", "suggestion_channel", "toggle_boost", "boost_channel", "description", "boost_perk_1", "boost_perk_2", "boost_perk_3", "boost_perk_4", "boost_perk_5", "boost_perk_6", "boost_perk_7", "boost_perk_8", "boost_perk_9", "boost_perk_10"]
                        return dict(zip(keys, result))
                    else:
                        return None
        except Exception as e:
            print(e)
    
    async def has_mod_role(self, user, guild_id):
        try:
            config = await self.get_config(guild_id)
            if not config:
                return False
            admin_roles = [int(role_id) for role_id in config.get("admin", "").split(',')] if config.get("admin") else []
            moderator_roles = [int(role_id) for role_id in config.get("moderator", "").split(',')] if config.get("moderator") else []
            user_roles = [role.id for role in user.roles]
            return any(role in user_roles for role in admin_roles + moderator_roles)
        except Exception as e:
            print(e)
            return False
    
    @commands.hybrid_command(description="Sends Commie's help menu")
    async def help(self, ctx):
        e = discord.Embed(color=commie_color)
        e.set_author(name="Commie Commands", icon_url=commie_logo)
        e.set_thumbnail(url=commie_logo)
        e.add_field(
            name="✧ __Command Menus__",
            value=f"> 📌 General"
                  f"\n> 🎉 Fun"
                  f"\n> 🎯 Action"
                  f"\n> 🧮 Misc"
                  f"\n> 🔰 Staff"
                  f"\n> ⚙️ Config",
        )
        view = DropdownView()
        await ctx.send(embed=e, view=view)
        
    @commands.hybrid_command(description="Sends information about the bot")
    async def info(self, ctx):
        try:
            current_config = await self.get_config(ctx.guild.id)
            current_prefix = current_config.get('prefix', '!') if current_config else '!'
            total_lines = 72
            cog_directory = "./cogs"
            for filename in os.listdir(cog_directory):
                if filename.endswith(".py"):
                    with open(os.path.join(cog_directory, filename), "r") as file:
                        lines = file.readlines()
                        non_empty_lines = [line.strip() for line in lines if line.strip()]
                        total_lines += len(non_empty_lines)
            total_guilds = len(self.bot.guilds)
            total_members = sum(guild.member_count for guild in self.bot.guilds)
            server_member_count = len([m for m in ctx.guild.members if not m.bot])
            delta_uptime = datetime.utcnow() - bot.launch_time
            hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            days, hours = divmod(hours, 24)
            e = discord.Embed(color=commie_color)
            e.set_author(name="Commie Information", icon_url=commie_logo)
            e.set_thumbnail(url=commie_logo)
            e.add_field(
                name=f"✯ {ctx.guild.name} Info",
                value=f"> **Prefix:** {current_prefix}"
                      f"\n> **Members:** {server_member_count}",
                inline=False
            )
            e.add_field(
                name="✯ Commie Info",
                value=f"> **Commands:** [97]"
                      f"\n> **Servers:** {total_guilds}"
                      f"\n> **Comrades:** {total_members}"
                      f"\n> **Ping:** {round(self.bot.latency * 1000)}ms"
                      f"\n> **Code:** {total_lines} Lines"
                      f"\n> **Uptime:** {days}**d** {hours}**h** {minutes}**m** {seconds}**s**",
                inline=False
            )
            e.add_field(
                name="✯ Credits",
                value=f"> **Dev:** `gamingderp`",
                inline=False
            )
            e.add_field(
                name="✯ Links",
                value=f"<a:CommiePet:1258041355012149328> [Add Commie](<https://discord.com/oauth2/authorize?client_id=1258968199899381771&permissions=8&integration_type=0&scope=bot&utm_source=discordbotlist.com&utm_medium=bot_page>)"
                      f"\n<:Discord:1258040249544736972> [Support Server](https://discord.gg/t9g3Wbt9Sj)"
                      f"\n📮 [Vote for Commie](<https://discordbotlist.com/bots/commie>)"
                      f"\n💰 [Tip Commie](<https://en.liberapay.com/CommieBot/>)"
                      f"\n<:GitHub:1123773190238392504> [Commie's GitHub](<https://github.com/GamingDerp/Commie/tree/main>)",
                inline=False
            )
            await ctx.send(embed=e)
        except Exception as e:
            print(e)

    @commands.hybrid_command(description="Learn more about Commie")
    async def about(self, ctx):
        e = discord.Embed(color=commie_color)
        e.set_author(name="About Commie", icon_url=commie_logo)
        e.set_thumbnail(url=commie_logo)
        e.description = "### ❓ What does Commie do? ❓ \n> **Commie** is a multi-purpose Discord bot that makes your server more customizable! It helps with and handles features like moderation, event logging, starboard, suggestions, welcome, leave and boost messages, and has fun and action commands for everyone to enjoy! \n### 💎 How can I support Commie? 💎 \n> Since Commie has no 'premium' features, you can [**donate**](<https://en.liberapay.com/CommieBot/>), boost the [**Commie Support Server**](<https://discord.gg/t9g3Wbt9Sj>), or [**vote**](<https://discordbotlist.com/bots/commie>) for **Commie** on the linked websites (checkout the `vote` command!) You can recommend **Commie** to other users as well! *Thank you for the support!* <a:CommiePet:1258041355012149328> \n### ⚙️ What does Commie run on? ⚙️ \n> <:Python:1260446899014602822> [Python](<https://www.python.org/downloads/release/python-3124/>) 3.12.4 \n> <:DiscordPY:1260446897894719518> [Discord.py](<https://github.com/Rapptz/discord.py>) 2.4.0"
        await ctx.send(embed=e, ephemeral=True)

    @commands.hybrid_command(description="Setup Commie")
    async def setup(self, ctx):
        if not await self.has_mod_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        e = discord.Embed(color=commie_color)
        e.set_author(name="Setting up Commie", icon_url=commie_logo)
        e.set_thumbnail(url=commie_logo)
        e.description = (
            "**# 📌 How To Setup Commie 📌**\n"
            "Toggle the commands to **enable** or **disable** them, then use the `set` commands to customize them!\n"
            "### Toggle Commands\n"
            "> ⚖️ `/togglelog`\n"
            "> ⚖️ `/togglewelcome`\n"
            "> ⚖️ `/toggleleave`\n"
            "> ⚖️ `/togglestar`\n"
            "> ⚖️ `/togglesuggest`\n"
            "> ⚖️ `/toggleboost`\n"
            "### Configuration Commands\n"
            "> 🔔 **Set the bot prefix:** `/setprefix [prefix]` (Default is `!`)\n"
            "> 🔰 **Set staff roles:** `/setstaff`\n"
            "> 🗃 **Configure logging:** `/setlog`\n"
            "> 👋 **Configure welcome messages:** `/setwelcome`\n"
            "> 🚫 **Configure leave messages:** `/setleave`\n"
            "> ⭐️ **Configure starboard:** `/setstar`\n"
            "> 💡 **Configure suggestions:** `/setsuggest`\n"
            "> <a:Boost:1258934863529246762> **Configure boost messages:** `/setboost`\n"
            f"> ⚙️ **Show {ctx.guild.name}'s Configurations:** `/configs`\n"
            "\n*If you need any help, feel free to join our* [***Support Server***](https://discord.gg/t9g3Wbt9Sj)*!*."
            )
        await ctx.send(embed=e, ephemeral=True)

    @commands.hybrid_command(description="Donate to Commie")
    async def donate(self, ctx):
        e = discord.Embed(color=commie_color)
        e.set_author(name="Donating to Commie", icon_url=commie_logo)
        e.set_thumbnail(url=commie_logo)
        e.description = "Thank you for wanting to donate to **Commie**! It's very appreciated! **Commie** runs off of donations like yours to keep being updated! \n### 🔍 Getting Donator Role 🔍 \n> To get the 'Donator' role, head to the [**Support Server**](<https://discord.gg/t9g3Wbt9Sj>) and open a ticket! \n> The donation **must** be over **$1 USD** to get the role!"
        view = discord.ui.View()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="💎 Donate to Commie!", url="https://en.liberapay.com/CommieBot/"))
        await ctx.send(embed=e, view=view, ephemeral=True)

    @commands.hybrid_command(description="Vote for Commie")
    async def vote(self, ctx):
        e = discord.Embed(color=commie_color)
        e.set_author(name="Vote for Commie", icon_url=commie_logo)
        e.set_thumbnail(url=commie_logo)
        e.description = "Thank you for wanting to vote for **Commie**! It's very appreciated! \n\n*Voting sites are linked below!*"
        view = discord.ui.View()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, emoji="<:DiscordBotList:1260504121249628201>", label="Vote for Commie!", url="https://discordbotlist.com/bots/commie"))
        await ctx.send(embed=e, view=view, ephemeral=True)

    @commands.hybrid_command(description="Test if the bot is up")
    async def test(self, ctx):
        await ctx.send("I'm up! <a:CommiePet:1258041355012149328>")

    @commands.hybrid_command(description="Sends Commie's ping")
    async def ping(self, ctx):
        e = discord.Embed(color=commie_color)
        e.add_field(
            name="📶 Ping",
            value=f"**Commie's** ping is **{round(self.bot.latency * 1000)}**ms",
            inline=False
        )
        await ctx.send(embed=e)

    @commands.hybrid_command(description="Make a suggestion")
    async def suggest(self, ctx, *, suggestion):
        try:
            config = await self.get_config(ctx.guild.id)
            if not config:
                await ctx.send("Suggestions are disabled or no suggestion channel is set for **{ctx.guild.name}**!")
                return
            suggestion_channel_id = config.get("suggestion_channel")
            if suggestion_channel_id:
                suggestion_channel = self.bot.get_channel(suggestion_channel_id)
                await ctx.send(f"Your suggestion has been added! Check {suggestion_channel.mention}!")
                se = discord.Embed(color=commie_color)
                se.set_author(name=f"Suggested by {ctx.author}")
                se.set_thumbnail(url=ctx.author.avatar.url)
                se.description = suggestion
                if ctx.message.attachments:
                    attachment_url = ctx.message.attachments[0].url
                    se.set_image(url=attachment_url)
                se.timestamp = datetime.utcnow()
                vote = await suggestion_channel.send(embed=se)
                for emoji in ["👍", "🤷‍♂️", "👎"]:
                    await vote.add_reaction(emoji)
            else:
                await ctx.send(f"Suggestions are disabled or no suggestion channel is set for **{ctx.guild.name}**!")
        except Exception as e:
            print(e)
    
    @commands.hybrid_command(description="Create a poll!")
    async def poll(self, ctx, question:str, option1:str=None, option2:str=None, option3:str=None, option4:str=None, option5:str=None):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        options = [option1, option2, option3, option4, option5]
        options = [option for option in options if option is not None]
        emoji_list = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]      
        if not options:
            await ctx.send("Please provide at least two options for the poll.")
            return
        if len(options) > 5:
            await ctx.send("You can only have up to 5 options in the poll.")
            return       
        e = discord.Embed(color=commie_color)
        e.title = f"📊 **{question}**"
        description_text = ""
        for i, option in enumerate(options):
            description_text += f"\n{emoji_list[i]} {option}"
        e.description = description_text
        msg = await ctx.send(embed=e)
        for i in range(len(options)):
            await msg.add_reaction(emoji_list[i])

async def setup(bot):
    await bot.add_cog(GeneralCog(bot))
