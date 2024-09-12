import discord
from discord.ext import commands
import aiosqlite
import asyncio

commie_logo = "https://media.discordapp.net/attachments/1257979868784758854/1258026914816331807/CommieLogo.png?ex=66868c5d&is=66853add&hm=36c6a57e62eca6ec2954f76efc6d20add7ea2ab786380aab1f1994e55513ef05&=&format=webp&quality=lossless"
commie_color = 0xd40001
boost_color = 0xff73fa
owner_id = 532706491438727169

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
                    toggle_logging BOOLEAN DEFAULT 0,
                    logging_channel INTEGER,
                    toggle_welcome BOOLEAN DEFAULT 0,
                    welcome_channel INTEGER,
                    welcome_message TEXT,
                    toggle_leave BOOLEAN DEFAULT 0,
                    leave_channel INTEGER,
                    leave_message TEXT,
                    toggle_starboard BOOLEAN DEFAULT 0,
                    starboard_channel INTEGER,
                    star_count INTEGER,
                    toggle_suggest BOOLEAN DEFAULT 0,
                    suggestion_channel INTEGER,
                    toggle_boost BOOLEAN DEFAULT 0,
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
                    toggle_autorole BOOLEAN DEFAULT 0,
                    role1 INTEGER,
                    role2 INTEGER,
                    role3 INTEGER,
                    role4 INTEGER,
                    role5 INTEGER,
                    toggle_filter BOOLEAN DEFAULT 0,
                    filtered_words TEXT DEFAULT '',
                    ignored_words TEXT DEFAULT '',
                    blocked_users TEXT DEFAULT '',
                    blocked_channels TEXT DEFAULT '',
                    blocked_roles TEXT DEFAULT '',
                    blocked_categories TEXT DEFAULT ''
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
        try:
            async with aiosqlite.connect("dbs/configs.db") as db:
                async with db.execute("SELECT * FROM server_configs WHERE server_id = ?", (guild_id,)) as cursor:
                    result = await cursor.fetchone()
                    if result:
                        columns = [column[0] for column in cursor.description]
                        config = dict(zip(columns, result))
                        for key, value in config.items():
                            if value is None:
                                config[key] = ""
                        return config
                    return None
        except Exception as e:
            print(f"Error in get_config: {e}")
            return None

    async def save_config(self, guild_id, config):
        try:
            async with aiosqlite.connect("dbs/configs.db") as db:
                placeholders = ', '.join([f"{key} = ?" for key in config.keys()])
                values = list(config.values())
                await db.execute(f"REPLACE INTO server_configs (server_id, {', '.join(config.keys())}) VALUES (?, {', '.join(['?'] * len(values))})",
                                 [guild_id, *values])
                await db.commit()
        except Exception as e:
            print(f"Error in save_config: {e}")

    async def send_role_prompt(self, ctx, role_type, admin_roles, moderator_roles, helper_roles):
        e = discord.Embed(color=commie_color)
        e.set_author(name="Staff Roles", icon_url=commie_logo)
        e.set_thumbnail(url=commie_logo)
        e.title = f"{ctx.guild.name} Staff Roles"
        e.description = self.format_roles_embed(admin_roles, moderator_roles, helper_roles)
        return await ctx.send(f"Mention (**@**) your **{role_type}** role(s)! Say '**done**' when all **{role_type}** role(s) have been added! Say '**skip**' to move to the next role without adding **{role_type}** role(s)!", embed=e)

    @commands.command()
    async def updatedb(self, ctx):
        if ctx.author.id == owner_id:
            try:
                async with aiosqlite.connect("dbs/configs.db") as db:
                    await db.execute('''
                        ALTER TABLE server_configs
                        ADD COLUMN blocked_categories TEXT DEFAULT ''
                    ''')
                    await db.commit()
                await ctx.send("Database schema updated successfully!", ephemeral=True)
            except Exception as e:
                await ctx.send(f"An error occurred while updating the database: {e}", ephemeral=True)
        else:
            return

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
            enable_button = discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Enable", custom_id="toggle_log_enable")
            disable_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Disable", custom_id="toggle_log_disable")
            async def toggle_log_callback(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You don't have the required permissions for this action!", ephemeral=True)
                    return
                try:
                    if interaction.data['custom_id'] == "toggle_log_disable":
                        if not logging_enabled:
                            await interaction.response.send_message("Event logging is already disabled!", ephemeral=True)
                            await interaction.message.delete()
                            return
                        config['toggle_logging'] = False
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** event logging has been disabled.", ephemeral=True)
                    elif interaction.data['custom_id'] == "toggle_log_enable":
                        if logging_enabled:
                            await interaction.response.send_message("Event logging is already enabled!", ephemeral=True)
                            await interaction.message.delete()
                            return
                        config['toggle_logging'] = True
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** event logging has been enabled, to set it up do `/set log`!", ephemeral=True)
                except Exception as e:
                    print(f"Error in toggle_log_callback: {e}")
                    raise e
                finally:
                    await interaction.message.delete()
            enable_button.callback = toggle_log_callback
            disable_button.callback = toggle_log_callback
            view.add_item(enable_button)
            view.add_item(disable_button)
            await ctx.send(embed=e, view=view)
        except Exception as e:
            print(f"Error in log command: {e}")
            raise e

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
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Enable", custom_id="toggle_suggest_enable"))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Disable", custom_id="toggle_suggest_disable"))
            await ctx.send(embed=e, view=view)
            async def toggle_suggest_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You don't have the required permissions for this action!", ephemeral=True)
                    return
                try:
                    if interaction.data['custom_id'] == "toggle_suggest_disable":
                        if not suggestions_enabled:
                            await interaction.response.send_message("Suggestions are already disabled!", ephemeral=True)
                            await interaction.message.delete()
                            return
                        config['toggle_suggest'] = False
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** suggestions have been disabled.", ephemeral=True)
                    elif interaction.data['custom_id'] == "toggle_suggest_enable":
                        config['toggle_suggest'] = True
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** suggestions have been enabled, to set it up do `/set suggest`!", ephemeral=True)
                except Exception as e:
                    print(f"Error in toggle_suggest_callback: {e}")
                finally:
                    await interaction.message.delete()
            view.children[0].callback = toggle_suggest_callback
            view.children[1].callback = toggle_suggest_callback
        except Exception as e:
            print(f"Error in suggest command: {e}")

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
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Enable", custom_id="toggle_star_enable"))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Disable", custom_id="toggle_star_disable"))
            await ctx.send(embed=e, view=view)
            async def toggle_star_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You don't have the required permissions for this action!", ephemeral=True)
                    return
                try:
                    if interaction.data['custom_id'] == "toggle_star_disable":
                        if not starboard_enabled:
                            await interaction.response.send_message("The starboard is already disabled!", ephemeral=True)
                            await interaction.message.delete()
                            return
                        config['toggle_starboard'] = False
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** starboard has been disabled.", ephemeral=True)
                    elif interaction.data['custom_id'] == "toggle_star_enable":
                        config['toggle_starboard'] = True
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** starboard has been enabled, to set it up do `/set star`!", ephemeral=True)
                except Exception as e:
                    print(f"Error in toggle_star_callback: {e}")
                finally:
                    await interaction.message.delete()
            view.children[0].callback = toggle_star_callback
            view.children[1].callback = toggle_star_callback
        except Exception as e:
            print(f"Error in star command: {e}")

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
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Enable", custom_id="toggle_welcome_enable"))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Disable", custom_id="toggle_welcome_disable"))
            await ctx.send(embed=e, view=view)
            async def toggle_welcome_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You don't have the required permissions for this action!", ephemeral=True)
                    return
                try:
                    if interaction.data['custom_id'] == "toggle_welcome_disable":
                        if not welcome_enabled:
                            await interaction.response.send_message("Welcome messages are already disabled!", ephemeral=True)
                            await interaction.message.delete()
                            return
                        config['toggle_welcome'] = False
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** welcome messages have been disabled.", ephemeral=True)
                    elif interaction.data['custom_id'] == "toggle_welcome_enable":
                        config['toggle_welcome'] = True
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** welcome messages have been enabled, to set it up do `/set welcome`!", ephemeral=True)
                except Exception as e:
                    print(f"Error in toggle_welcome_callback: {e}")
                finally:
                    await interaction.message.delete()
            view.children[0].callback = toggle_welcome_callback
            view.children[1].callback = toggle_welcome_callback
        except Exception as e:
            print(f"Error in welcome command: {e}")

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
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Enable", custom_id="toggle_leave_enable"))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Disable", custom_id="toggle_leave_disable"))
            await ctx.send(embed=e, view=view)
            async def toggle_leave_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You don't have the required permissions for this action!", ephemeral=True)
                    return
                try:
                    if interaction.data['custom_id'] == "toggle_leave_disable":
                        if not leave_enabled:
                            await interaction.response.send_message("Leave messages are already disabled!", ephemeral=True)
                            await interaction.message.delete()
                            return
                        config['toggle_leave'] = False
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** leave messages have been disabled.", ephemeral=True)
                    elif interaction.data['custom_id'] == "toggle_leave_enable":
                        config['toggle_leave'] = True
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** leave messages have been enabled, to set it up do `/set leave`!", ephemeral=True)
                except Exception as e:
                    print(f"Error in toggle_leave_callback: {e}")
                finally:
                    await interaction.message.delete()
            view.children[0].callback = toggle_leave_callback
            view.children[1].callback = toggle_leave_callback
        except Exception as e:
            print(f"Error in leave command: {e}")

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
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Enable", custom_id="toggle_boost_enable"))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Disable", custom_id="toggle_boost_disable"))
            await ctx.send(embed=e, view=view)
            async def toggle_boost_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You don't have the required permissions for this action!", ephemeral=True)
                    return
                try:
                    if interaction.data['custom_id'] == "toggle_boost_disable":
                        if not boost_enabled:
                            await interaction.response.send_message("Boost messages are already disabled!", ephemeral=True)
                            await interaction.message.delete()
                            return
                        config['toggle_boost'] = False
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** boost messages have been disabled.", ephemeral=True)
                    elif interaction.data['custom_id'] == "toggle_boost_enable":
                        config['toggle_boost'] = True
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** boost messages have been enabled, to set it up do `/set boost`!", ephemeral=True)
                except Exception as e:
                    print(f"Error in toggle_boost_callback: {e}")
                finally:
                    await interaction.message.delete()
            view.children[0].callback = toggle_boost_callback
            view.children[1].callback = toggle_boost_callback
        except Exception as e:
            print(f"Error in boost command: {e}")

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
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Enable", custom_id="toggle_autorole_enable"))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Disable", custom_id="toggle_autorole_disable"))
            await ctx.send(embed=e, view=view)
            async def toggle_autorole_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You don't have the required permissions for this action!", ephemeral=True)
                    return
                try:
                    if interaction.data['custom_id'] == "toggle_autorole_disable":
                        if not autorole_enabled:
                            await interaction.response.send_message("Autorole is already disabled!", ephemeral=True)
                            await interaction.message.delete()
                            return
                        config['toggle_autorole'] = False
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** autorole has been disabled.", ephemeral=True)
                    elif interaction.data['custom_id'] == "toggle_autorole_enable":
                        config['toggle_autorole'] = True
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** autorole has been enabled, to set it up do `/set autorole`!", ephemeral=True)
                except Exception as e:
                    print(f"Error in toggle_autorole_callback: {e}")
                finally:
                    await interaction.message.delete()
            view.children[0].callback = toggle_autorole_callback
            view.children[1].callback = toggle_autorole_callback
        except Exception as e:
            print(f"Error in autorole command: {e}")

    @toggle_group.command(name="filter", description="Toggle the chat filter feature")
    async def filter(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id) or {}
            filter_enabled = config.get('toggle_filter', False)
            e = discord.Embed(color=commie_color)
            e.set_author(name="🔇 Chat Filter", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.description = f"Toggle the chat filter feature for **{ctx.guild.name}**. Click the **'Enable'** button to enable or the **'Disable'** button to disable it."
            view = discord.ui.View()
            enable_button = discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Enable", custom_id="toggle_filter_enable")
            disable_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Disable", custom_id="toggle_filter_disable")
            async def toggle_filter_callback(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You don't have the required permissions for this action!", ephemeral=True)
                    return
                try:
                    if interaction.data['custom_id'] == "toggle_filter_disable":
                        if not filter_enabled:
                            await interaction.response.send_message("Chat filter is already disabled!", ephemeral=True)
                            await interaction.message.delete()
                            return
                        config['toggle_filter'] = False
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** chat filter has been disabled.", ephemeral=True)
                    elif interaction.data['custom_id'] == "toggle_filter_enable":
                        if filter_enabled:
                            await interaction.response.send_message("Chat filter is already enabled!", ephemeral=True)
                            await interaction.message.delete()
                            return
                        config['toggle_filter'] = True
                        await self.save_config(ctx.guild.id, config)
                        await interaction.response.send_message(f"**{ctx.guild.name}'s** chat filter has been enabled. Use `/filter help` to get started!", ephemeral=True)
                except Exception as e:
                    print(f"Error in toggle_filter_callback: {e}")
                finally:
                    await interaction.message.delete()
            enable_button.callback = toggle_filter_callback
            disable_button.callback = toggle_filter_callback
            view.add_item(enable_button)
            view.add_item(disable_button)
            await ctx.send(embed=e, view=view)
        except Exception as e:
            print(f"Error in filter command: {e}")

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
            print(f"Error in prefix command: {e}")

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
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="✅ Start", custom_id="set_staff_start"))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="❌ Cancel", custom_id="set_staff_cancel"))
            initial_message = await ctx.send(embed=e, view=view)
            def check(interaction):
                return interaction.type == discord.InteractionType.component and interaction.user == ctx.author and interaction.data['custom_id'].startswith("set_staff")
            interaction = await self.bot.wait_for("interaction", check=check)
            if interaction.data['custom_id'] == "set_staff_cancel":
                await interaction.response.send_message("Command canceled.", ephemeral=True)
                await initial_message.delete()
                return
            if interaction.data['custom_id'] == "set_staff_start":
                await interaction.response.defer()
                admin_roles, moderator_roles, helper_roles = [], [], []
                message = await self.send_role_prompt(ctx, "Admin", admin_roles, moderator_roles, helper_roles)
                await self.collect_roles(ctx, "Admin", admin_roles, moderator_roles, helper_roles, message)
                await message.edit(content="Mention your **Moderator** role(s)! Say '**done**' when all **Moderator** role(s) have been added! Say '**skip**' to move to the next role without adding **Moderator** role(s)!", embed=self.format_embed(ctx, admin_roles, moderator_roles, helper_roles))
                await self.collect_roles(ctx, "Moderator", admin_roles, moderator_roles, helper_roles, message)
                await message.edit(content="Mention your **Helper** role(s)! Say '**done**' when all **Helper** role(s) have been added! Say '**skip**' to move to the next role without adding **Helper** role(s)!", embed=self.format_embed(ctx, admin_roles, moderator_roles, helper_roles))
                await self.collect_roles(ctx, "Helper", admin_roles, moderator_roles, helper_roles, message)
                config = await self.get_config(ctx.guild.id) or {}
                config['admin'] = ','.join([str(role.id) for role in admin_roles])
                config['moderator'] = ','.join([str(role.id) for role in moderator_roles])
                config['helper'] = ','.join([str(role.id) for role in helper_roles])
                await self.save_config(ctx.guild.id, config)
                await ctx.send(f"All staff roles for **{ctx.guild.name}** have been added! To view them use the `/configs` command!")
        except Exception as e:
            print(f"Error in staff command: {e}")

    @set_group.command(name="log", description="Set the servers logging channel")
    async def log(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        config = await self.get_config(ctx.guild.id)
        if not config or not config.get('toggle_logging'):
            await ctx.send(f"**{ctx.guild.name}'s** event logging is **disabled**! To enable it do `/toggle log`!")
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
            await ctx.send(f"**{ctx.guild.name}'s** suggestions are **disabled**! To enable it do `/toggle suggest`!")
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
            print(f"Error in suggest command: {e}")

    @set_group.command(name="star", description="Set the star count and starboard channel")
    async def star(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        config = await self.get_config(ctx.guild.id)
        if not config or not config.get('toggle_starboard'):
            await ctx.send(f"**{ctx.guild.name}'s** starboard is **disabled**! To enable it do `/toggle star`!")
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
                preview_message = welcome_message.format(name=ctx.author.name, mention=ctx.author.mention, server=ctx.guild.name)
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
            await ctx.send(f"**{ctx.guild.name}'s** welcoming channel has been set to {channel.mention}! To see your welcome message do `/test welcome`!")
        except Exception as e:
            print(f"Error in welcome command: {e}")

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
                preview_message = leave_message.format(name=ctx.author.name, mention=ctx.author.mention, server=ctx.guild.name)
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
            await ctx.send(f"**{ctx.guild.name}'s** leave channel has been set to {channel.mention}! To see your leave message do `/test leave`!")
        except Exception as e:
            print(f"Error in leave command: {e}")

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
            instruction_message = await ctx.send("Customize your boost message description!", embed=e)
            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel
            msg = await self.bot.wait_for('message', check=check, timeout=300)
            description = msg.content
            await instruction_message.delete()
            await msg.delete()
            preview_embed = discord.Embed(color=boost_color)
            preview_embed.title = f"<a:Boost:1261831287786704966> {ctx.author.name} boosted the server!"
            preview_embed.set_thumbnail(url=ctx.author.avatar.url)
            preview_embed.description = description.format(name=ctx.author.name, mention=ctx.author.mention, server=ctx.guild.name) + "\n\n***You'll now receive these perks:***"
            preview_message = await ctx.send(embed=preview_embed)
            perks = []
            for i in range(1, 11):
                prompt_message = await ctx.send(f"What is your **{['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth'][i-1]}** booster perk? Once it's added to the embed, say '**done**' to go to the next perk. If that's all your perks, say '**complete**'!")
                msg = await self.bot.wait_for('message', check=check, timeout=300)
                if msg.content.lower() == 'complete':
                    await msg.delete()
                    await prompt_message.delete()
                    break
                if msg.content.lower() == 'done':
                    await msg.delete()
                    await prompt_message.delete()
                    continue
                perks.append(msg.content)
                preview_embed.description += f"\n> {msg.content}"
                await preview_message.edit(embed=preview_embed)
                await msg.delete()
                await prompt_message.delete()
            channel_prompt_message = await ctx.send("Mention the channel the boost message should be sent in!")
            msg = await self.bot.wait_for('message', check=check, timeout=300)
            channel = msg.channel_mentions[0]
            await channel_prompt_message.delete()
            await msg.delete()
            config = await self.get_config(ctx.guild.id) or {}
            config['toggle_boost'] = True
            config['boost_channel'] = channel.id
            config['description'] = description
            for i, perk in enumerate(perks, 1):
                config[f'boost_perk_{i}'] = perk
            await self.save_config(ctx.guild.id, config)
            await ctx.send(f"**{ctx.guild.name}'s** boost message channel has been set to {channel.mention}! To see your boost message, use `/test boost`!")
        except asyncio.TimeoutError:
            await ctx.send("Timed out. Boost setup canceled.", delete_after=10)
        except Exception as e:
            print(f"Error in boost command: {e}")

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
            print(f"Error in autorole command: {e}")

    def format_roles_embed(self, admin_roles, moderator_roles, helper_roles):
        admin_mentions = ', '.join([role.mention for role in admin_roles]) if admin_roles else "None"
        moderator_mentions = ', '.join([role.mention for role in moderator_roles]) if moderator_roles else "None"
        helper_mentions = ', '.join([role.mention for role in helper_roles]) if helper_roles else "None"
        return (f"### 🥇 Admin Roles \n> {admin_mentions}\n\n"
                f"### 🥈 Moderator Roles \n> {moderator_mentions}\n\n"
                f"### 🥉 Helper Roles \n> {helper_mentions}")

    async def collect_roles(self, ctx, role_type, admin_roles, moderator_roles, helper_roles, message):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel
        role_lists = {
            "Admin": admin_roles,
            "Moderator": moderator_roles,
            "Helper": helper_roles
        }
        while True:
            msg = await self.bot.wait_for('message', check=check)
            if msg.content.lower() == "done":
                await message.edit(embed=self.format_embed(ctx, admin_roles, moderator_roles, helper_roles))
                break
            if msg.content.lower() == "skip":
                break
            if msg.role_mentions:
                role_lists[role_type].extend(msg.role_mentions)
                await message.edit(embed=self.format_embed(ctx, admin_roles, moderator_roles, helper_roles))
            await msg.delete()

    def format_embed(self, ctx, admin_roles, moderator_roles, helper_roles):
        embed = discord.Embed(color=commie_color)
        embed.set_author(name=f"{ctx.guild.name} Staff Roles", icon_url=ctx.guild.icon.url)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.title = f"{ctx.guild.name} Staff Roles"
        embed.description = self.format_roles_embed(admin_roles, moderator_roles, helper_roles)
        return embed

    @commands.hybrid_group(name="test", description="Test commands for various features")
    async def test_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `/test <feature>` to test specific features.")

    @test_group.command(name="welcome", description="Test the server's welcome message")
    async def welcome(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id)
            if config and config.get('toggle_welcome') and config.get('welcome_message'):
                welcome_message = config['welcome_message'].format(name=ctx.author.name, mention=ctx.author.mention, server=ctx.guild.name)
                await ctx.send(welcome_message)
            else:
                await ctx.send(f"**{ctx.guild.name}** doesn't have a welcome message set! To **toggle** welcome messages, use `/toggle welcome`, to **set** a welcome message, use `/set welcome`!")
        except Exception as e:
            print(e)

    @test_group.command(name="leave", description="Test the server's leave message")
    async def leave(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id)
            if config and config.get('toggle_leave') and config.get('leave_message'):
                leave_message = config['leave_message'].format(name=ctx.author.name, mention=ctx.author.mention, server=ctx.guild.name)
                await ctx.send(leave_message)
            else:
                await ctx.send(f"**{ctx.guild.name}** doesn't have a leave message set! To **toggle** leave messages, use `/toggle leave`, to **set** a leave message, use `/set leave`!")
        except Exception as e:
            print(e)

    @test_group.command(name="boost", description="Test the server's boost message")
    async def boost(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id)
            if config and config.get('toggle_boost') and config.get('boost_channel'):
                description = config.get('description', "Thank you {mention} for boosting {server}!")
                perks = [config.get(f'boost_perk_{i}', '') for i in range(1, 11)]
                perks_list = "\n".join([f"> {perk}" for perk in perks if perk])
                embed = discord.Embed(color=boost_color)
                embed.title = f"<a:Boost:1261831287786704966> {ctx.author.name} boosted the server!"
                embed.set_thumbnail(url=ctx.author.avatar.url)
                embed.description = description.format(name=ctx.author.name, mention=ctx.author.mention, server=ctx.guild.name) + "\n\n***You'll now receive these perks:***\n" + perks_list
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"**{ctx.guild.name}** doesn't have a boost message set! To **toggle** boost messages, use `/toggle boost`, to **set** a boost message, use `/set boost`!")
        except Exception as e:
            print(e)

    @commands.hybrid_group(name="filter", description="Manage the chat filter")
    async def filter_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `/filter <command>` to manage the chat filter.", ephemeral=True)

    @filter_group.command(name="add", description="Add a word to the filter")
    async def add(self, ctx, word: str):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id)
            if not config or not config.get('toggle_filter'):
                await ctx.send(f"**{ctx.guild.name}'s** chat filter is **disabled**! To enable it do `/toggle filter`!", ephemeral=True)
                return
            filtered_words = [w for w in config.get('filtered_words', '').split(',') if w]
            if word in filtered_words:
                await ctx.send(f"**{word}** is already in the filter.", ephemeral=True)
                return
            filtered_words.append(word)
            config['filtered_words'] = ','.join(filtered_words)
            await self.save_config(ctx.guild.id, config)
            await ctx.send(f"**{word}** has been added to the filter.", ephemeral=True)
        except Exception as e:
            print(e)

    @filter_group.command(name="remove", description="Remove a word from the filter")
    async def remove(self, ctx, word: str):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id)
            if not config or not config.get('toggle_filter'):
                await ctx.send(f"**{ctx.guild.name}'s** chat filter is **disabled**! To enable it do `/toggle filter`!", ephemeral=True)
                return
            filtered_words = config.get('filtered_words', '').split(',')
            if word not in filtered_words:
                await ctx.send(f"**{word}** is not in the filter.", ephemeral=True)
                return
            filtered_words.remove(word)
            config['filtered_words'] = ','.join(filtered_words)
            await self.save_config(ctx.guild.id, config)
            await ctx.send(f"**{word}** removed from the filter.", ephemeral=True)
        except Exception as e:
            print(e)

    @filter_group.command(name="clear", description="Clear the filtered words list")
    async def clear(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id)
            if not config or not config.get('toggle_filter'):
                await ctx.send(f"**{ctx.guild.name}'s** chat filter is **disabled**! To enable it do `/toggle filter`!", ephemeral=True)
                return
            config['filtered_words'] = ''
            await self.save_config(ctx.guild.id, config)
            await ctx.send("Filtered words list cleared.", ephemeral=True)
        except Exception as e:
            print(e)

    @filter_group.command(name="block", description="Block a user, role, channel, or category from the filter")
    async def block(self, ctx, user: discord.Member = None, role: discord.Role = None, channel: discord.TextChannel = None, category_id: str = None):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id)
            if not config or not config.get('toggle_filter'):
                await ctx.send(f"**{ctx.guild.name}'s** chat filter is **disabled**! To enable it do `/toggle filter`!", ephemeral=True)
                return
            if user:
                blocked_users = config.get('blocked_users', '').split(',')
                blocked_users.append(str(user.id))
                config['blocked_users'] = ','.join(blocked_users)
                await ctx.send(f"**{user.name}** has been blocked from the chat filter.", ephemeral=True)
            if role:
                blocked_roles = config.get('blocked_roles', '').split(',')
                blocked_roles.append(str(role.id))
                config['blocked_roles'] = ','.join(blocked_roles)
                await ctx.send(f"**{role.name}** has been blocked from the chat filter.", ephemeral=True)
            if channel:
                blocked_channels = config.get('blocked_channels', '').split(',')
                blocked_channels.append(str(channel.id))
                config['blocked_channels'] = ','.join(blocked_channels)
                await ctx.send(f"**{channel.name}** has been blocked from the chat filter.", ephemeral=True)
            if category_id:
                try:
                    category = ctx.guild.get_channel(int(category_id))
                    if not category or category.type != discord.ChannelType.category:
                        await ctx.send("Invalid category ID provided. Please input a valid category ID.", ephemeral=True, delete_after=10)
                        return
                    blocked_categories = config.get('blocked_categories', '').split(',')
                    blocked_categories.append(str(category_id))
                    config['blocked_categories'] = ','.join(blocked_categories)
                    await ctx.send(f"**{category.name}** has been blocked from the chat filter.", ephemeral=True)
                except ValueError:
                    await ctx.send("Invalid category ID format. Please input a valid integer.", ephemeral=True, delete_after=10)
                    return
            await self.save_config(ctx.guild.id, config)
        except Exception as e:
            print(e)

    @filter_group.command(name="unblock", description="Remove a user, role, channel, or category from the chat filter's block list")
    async def unblock(self, ctx, user: discord.Member = None, role: discord.Role = None, channel: discord.TextChannel = None, category_id: str = None):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id)
            if not config or not config.get('toggle_filter'):
                await ctx.send(f"**{ctx.guild.name}'s** chat filter is **disabled**! To enable it do `/toggle filter`!", ephemeral=True)
                return
            if user:
                blocked_users = config.get('blocked_users', '').split(',')
                if str(user.id) in blocked_users:
                    blocked_users.remove(str(user.id))
                    config['blocked_users'] = ','.join(blocked_users)
                    await ctx.send(f"**{user.name}** has been unblocked from the chat filter.", ephemeral=True)
                else:
                    await ctx.send(f"**{user.name}** is not blocked from the chat filter.", ephemeral=True)
            if role:
                blocked_roles = config.get('blocked_roles', '').split(',')
                if str(role.id) in blocked_roles:
                    blocked_roles.remove(str(role.id))
                    config['blocked_roles'] = ','.join(blocked_roles)
                    await ctx.send(f"**{role.name}** has been unblocked from the chat filter.", ephemeral=True)
                else:
                    await ctx.send(f"**{role.name}** is not blocked from the chat filter.", ephemeral=True)
            if channel:
                blocked_channels = config.get('blocked_channels', '').split(',')
                if str(channel.id) in blocked_channels:
                    blocked_channels.remove(str(channel.id))
                    config['blocked_channels'] = ','.join(blocked_channels)
                    await ctx.send(f"**{channel.name}** has been unblocked from the chat filter.", ephemeral=True)
                else:
                    await ctx.send(f"**{channel.name}** is not blocked from the chat filter.", ephemeral=True)
            if category_id:
                try:
                    blocked_categories = config.get('blocked_categories', '').split(',')
                    if category_id in blocked_categories:
                        blocked_categories.remove(category_id)
                        config['blocked_categories'] = ','.join(blocked_categories)
                        category = ctx.guild.get_channel(int(category_id))
                        if category:
                            await ctx.send(f"**{category.name}** has been unblocked from the chat filter.", ephemeral=True)
                        else:
                            await ctx.send(f"Category ID **{category_id}** has been unblocked from the chat filter.", ephemeral=True)
                    else:
                        await ctx.send(f"Category ID **{category_id}** is not blocked from the chat filter.", ephemeral=True)
                except ValueError:
                    await ctx.send("Invalid category ID format. Please input a valid integer.", ephemeral=True, delete_after=10)
                    return
            await self.save_config(ctx.guild.id, config)
        except Exception as e:
            print(e)

    @filter_group.command(name="ignore", description="Ignore a word from the filter")
    async def ignore(self, ctx, word: str):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id)
            if not config or not config.get('toggle_filter'):
                await ctx.send(f"**{ctx.guild.name}'s** chat filter is **disabled**! To enable it do `/toggle filter`!", ephemeral=True)
                return
            ignored_words = config.get('ignored_words', '').split(',')
            if word in ignored_words:
                await ctx.send(f"**{word}** is already in the ignore list.", ephemeral=True)
                return
            ignored_words.append(word)
            config['ignored_words'] = ','.join(ignored_words)
            await self.save_config(ctx.guild.id, config)
            await ctx.send(f"**{word}** has been added to the ignore list", ephemeral=True)
        except Exception as e:
            print(e)

    @filter_group.command(name="unignore", description="Remove a word from the chat filter's ignore list")
    async def unignore(self, ctx, word: str):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id)
            if not config or not config.get('toggle_filter'):
                await ctx.send(f"**{ctx.guild.name}'s** chat filter is **disabled**! To enable it do `/toggle filter`!", ephemeral=True)
                return
            ignored_words = config.get('ignored_words', "").split(',')
            if word in ignored_words:
                ignored_words.remove(word)
                config['ignored_words'] = ','.join(ignored_words)
                await self.save_config(ctx.guild.id, config)
                await ctx.send(f"**{word}** has been removed from the ignore list", ephemeral=True)
            else:
                await ctx.send(f"**{word}** is not in the ignore list.", ephemeral=True)
        except Exception as e:
            print(e)

    @filter_group.command(name="defaults", description="Add a default list of words to the filter")
    async def defaults(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id)
            if not config or not config.get('toggle_filter'):
                await ctx.send(f"**{ctx.guild.name}'s** chat filter is **disabled**! To enable it do `/toggle filter`!", ephemeral=True)
                return
            default_words = ["nigger", "nigga", "faggot", "fag", "kys"]
            filtered_words = config.get('filtered_words', '').split(',')
            filtered_words.extend([word for word in default_words if word not in filtered_words])
            config['filtered_words'] = ','.join(filtered_words)
            await self.save_config(ctx.guild.id, config)
            await ctx.send("Default words added to the filter.", ephemeral=True)
        except Exception as e:
            print(e)

    @filter_group.command(name="show", description="Show the current chat filter settings")
    async def show(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            config = await self.get_config(ctx.guild.id)
            if not config or not config.get('toggle_filter'):
                await ctx.send(f"**{ctx.guild.name}'s** chat filter is **disabled**! To enable it do `/toggle filter`!", ephemeral=True)
                return
            e = discord.Embed(color=commie_color)
            e.set_author(name=f"{ctx.guild.name} Chat Filter Settings", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            filtered_words = config.get('filtered_words', '').split(',')
            filtered_words_display = ', '.join([f"{word}" for word in filtered_words if word]) or "None"
            e.add_field(name="📑 Filtered Words", value=f"> {filtered_words_display}", inline=False)
            ignored_words = config.get('ignored_words', '').split(',')
            ignored_words_display = ', '.join([f"{word}" for word in ignored_words if word]) or "None"
            e.add_field(name="🚫 Ignored Words", value=f"> {ignored_words_display}", inline=False)
            blocked_users = config.get('blocked_users', '').split(',')
            blocked_users_display = ', '.join([f"<@{uid}>" for uid in blocked_users if uid and ctx.guild.get_member(int(uid))]) or "None"
            e.add_field(name="👤 Blocked Users", value=f"> {blocked_users_display}", inline=False)
            blocked_roles = config.get('blocked_roles', '').split(',')
            blocked_roles_display = ', '.join([f"<@&{rid}>" for rid in blocked_roles if rid and ctx.guild.get_role(int(rid))]) or "None"
            e.add_field(name="🎭 Blocked Roles", value=f"> {blocked_roles_display}", inline=False)
            blocked_channels = config.get('blocked_channels', '').split(',')
            blocked_channels_display = ', '.join([f"<#{cid}>" for cid in blocked_channels if cid and ctx.guild.get_channel(int(cid))]) or "None"
            e.add_field(name="📰 Blocked Channels", value=f"> {blocked_channels_display}", inline=False)
            blocked_categories = config.get('blocked_categories', '').split(',')
            blocked_categories_display = ', '.join([f"{ctx.guild.get_channel(int(catid)).name}" for catid in blocked_categories if catid and ctx.guild.get_channel(int(catid))]) or "None"
            e.add_field(name="📍 Blocked Categories", value=f"> {blocked_categories_display}", inline=False)
            await ctx.send(embed=e, ephemeral=True)
        except Exception as e:
            print(e)

    @filter_group.command(name="help", description="Shows the filter help menu")
    async def help(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True)
            return
        try:
            e = discord.Embed(title=f"⚙️ Filter Help ⚙️", color=commie_color)
            e.description = f"Here are the available public commands for managing the Filter. \n\n### 📌 Filter Commands 📌 \n> 💡 **Toggle filter** **|** `toggle filter` **|** Toggles the chat filter feature \n> ⚙️ **Filter help** **|** `filter help` **|** Sends the Filter Help Menu \n> 📑 **Filter defaults** **|** `filter defaults` **|** Adds a default list of slurs to **{ctx.guild.name}'s** filter \n> ➕ **Filter add** **|** `filter add [word]` **|** Adds a word to the filter \n> ➖ **Filter remove** **|** `filter remove [word]` **|** Removes a word from the filter \n> ♻️ **Filter clear** **|** `filter clear` **|** Clears the filter \n> 🔕 **Filter ignore** **|** `filter ignore [word]` **|** Ignores a word that contains a word in the filter **Ex:** If you ignore 'hit', the message won't be deleted when someone says '**hi**'. \n> 🔔 **Filter unignore** **|** `filter unignore [word]` **|** Unignores a word that contains a word in the filter \n> ❌ **Filter block** **|** `filter block [user] [role] [channel] [category_id]` **|** When a user, role, channel or category is 'blocked' their message won't get deleted when they say a word in the filter \n> ✅ **Filter unblock** **|** `filter unblock [user] [role] [channel] [category_id]` **|** Unblocks a user, role, channel or category you had blocked\n> 📰 **Filter show** **|** `filter show` **|** Shows all the information about the chat filter"
            await ctx.send(embed=e, ephemeral=True)
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
            e = discord.Embed(color=commie_color)
            e.set_author(name=f"{ctx.guild.name} Configurations", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            def add_field(field_name, value, inline=False):
                e.add_field(name=field_name, value=value, inline=inline)
            def add_toggle_field(field_name, toggle_key, channel_key=None, extra_info=None, is_role_list=False):
                if config.get(toggle_key, False):
                    if channel_key:
                        channel = ctx.guild.get_channel(config.get(channel_key))
                        value = f"> **Channel:** {channel.mention if channel else 'None'}"
                        if extra_info:
                            value += f"\n> {extra_info}"
                    elif is_role_list:
                        roles = [ctx.guild.get_role(int(config.get(f'role{i}'))) for i in range(1, 6) if config.get(f'role{i}')]
                        roles_mentions = ', '.join([role.mention for role in roles if role])
                        value = f"> {roles_mentions}" if roles_mentions else "> None"
                    else:
                        value = "> **✅ Enabled**"
                else:
                    value = "> ❌ **Disabled**"
                add_field(field_name, value)
            def get_role_mentions(role_ids):
                return ', '.join([ctx.guild.get_role(int(role_id)).mention for role_id in role_ids.split(',') if role_id])
            add_field("🔔 Server Prefix", f"> **{config.get('prefix', '!')}**")
            add_field("🔰 Staff Roles", f"> 🥇 **Admin:** {get_role_mentions(config.get('admin', ''))}\n"
                                        f"> 🥈 **Moderator:** {get_role_mentions(config.get('moderator', ''))}\n"
                                        f"> 🥉 **Helper:** {get_role_mentions(config.get('helper', ''))}")
            add_toggle_field("🗃 Logging", 'toggle_logging', 'logging_channel')
            add_toggle_field("💡 Suggestions", 'toggle_suggest', 'suggestion_channel')
            add_toggle_field("⭐ Starboard", 'toggle_starboard', 'starboard_channel', f"**Star Count:** {config.get('star_count', 'None')}")
            add_toggle_field("👋 Welcome Messages", 'toggle_welcome', 'welcome_channel')
            add_toggle_field("🚫 Leave Messages", 'toggle_leave', 'leave_channel')
            add_toggle_field("<a:Boost:1261831287786704966> Boost Messages", 'toggle_boost', 'boost_channel')
            add_toggle_field("🎭 AutoRoles", 'toggle_autorole', is_role_list=True)
            add_toggle_field("🗑 Chat Filter", 'toggle_filter')
            await ctx.send(embed=e)
        except Exception as e:
            print(f"Error in configs command: {e}")

async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
