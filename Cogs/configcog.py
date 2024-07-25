import discord
from discord.ext import commands
import aiosqlite
import asyncio

commie_logo = "https://media.discordapp.net/attachments/1257979868784758854/1258026914816331807/CommieLogo.png?ex=66868c5d&is=66853add&hm=36c6a57e62eca6ec2954f76efc6d20add7ea2ab786380aab1f1994e55513ef05&=&format=webp&quality=lossless"
commie_color = 0xd40001
boost_color = 0xff73fa

class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.get_prefix = self.get_prefix
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.create_config_table()

    async def create_config_table(self):
        async with aiosqlite.connect("dbs/configs.db") as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS server_configs (
                    server_id INTEGER PRIMARY KEY,
                    prefix TEXT DEFAULT '!',
                    admin TEXT,
                    moderator TEXT,
                    helper TEXT,
                    toggle_logging BOOLEAN,
                    logging_channel INTEGER,
                    toggle_welcome BOOLEAN,
                    welcome_channel INTEGER,
                    welcome_message TEXT,
                    toggle_leave BOOLEAN,
                    leave_channel INTEGER,
                    leave_message TEXT,
                    toggle_starboard BOOLEAN,
                    starboard_channel INTEGER,
                    star_count INTEGER,
                    toggle_suggest BOOLEAN,
                    suggestion_channel INTEGER,
                    toggle_boost BOOLEAN,
                    boost_channel INTEGER,
                    description TEXT,
                    boost_perk_1 TEXT,
                    boost_perk_2 TEXT,
                    boost_perk_3 TEXT,
                    boost_perk_4 TEXT,
                    boost_perk_5 TEXT,
                    boost_perk_6 TEXT,
                    boost_perk_7 TEXT,
                    boost_perk_8 TEXT,
                    boost_perk_9 TEXT,
                    boost_perk_10 TEXT,
                    toggle_autorole BOOLEAN,
                    role1 INTEGER,
                    role2 INTEGER,
                    role3 INTEGER,
                    role4 INTEGER,
                    role5 INTEGER
                )
            ''')
            await db.commit()

    async def has_admin_role(self, user, guild_id):
        config = await self.get_config(guild_id)
        if config and config['admin']:
            admin_roles = config['admin'].split(',')
            user_roles = [role.id for role in user.roles]
            if any(int(role) in user_roles for role in admin_roles):
                return True
        return False

    async def get_prefix(self, message):
        config = await self.get_config(message.guild.id)
        return config['prefix'] if config and config['prefix'] else "!"

    async def get_config(self, guild_id):
        async with aiosqlite.connect("dbs/configs.db") as db:
            async with db.execute("SELECT * FROM server_configs WHERE server_id = ?", (guild_id,)) as cursor:
                result = await cursor.fetchone()
                if result:
                    columns = [column[0] for column in cursor.description]
                    return dict(zip(columns, result))
                return None

    async def save_config(self, guild_id, config):
        async with aiosqlite.connect("dbs/configs.db") as db:
            placeholders = ', '.join([f"{key} = ?" for key in config.keys()])
            values = list(config.values())
            await db.execute(f"REPLACE INTO server_configs (server_id, {', '.join(config.keys())}) VALUES (?, {', '.join(['?'] * len(values))})",
                             [guild_id, *values])
            await db.commit()

    @commands.hybrid_group(name="toggle", description="Toggle features for the server")
    async def toggle_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `/toggle <feature>` to toggle specific features.")

    @toggle_group.command(name="log", description="Toggle the logging feature")
    async def log(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id) or {}
            logging_enabled = config.get('toggle_logging', False)
            e = discord.Embed(color=commie_color)
            e.set_author(name="📋 Logging", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.description = f"Toggle the logging feature for **{ctx.guild.name}**. Click the **'Enable'** button to enable or the **'Disable'** button to disable it."
            view = discord.ui.View()
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Enable", custom_id="enable"))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Disable", custom_id="disable"))
            initial_message = await ctx.send(embed=e, view=view)
            def check(interaction):
                return interaction.type == discord.InteractionType.component and interaction.user == ctx.author and interaction.data['custom_id'] in ["enable", "disable"]
            interaction = await self.bot.wait_for("interaction", check=check)
            if interaction.data['custom_id'] == "disable":
                if not logging_enabled:
                    await interaction.response.send_message("Event logging is already disabled!")
                    await initial_message.delete()
                    return
                config['toggle_logging'] = False
                await self.save_config(ctx.guild.id, config)
                await interaction.response.send_message(f"**{ctx.guild.name}'s** event logging has been disabled.")
                await initial_message.delete()
                return
            if interaction.data['custom_id'] == "enable":
                config['toggle_logging'] = True
                await self.save_config(ctx.guild.id, config)
                await interaction.response.send_message(f"**{ctx.guild.name}'s** event logging has been enabled, to set it up do `set log`!")
                await initial_message.delete()
        except Exception as e:
            print(e)

    @toggle_group.command(name="suggest", description="Toggle the suggestions feature")
    async def suggest(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id) or {}
            suggestions_enabled = config.get('toggle_suggest', False)
            e = discord.Embed(color=commie_color)
            e.set_author(name="💡 Suggestions", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.description = f"Toggle the suggestions feature for **{ctx.guild.name}**. Click the **'Enable'** button to enable or the **'Disable'** button to disable it."
            view = discord.ui.View()
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Enable", custom_id="enable"))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Disable", custom_id="disable"))
            initial_message = await ctx.send(embed=e, view=view)
            def check(interaction):
                return interaction.type == discord.InteractionType.component and interaction.user == ctx.author and interaction.data['custom_id'] in ["enable", "disable"]
            interaction = await self.bot.wait_for("interaction", check=check)
            if interaction.data['custom_id'] == "disable":
                if not suggestions_enabled:
                    await interaction.response.send_message("Suggestions are already disabled!")
                    await initial_message.delete()
                    return
                config['toggle_suggest'] = False
                await self.save_config(ctx.guild.id, config)
                await interaction.response.send_message(f"**{ctx.guild.name}'s** suggestions have been disabled.")
                await initial_message.delete()
                return
            if interaction.data['custom_id'] == "enable":
                config['toggle_suggest'] = True
                await self.save_config(ctx.guild.id, config)
                await interaction.response.send_message(f"**{ctx.guild.name}'s** suggestions have been enabled, to set it up do `set suggest`!")
                await initial_message.delete()
        except Exception as e:
            print(e)

    @toggle_group.command(name="star", description="Toggle the starboard feature")
    async def star(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id) or {}
            starboard_enabled = config.get('toggle_starboard', False)
            e = discord.Embed(color=commie_color)
            e.set_author(name="⭐️ Starboard", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.description = f"Toggle the starboard feature for **{ctx.guild.name}**. Click the **'Enable'** button to enable or the **'Disable'** button to disable it."
            view = discord.ui.View()
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Enable", custom_id="enable"))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Disable", custom_id="disable"))
            initial_message = await ctx.send(embed=e, view=view)
            def check(interaction):
                return interaction.type == discord.InteractionType.component and interaction.user == ctx.author and interaction.data['custom_id'] in ["enable", "disable"]
            interaction = await self.bot.wait_for("interaction", check=check)
            if interaction.data['custom_id'] == "disable":
                if not starboard_enabled:
                    await interaction.response.send_message("The starboard is already disabled!")
                    await initial_message.delete()
                    return
                config['toggle_starboard'] = False
                await self.save_config(ctx.guild.id, config)
                await interaction.response.send_message(f"**{ctx.guild.name}'s** starboard has been disabled.")
                await initial_message.delete()
                return
            if interaction.data['custom_id'] == "enable":
                config['toggle_starboard'] = True
                await self.save_config(ctx.guild.id, config)
                await interaction.response.send_message(f"**{ctx.guild.name}'s** starboard has been enabled, to set it up do `set star`!")
                await initial_message.delete()
        except Exception as e:
            print(e)

    @toggle_group.command(name="welcome", description="Toggle the welcome messages feature")
    async def welcome(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id) or {}
            welcome_enabled = config.get('toggle_welcome', False)
            e = discord.Embed(color=commie_color)
            e.set_author(name="👋 Welcome Messages", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.description = f"Toggle the welcome messages feature for **{ctx.guild.name}**. Click the **'Enable'** button to enable or the **'Disable'** button to disable it."
            view = discord.ui.View()
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Enable", custom_id="enable"))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Disable", custom_id="disable"))
            initial_message = await ctx.send(embed=e, view=view)
            def check(interaction):
                return interaction.type == discord.InteractionType.component and interaction.user == ctx.author and interaction.data['custom_id'] in ["enable", "disable"]
            interaction = await self.bot.wait_for("interaction", check=check)
            if interaction.data['custom_id'] == "disable":
                if not welcome_enabled:
                    await interaction.response.send_message("Welcome messages are already disabled!")
                    await initial_message.delete()
                    return
                config['toggle_welcome'] = False
                await self.save_config(ctx.guild.id, config)
                await interaction.response.send_message(f"**{ctx.guild.name}'s** welcome messages have been disabled.")
                await initial_message.delete()
                return
            if interaction.data['custom_id'] == "enable":
                config['toggle_welcome'] = True
                await self.save_config(ctx.guild.id, config)
                await interaction.response.send_message(f"**{ctx.guild.name}'s** welcome messages have been enabled, to set it up do `set welcome`!")
                await initial_message.delete()
        except Exception as e:
            print(e)
    
    @toggle_group.command(name="leave", description="Toggle the leave messages feature")
    async def leave(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id) or {}
            leave_enabled = config.get('toggle_leave', False)
            e = discord.Embed(color=commie_color)
            e.set_author(name="🚫 Leave Messages", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.description = (f"Toggle the leave messages feature for **{ctx.guild.name}**. "
                             "Click the **'Enable'** button to enable or the **'Disable'** button to disable it.")
            view = discord.ui.View()
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Enable", custom_id="enable"))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Disable", custom_id="disable"))
            initial_message = await ctx.send(embed=e, view=view)
            def check(interaction):
                return interaction.type == discord.InteractionType.component and interaction.user == ctx.author and interaction.data['custom_id'] in ["enable", "disable"]
            interaction = await self.bot.wait_for("interaction", check=check)
            if interaction.data['custom_id'] == "disable":
                if not leave_enabled:
                    await interaction.response.send_message("Leave messages are already disabled!", ephemeral=True)
                    await initial_message.delete()
                    return
                config['toggle_leave'] = False
                await self.save_config(ctx.guild.id, config)
                await interaction.response.send_message(f"**{ctx.guild.name}'s** leave messages have been disabled.")
                await initial_message.delete()
                return
            if interaction.data['custom_id'] == "enable":
                config['toggle_leave'] = True
                await self.save_config(ctx.guild.id, config)
                await interaction.response.send_message(f"**{ctx.guild.name}'s** leave messages have been enabled, to set it up do `set leave`!")
                await initial_message.delete()
        except Exception as e:
            print(e)

    @toggle_group.command(name="boost", description="Toggle the boost messages feature")
    async def boost(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id) or {}
            boost_enabled = config.get('toggle_boost', False)
            e = discord.Embed(color=commie_color)
            e.set_author(name="Boost Messages", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.description = f"Toggle the boost messages feature for **{ctx.guild.name}**. Click the **'Enable'** button to enable or the **'Disable'** button to disable it."
            view = discord.ui.View()
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Enable", custom_id="enable"))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Disable", custom_id="disable"))
            initial_message = await ctx.send(embed=e, view=view)
            def check(interaction):
                return interaction.type == discord.InteractionType.component and interaction.user == ctx.author and interaction.data['custom_id'] in ["enable", "disable"]
            interaction = await self.bot.wait_for("interaction", check=check)
            if interaction.data['custom_id'] == "disable":
                if not boost_enabled:
                    await interaction.response.send_message("Boost messages are already disabled!", ephemeral=True)
                    await initial_message.delete()
                    return
                config['toggle_boost'] = False
                await self.save_config(ctx.guild.id, config)
                await interaction.response.send_message(f"**{ctx.guild.name}'s** boost messages have been disabled.")
                await initial_message.delete()
                return
            if interaction.data['custom_id'] == "enable":
                config['toggle_boost'] = True
                await self.save_config(ctx.guild.id, config)
                await interaction.response.send_message(f"**{ctx.guild.name}'s** boost messages have been enabled, to set it up do `set boost`!")
                await initial_message.delete()
        except Exception as e:
            print(e)

    @toggle_group.command(name="autorole", description="Toggle the autorole feature")
    async def autorole(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id) or {}
            autorole_enabled = config.get('toggle_autorole', False)
            e = discord.Embed(color=commie_color)
            e.set_author(name="🤖 Autorole", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.description = f"Toggle the autorole feature for **{ctx.guild.name}**. Click the **'Enable'** button to enable or the **'Disable'** button to disable it."
            view = discord.ui.View()
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Enable", custom_id="enable"))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Disable", custom_id="disable"))
            initial_message = await ctx.send(embed=e, view=view)
            def check(interaction):
                return interaction.type == discord.InteractionType.component and interaction.user == ctx.author and interaction.data['custom_id'] in ["enable", "disable"]
            interaction = await self.bot.wait_for("interaction", check=check)
            if interaction.data['custom_id'] == "disable":
                if not autorole_enabled:
                    await interaction.response.send_message("Autorole is already disabled!", ephemeral=True)
                    await initial_message.delete()
                    return
                config['toggle_autorole'] = False
                await self.save_config(ctx.guild.id, config)
                await interaction.response.send_message(f"**{ctx.guild.name}'s** autorole has been disabled.")
                await initial_message.delete()
                return
            if interaction.data['custom_id'] == "enable":
                config['toggle_autorole'] = True
                await self.save_config(ctx.guild.id, config)
                await interaction.response.send_message(f"**{ctx.guild.name}'s** autorole has been enabled, to set it up do `set autorole`!")
                await initial_message.delete()
        except Exception as e:
            print(e)

    @commands.hybrid_group(name="set", description="Set features for the server")
    async def set_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `/set <feature>` to set specific features.")

    @set_group.command(name="prefix", description="Set the bot's prefix for the server")
    async def prefix(self, ctx, new_prefix: str):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id) or {}
            config['prefix'] = new_prefix
            await self.save_config(ctx.guild.id, config)
            await ctx.send(f"**{ctx.guild.name}** server prefix is now: `{new_prefix}`")
        except Exception as e:
            print(e)

    @set_group.command(name="staff", description="Set the staff commands for your server")
    async def staff(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You do not have the required permissions to use this command.", ephemeral=True, delete_after=10)
            return
        try:
            e = discord.Embed(color=commie_color)
            e.set_author(name="Staff Roles", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.description = (f"To set the 'staff' roles for **{ctx.guild.name}**, click the **'Start'** button down below! \n\n### ⚖️ Role Ranks \n> - **Admin** | "
                             f"*Has access to the 'config' commands, ex: `setstaff`, and all staff commands* \n> - **Moderator** | "
                             f"*Has access to various staff commands, ex: `ban`, `gulag`* \n> - **Helper** | *Has access to smaller staff commands, ex: `kick`, `warn`* \n\n*Be careful who you give access!*")
            view = discord.ui.View()
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Start", custom_id="start"))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Cancel", custom_id="cancel"))
            initial_message = await ctx.send(embed=e, view=view)
            def check(interaction):
                return interaction.type == discord.InteractionType.component and interaction.user == ctx.author and interaction.data['custom_id'] in ["start", "cancel"]
            interaction = await self.bot.wait_for("interaction", check=check)
            if interaction.data['custom_id'] == "cancel":
                await interaction.response.send_message("Command canceled.", ephemeral=True)
                await initial_message.delete()
                return
            if interaction.data['custom_id'] == "start":
                await interaction.response.defer()
                admin_roles, moderator_roles, helper_roles = [], [], []
                message = await self.send_role_prompt(ctx, "Admin", admin_roles, moderator_roles, helper_roles)
                await self.collect_roles(ctx, "Admin", admin_roles, moderator_roles, helper_roles, message)
                await message.edit(content="Mention (**@**) your **Moderator** role(s)! Say '**done**' when you're finished mentioning **Moderator** Roles! To skip this Staff Role, say '**skip**'!", embed=self.format_embed(ctx, admin_roles, moderator_roles, helper_roles))
                await self.collect_roles(ctx, "Moderator", admin_roles, moderator_roles, helper_roles, message)
                await message.edit(content="Mention (**@**) your **Helper** role(s)! Say '**done**' when you're finished mentioning **Helper** Roles! To skip this Staff Role, say '**skip**'!", embed=self.format_embed(ctx, admin_roles, moderator_roles, helper_roles))
                await self.collect_roles(ctx, "Helper", admin_roles, moderator_roles, helper_roles, message)
                config = await self.get_config(ctx.guild.id) or {}
                config['admin'] = ','.join([str(role.id) for role in admin_roles])
                config['moderator'] = ','.join([str(role.id) for role in moderator_roles])
                config['helper'] = ','.join([str(role.id) for role in helper_roles])
                await self.save_config(ctx.guild.id, config)
                await ctx.send(f"All staff roles for **{ctx.guild.name}** have been added! To view them use the `configs` command!")
        except Exception as e:
            print(e)

    @set_group.command(name="log", description="Set the servers logging channel")
    async def log(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        config = await self.get_config(ctx.guild.id)
        if not config or not config.get('toggle_logging'):
            await ctx.send(f"**{ctx.guild.name}'s** event logging is **disabled**! To enable it do `toggle log`!")
            return
        await ctx.send("Mention the channel to set as your logging channel!")
        try:
            def check_channel(message):
                return message.author == ctx.author and message.channel == ctx.channel and message.channel_mentions
            msg = await self.bot.wait_for("message", timeout=30.0, check=check_channel)
            channel = msg.channel_mentions[0]
            config['logging_channel'] = channel.id
            await self.save_config(ctx.guild.id, config)
            await ctx.send(f"**{ctx.guild.name}'s** logging channel has been set to {channel.mention}!")
        except asyncio.TimeoutError:
            await ctx.send("Timed out. Logging setup cancelled.", delete_after=10)

    @set_group.command(name="suggest", description="Set the suggestion channel for the server")
    async def suggest(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        config = await self.get_config(ctx.guild.id)
        if not config or not config.get('toggle_suggest'):
            await ctx.send(f"**{ctx.guild.name}'s** suggestions are **disabled**! To enable it do `toggle suggest`!")
            return
        await ctx.send("Mention the channel to set as your suggestion channel!")
        def check_channel(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.channel_mentions
        try:
            msg = await self.bot.wait_for("message", timeout=30.0, check=check_channel)
            channel = msg.channel_mentions[0]
            config['suggestion_channel'] = channel.id
            await self.save_config(ctx.guild.id, config)
            await ctx.send(f"**{ctx.guild.name}'s** suggestion channel has been set to {channel.mention}!")
        except asyncio.TimeoutError:
            await ctx.send("Timed out. Suggestion channel setting cancelled.", delete_after=10)
        except Exception as e:
            print(e)

    @set_group.command(name="star", description="Set the star count and starboard channel")
    async def star(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        config = await self.get_config(ctx.guild.id)
        if not config or not config.get('toggle_starboard'):
            await ctx.send(f"**{ctx.guild.name}'s** starboard is **disabled**! To enable it do `toggle star`!")
            return
        await ctx.send("Mention the channel to set as your starboard!")
        try:
            def check_channel(message):
                return message.author == ctx.author and message.channel == ctx.channel and message.channel_mentions
            msg = await self.bot.wait_for("message", timeout=30.0, check=check_channel)
            channel = msg.channel_mentions[0]
            config['starboard_channel'] = channel.id
            await self.save_config(ctx.guild.id, config)
            await ctx.send(f"**{ctx.guild.name}'s** starboard channel has been set to {channel.mention}!")
            await ctx.send("How many ⭐ reactions should put a message on your starboard?")
            def check_number(message):
                return message.author == ctx.author and message.channel == ctx.channel
            msg = await self.bot.wait_for("message", timeout=30.0, check=check_number)
            if not msg.content.isdigit():
                await ctx.send("That's not a number! Try again!", delete_after=10)
                return
            star_count = int(msg.content)
            config['star_count'] = star_count
            await self.save_config(ctx.guild.id, config)
            await ctx.send(f"For **{ctx.guild.name}**, it takes **{star_count}** ⭐ reactions to get a message onto the starboard!")
        except asyncio.TimeoutError:
            await ctx.send("Timed out. Starboard setup cancelled.", delete_after=10)

    @set_group.command(name="welcome", description="Set the welcome message and welcome channel")
    async def welcome(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            e = discord.Embed(color=commie_color)
            e.set_author(name="Welcome Message Setup", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.description = ("Create and send your welcome message! You can use the following variables:\n"
                             "> 📑 `{name}` = **User's username**\n"
                             "> 🔔 `{mention}` = **Mentions the user**\n"
                             "> 📰 `{server}` = **Server name**\n\n"
                             "**Example:** `Welcome {mention} to {server}!`")
            await ctx.send(embed=e)
            def check(message):
                return message.author == ctx.author and message.channel == ctx.channel
            while True:
                msg = await self.bot.wait_for('message', check=check)
                welcome_message = msg.content
                preview_message = welcome_message.format(name="ExampleUser", mention=ctx.author.mention, server=ctx.guild.name)
                confirm_embed = discord.Embed(color=commie_color)
                confirm_embed.set_author(name=f"{ctx.guild.name}'s Welcome Message", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
                confirm_embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
                confirm_embed.description = (f"*Does this look correct? If not, click* ***No*** *and remake it!*\n\n"
                                             f"{preview_message}")
                view = discord.ui.View()
                view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="Yes", custom_id="yes"))
                view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="No", custom_id="no"))
                confirmation_message = await ctx.send(embed=confirm_embed, view=view)
                def check_interaction(interaction):
                    return interaction.type == discord.InteractionType.component and interaction.user == ctx.author and interaction.data['custom_id'] in ["yes", "no"]
                interaction = await self.bot.wait_for("interaction", check=check_interaction)
                if interaction.data['custom_id'] == "yes":
                    await confirmation_message.delete()
                    break
                elif interaction.data['custom_id'] == "no":
                    await confirmation_message.delete()
                    await ctx.send("Create and send your welcome message! Be sure to include the variables as shown! Ex: `{mention}`")
            await ctx.send("Mention the channel you want to have your welcome messages show up in!")
            msg = await self.bot.wait_for("message", check=check)
            channel = msg.channel_mentions[0]
            config = await self.get_config(ctx.guild.id) or {}
            config['toggle_welcome'] = True
            config['welcome_channel'] = channel.id
            config['welcome_message'] = welcome_message
            await self.save_config(ctx.guild.id, config)
            await ctx.send(f"**{ctx.guild.name}'s** welcoming channel has been set to {channel.mention}! To see your welcome message do `test welcome`!")
        except Exception as e:
            print(e)

    @set_group.command(name="leave", description="Set the leave message and leave channel")
    async def leave(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            e = discord.Embed(color=commie_color)
            e.set_author(name="Leave Message Setup", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.description = ("Create and send your leave message! You can use the following variables:\n"
                             "> 📑 `{name}` = **User's username**\n"
                             "> 🔔 `{mention}` = **Mentions the user**\n"
                             "> 📰 `{server}` = **Server name**\n\n"
                             "**Example:** `{name} has left {server}!`")
            await ctx.send(embed=e)
            def check(message):
                return message.author == ctx.author and message.channel == ctx.channel
            while True:
                msg = await self.bot.wait_for('message', check=check)
                leave_message = msg.content
                preview_message = leave_message.format(name="ExampleUser", mention=ctx.author.mention, server=ctx.guild.name)
                confirm_embed = discord.Embed(color=commie_color)
                confirm_embed.set_author(name=f"{ctx.guild.name}'s Leave Message", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
                confirm_embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
                confirm_embed.description = (f"*Does this look correct? If not, click* ***No*** *and remake it!*\n\n"
                                             f"{preview_message}")
                view = discord.ui.View()
                view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="Yes", custom_id="yes"))
                view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="No", custom_id="no"))
                confirmation_message = await ctx.send(embed=confirm_embed, view=view)
                def check_interaction(interaction):
                    return interaction.type == discord.InteractionType.component and interaction.user == ctx.author and interaction.data['custom_id'] in ["yes", "no"]
                interaction = await self.bot.wait_for("interaction", check=check_interaction)
                if interaction.data['custom_id'] == "yes":
                    await confirmation_message.delete()
                    break
                elif interaction.data['custom_id'] == "no":
                    await confirmation_message.delete()
                    await ctx.send("Create and send your leave message! Be sure to include the variables as shown! Ex: `{mention}`")
            await ctx.send("Mention the channel you want to have your leave messages show up in!")
            msg = await self.bot.wait_for("message", check=check)
            channel = msg.channel_mentions[0]
            config = await self.get_config(ctx.guild.id) or {}
            config['toggle_leave'] = True
            config['leave_channel'] = channel.id
            config['leave_message'] = leave_message
            await self.save_config(ctx.guild.id, config)
            await ctx.send(f"**{ctx.guild.name}'s** leave channel has been set to {channel.mention}! To see your leave message do `test leave`!")
        except Exception as e:
            print(e)

    @set_group.command(name="boost", description="Set the boost message and channel")
    async def boost(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            e = discord.Embed(color=commie_color)
            e.set_author(name="Boost Message Setup", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.description = ("You can use the following variables in your boost message:\n"
                            "📑 `{name}` = **Boosting member's name**\n"
                            "🔔 `{mention}` = **Mentions the Boosting member**\n"
                            "📰 `{server}` = **Server name**\n\n"
                            "**Example:** `Thank you {mention} for boosting {server}!`")
            await ctx.send(embed=e)
            initial_embed = discord.Embed(color=boost_color)
            initial_embed.title = f"<a:Boost:1258934863529246762> {ctx.author.name} boosted the server!"
            initial_embed.set_thumbnail(url=ctx.author.avatar.url)
            initial_embed.description = "**[ Placeholder ]** \n\n***You'll now receive these perks:*** \n> [ Placeholder Perk 1 ]"
            preview_message = await ctx.send(embed=initial_embed)
            await ctx.send("Customize your boost message description! For example: Thank you `{mention}` for boosting the server!")
            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel
            msg = await self.bot.wait_for('message', check=check, timeout=300)
            description = msg.content
            initial_embed.description = description.format(name=ctx.author.name, mention=ctx.author.mention, server=ctx.guild.name) + "\n\n***You'll now receive these perks:***"
            await preview_message.edit(embed=initial_embed)
            perks = []
            for i in range(1, 11):
                await ctx.send(f"What is your {['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth'][i-1]} booster perk? Once it's added to the embed, say '**done**' to go to the next perk. If that's all your perks, say '**complete**'!")
                msg = await self.bot.wait_for('message', check=check, timeout=300)
                if msg.content.lower() == 'complete':
                    break
                perks.append(msg.content)
                initial_embed.description += f"\n> {msg.content}"
                await preview_message.edit(embed=initial_embed)
            await ctx.send("Mention the channel the boost message should be sent in!")
            msg = await self.bot.wait_for('message', check=check, timeout=300)
            channel = msg.channel_mentions[0]
            config = await self.get_config(ctx.guild.id) or {}
            config['toggle_boost'] = True
            config['boost_channel'] = channel.id
            config['description'] = description
            for i, perk in enumerate(perks, 1):
                config[f'boost_perk_{i}'] = perk
            await self.save_config(ctx.guild.id, config)
            await ctx.send(f"**{ctx.guild.name}'s** boost message channel has been set to {channel.mention}! To see your boost message do `test boost`!")
        except asyncio.TimeoutError:
            await ctx.send("Timed out. Boost setup cancelled.", delete_after=10)
        except Exception as e:
            print(e)

    @set_group.command(name="autorole", description="Set autoroles for the server")
    async def autorole(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            await ctx.send(f"Mention your first **Auto Role** for **{ctx.guild.name}**! Say '**done**' to move to the next role! Say '**complete**' if that's all your roles!")
            roles = []
            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel
            while len(roles) < 5:
                msg = await self.bot.wait_for('message', check=check)
                if msg.content.lower() == 'complete':
                    break
                if msg.role_mentions:
                    roles.append(msg.role_mentions[0])
                    await ctx.send(f"Role collected. Mention the next role or say '**complete**'.")
                else:
                    await ctx.send("Please mention a valid role.")
            config = await self.get_config(ctx.guild.id) or {}
            for i, role in enumerate(roles):
                config[f'role{i+1}'] = role.id
            await self.save_config(ctx.guild.id, config)
            role_mentions = ', '.join([role.mention for role in roles])
            await ctx.send(f"All auto roles for **{ctx.guild.name}** have been collected! \n> {role_mentions}")
        except Exception as e:
            print(e)

    @commands.hybrid_command(description="View the server configurations")
    async def configs(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id)
            if not config:
                await ctx.send(f"No configurations found for **{ctx.guild.name}**.", ephemeral=True)
                return
            prefix = config.get('prefix', "!")
            admin_roles = [int(role_id) for role_id in config.get('admin', "").split(',') if role_id]
            moderator_roles = [int(role_id) for role_id in config.get('moderator', "").split(',') if role_id]
            helper_roles = [int(role_id) for role_id in config.get('helper', "").split(',') if role_id]
            starboard_enabled = config.get('toggle_starboard', False)
            starboard_channel_id = config.get('starboard_channel')
            star_count = config.get('star_count')
            logging_enabled = config.get('toggle_logging', False)
            logging_channel_id = config.get('logging_channel')
            suggestions_enabled = config.get('toggle_suggest', False)
            suggestions_channel_id = config.get('suggestion_channel')
            welcome_enabled = config.get('toggle_welcome', False)
            welcome_channel_id = config.get('welcome_channel')
            leave_enabled = config.get('toggle_leave', False)
            leave_channel_id = config.get('leave_channel')
            boost_enabled = config.get('toggle_boost', False)
            boost_channel_id = config.get('boost_channel')
            autorole_enabled = config.get('toggle_autorole', False)
            roles = [config.get(f'role{i}') for i in range(1, 6)]
            roles_mentions = ', '.join([ctx.guild.get_role(role_id).mention for role_id in roles if role_id])
            e = discord.Embed(color=commie_color)
            e.set_author(name=f"{ctx.guild.name} Configurations", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.add_field(name="🔔 Server Prefix", value=f"> **{prefix}**", inline=False)
            admin_mentions = ', '.join([ctx.guild.get_role(role_id).mention for role_id in admin_roles if ctx.guild.get_role(role_id)]) if admin_roles else "None"
            moderator_mentions = ', '.join([ctx.guild.get_role(role_id).mention for role_id in moderator_roles if ctx.guild.get_role(role_id)]) if moderator_roles else "None"
            helper_mentions = ', '.join([ctx.guild.get_role(role_id).mention for role_id in helper_roles if ctx.guild.get_role(role_id)]) if helper_roles else "None"
            e.add_field(name="🔰 Staff Roles", value=f"> 🥇 **Admin:** {admin_mentions}\n> 🥈 **Moderator:** {moderator_mentions}\n> 🥉 **Helper:** {helper_mentions}", inline=False)
            if logging_enabled:
                logging_channel = f"**Channel:** {ctx.guild.get_channel(logging_channel_id).mention}" if logging_channel_id and ctx.guild.get_channel(logging_channel_id) else "**Channel:** **None**"
                e.add_field(name="🗃 Logging", value=f"> {logging_channel}", inline=False)
            else:
                e.add_field(name="🗃 Logging", value="> ❌ **Disabled**", inline=False)
            if suggestions_enabled:
                suggestions_channel = f"**Channel:** {ctx.guild.get_channel(suggestions_channel_id).mention}" if suggestions_channel_id and ctx.guild.get_channel(suggestions_channel_id) else "**Channel:** **None**"
                e.add_field(name="💡 Suggestions", value=f"> {suggestions_channel}", inline=False)
            else:
                e.add_field(name="💡 Suggestions", value="> ❌ **Disabled**", inline=False)
            if starboard_enabled:
                starboard_channel = f"**Channel:** {ctx.guild.get_channel(starboard_channel_id).mention}" if starboard_channel_id and ctx.guild.get_channel(starboard_channel_id) else "**Channel:** **None**"
                starboard_count = f"**Star Count:** {star_count}" if star_count else "**Star Count:** **None**"
                e.add_field(name="⭐ Starboard", value=f"> {starboard_channel}\n> {starboard_count}", inline=False)
            else:
                e.add_field(name="⭐ Starboard", value="> ❌ **Disabled**", inline=False)
            if welcome_enabled:
                welcome_channel = f"**Channel:** {ctx.guild.get_channel(welcome_channel_id).mention}" if welcome_channel_id and ctx.guild.get_channel(welcome_channel_id) else "**Channel:** **None**"
                e.add_field(name="👋 Welcome Messages", value=f"> {welcome_channel}", inline=False)
            else:
                e.add_field(name="👋 Welcome Messages", value="> ❌ **Disabled**", inline=False)
            if leave_enabled:
                leave_channel = f"**Channel:** {ctx.guild.get_channel(leave_channel_id).mention}" if leave_channel_id and ctx.guild.get_channel(leave_channel_id) else "**Channel:** **None**"
                e.add_field(name="🚫 Leave Messages", value=f"> {leave_channel}", inline=False)
            else:
                e.add_field(name="🚫 Leave Messages", value="> ❌ **Disabled**", inline=False)
            if boost_enabled:
                boost_channel = f"**Channel:** {ctx.guild.get_channel(boost_channel_id).mention}" if boost_channel_id and ctx.guild.get_channel(boost_channel_id) else "**Channel:** **None**"
                e.add_field(name="<a:Boost:1261831287786704966> Boost Messages", value=f"> {boost_channel}", inline=False)
            else:
                e.add_field(name="<a:Boost:1261831287786704966> Boost Messages", value="> ❌ **Disabled**", inline=False)
            if autorole_enabled:
                e.add_field(name="🎭 AutoRoles", value=f"> {roles_mentions}", inline=False)
            else:
                e.add_field(name="🎭 AutoRoles", value="> ❌ **Disabled**", inline=False)
            await ctx.send(embed=e)
        except Exception as e:
            print(e)

async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
