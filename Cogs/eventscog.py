import discord
from discord.ext import commands
from datetime import datetime
import aiosqlite

boost_color = 0xff73fa
commie_logo = "https://media.discordapp.net/attachments/1257979868784758854/1258026914816331807/CommieLogo.png?ex=66868c5d&is=66853add&hm=36c6a57e62eca6ec2954f76efc6d20add7ea2ab786380aab1f1994e55513ef05&=&format=webp&quality=lossless"
commie_color = 0xd40001

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.processed_messages = set()
    
    async def get_config(self, guild_id):
        try:
            async with aiosqlite.connect("dbs/configs.db") as db:
                async with db.execute("SELECT * FROM server_configs WHERE server_id = ?", (guild_id,)) as cursor:
                    result = await cursor.fetchone()
                    if result:
                        columns = [column[0] for column in cursor.description]
                        config = dict(zip(columns, result))
                        config['filtered_words'] = [w for w in config.get('filtered_words', '').split(',') if w]
                        config['ignored_words'] = [w for w in config.get('ignored_words', '').split(',') if w]
                        config['blocked_users'] = [u for u in config.get('blocked_users', '').split(',') if u]
                        config['blocked_roles'] = [r for r in config.get('blocked_roles', '').split(',') if r]
                        config['blocked_channels'] = [c for c in config.get('blocked_channels', '').split(',') if c]
                        config['blocked_categories'] = [cat for cat in config.get('blocked_categories', '').split(',') if cat]
                        return config
                    return None
        except Exception as e:
            print(e)
            return None

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Game(name="Helping fellow Comrades..."))
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        try:
            if reaction.emoji == "⭐":
                config = await self.get_config(reaction.message.guild.id)
                if not config:
                    return
                starboard_enabled = config.get("toggle_starboard")
                starboard_channel_id = config.get("starboard_channel")
                star_count = config.get("star_count")
                if not starboard_enabled or not starboard_channel_id or not star_count:
                    return
                async with aiosqlite.connect("dbs/menus.db") as db:
                    async with db.execute("SELECT menu_id FROM menus WHERE message_id = ?", (reaction.message.id,)) as cursor:
                        result = await cursor.fetchone()
                if result:
                    return
                if reaction.count >= star_count and reaction.message.id not in self.processed_messages:
                    starboard_channel = self.bot.get_channel(starboard_channel_id)
                    if starboard_channel:
                        e = discord.Embed(color=0xF7c11e)
                        e.set_author(name=reaction.message.author.display_name, icon_url=reaction.message.author.avatar.url)
                        e.description = reaction.message.content
                        if reaction.message.attachments:
                            e.set_image(url=reaction.message.attachments[0].url)
                        e.add_field(name="**Posted In**", value=reaction.message.channel.mention)
                        jump_url = reaction.message.jump_url
                        e.add_field(name="**Jump URL**", value=f"[Message Link]({jump_url})")
                        e.timestamp = datetime.utcnow()
                        await starboard_channel.send(embed=e)
                        self.processed_messages.add(reaction.message.id)
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        try:
            if before.premium_since is None and after.premium_since is not None:
                config = await self.get_config(after.guild.id)
                if not config:
                    return
                boost_enabled = config.get("toggle_boost")
                boost_channel_id = config.get("boost_channel")
                description = config.get("description")
                perks = [config.get(f"boost_perk_{i}") for i in range(1, 11)]
                if boost_enabled and boost_channel_id:
                    channel = self.bot.get_channel(boost_channel_id)
                    e = discord.Embed(color=boost_color)
                    e.title = f"<a:Boost:1258934863529246762> {after.name} boosted the server!"
                    e.set_thumbnail(url=after.avatar.url)
                    e.description = description.format(name=after.name, mention=after.mention, server=after.guild.name)
                    if any(perks):
                        e.description += "\n\n***You'll now receive these perks:***\n"
                        for perk in perks:
                            if perk:
                                e.description += f"> {perk}\n"
                    await channel.send(embed=e)
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            config = await self.get_config(member.guild.id)
            if not config:
                return
            welcome_status = config.get("toggle_welcome")
            welcome_channel_id = config.get("welcome_channel")
            welcome_message = config.get("welcome_message")
            if welcome_status and welcome_channel_id and welcome_message:
                welcome_channel = self.bot.get_channel(welcome_channel_id)
                if welcome_channel:
                    welcome_text = welcome_message.format(name=member.name, mention=member.mention, server=member.guild.name)
                    await welcome_channel.send(welcome_text)
            autorole_status = config.get("toggle_autorole")
            if autorole_status:
                role_ids = [config.get(f'role{i}') for i in range(1, 6)]
                roles = [member.guild.get_role(int(role_id)) for role_id in role_ids if role_id]
                for role in roles:
                    if role:
                        await member.add_roles(role)
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        try:
            config = await self.get_config(member.guild.id)
            if not config:
                return
            leave_status = config.get("toggle_leave")
            leave_channel_id = config.get("leave_channel")
            leave_message = config.get("leave_message")
            if leave_status and leave_channel_id and leave_message:
                leave_channel = self.bot.get_channel(leave_channel_id)
                if leave_channel:
                    leave_text = leave_message.format(name=member.name, mention=member.mention, server=member.guild.name)
                    await leave_channel.send(leave_text)
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        try:
            channel = self.bot.get_channel(1257988420144201810)
            e = discord.Embed(color=0x00fb15)
            e.title = "✅ Bot Added ✅"
            e.description = f"**Commie** has been added! \n<:ChainReply:1259287285845725214> **Guild:** {guild.name} \n<:Reply:1259287286814740541> **ID:** {guild.id}"
            e.timestamp = datetime.utcnow()
            await channel.send(embed=e)
            setup_embed = discord.Embed(color=commie_color)
            setup_embed.set_author(name="Thank you for adding Commie!", icon_url=commie_logo)
            setup_embed.set_thumbnail(url=commie_logo)
            setup_embed.description = (
                "**# 📌 How To Setup Commie 📌**\n"
                "Toggle the commands to **enable** or **disable** them, then use the `set` commands to customize them!\n"
                "### Toggle Commands\n"
                "> ⚖️ `/togglelog`\n"
                "> ⚖️ `/togglewelcome`\n"
                "> ⚖️ `/toggleleave`\n"
                "> ⚖️ `/togglestar`\n"
                "> ⚖️ `/togglesuggest`\n"
                "> ⚖️ `/toggleboost`\n"
                "> ⚖️ `/toggleautorole`\n"
                "> ⚖️ `/togglefilter`\n"
                "### Configuration Commands\n"
                "> 🔔 **Set the bot prefix:** `/setprefix [prefix]` (Default is `!`)\n"
                "> 🔰 **Set staff roles:** `/setstaff`\n"
                "> 🗃 **Configure logging:** `/setlog`\n"
                "> 👋 **Configure welcome messages:** `/setwelcome`\n"
                "> 🚫 **Configure leave messages:** `/setleave`\n"
                "> ⭐️ **Configure starboard:** `/setstar`\n"
                "> 💡 **Configure suggestions:** `/setsuggest`\n"
                "> <a:Boost:1258934863529246762> **Configure boost messages:** `/setboost`\n"
                "> 🎭 **Configure auto roles:** `/setautoroles`\n"
                f"> ⚙️ **Show {guild.name}'s Configurations:** `/configs`\n"
                "\n*If you need any help, feel free to join our* [***Support Server***](https://discord.gg/t9g3Wbt9Sj)*!*."
                )
            if guild.system_channel:
                await guild.system_channel.send(embed=setup_embed)
            else:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        await channel.send(embed=setup_embed)
                        break
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        try:
            channel = self.bot.get_channel(1257988420144201810)
            e = discord.Embed(color=0xFf0000)
            e.title = "❌ Bot Removed ❌"
            e.description = f"**Commie** has been removed! \n<:ChainReply:1259287285845725214> **Guild:** {guild.name} \n<:Reply:1259287286814740541> **ID:** {guild.id}"
            e.timestamp = datetime.utcnow()
            await channel.send(embed=e)
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            if message.author.bot:
                return
            config = await self.get_config(message.guild.id)
            if not config or not config.get('toggle_filter'):
                return
            filtered_words = config.get('filtered_words', [])
            ignored_words = config.get('ignored_words', [])
            blocked_users = config.get('blocked_users', [])
            blocked_roles = config.get('blocked_roles', [])
            blocked_channels = config.get('blocked_channels', [])
            blocked_categories = config.get('blocked_categories', [])
            if str(message.author.id) in blocked_users:
                return
            if str(message.channel.id) in blocked_channels:
                return
            if message.channel.category and str(message.channel.category.id) in blocked_categories:
                return
            if any(role.id in map(int, blocked_roles) for role in message.author.roles):
                return
            message_content = message.content.lower()
            for word in filtered_words:
                if word in message_content:
                    if any(ignored_word in message_content for ignored_word in ignored_words):
                        continue
                    await message.delete()
                    break
        except Exception as e:
            print(f"Error in on_message: {e}")

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
