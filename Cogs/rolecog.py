import aiosqlite
import discord
from discord.ext import commands
import asyncio
import re

commie_logo = "https://media.discordapp.net/attachments/1257979868784758854/1258026914816331807/CommieLogo.png?ex=66868c5d&is=66853add&hm=36c6a57e62eca6ec2954f76efc6d20add7ea2ab786380aab1f1994e55513ef05&=&format=webp&quality=lossless"
commie_color = 0xd40001

color_mapping = {
    "red": 0xd40001,
    "orange": 0xff6800,
    "yellow": 0xffe600,
    "green": 0x02ce16,
    "blue": 0x0038ff,
    "purple": 0x4c00cb,
    "pink": 0xffa2ed,
    "brown": 0x752c00,
    "black": 0x000000,
    "grey": 0x909090,
    "white": 0xffffff
}

custom_emoji_pattern = re.compile(r"^<a?:\w+:\d+>$")
default_emoji_pattern = re.compile(r"[\U0001F300-\U0001FAFF]|[\u2600-\u27BF]")

class RoleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.menus = {}
        self.editing_role = False

    @commands.Cog.listener()
    async def on_ready(self):
        await self.create_menu_table()
        await self.load_menus()

    async def create_menu_table(self):
        async with aiosqlite.connect("dbs/menus.db") as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS menus (
                    menu_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER,
                    guild_id INTEGER,
                    selection_format TEXT,
                    title TEXT,
                    description TEXT,
                    color INTEGER,
                    include_role_name BOOLEAN
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS menu_roles (
                    menu_id INTEGER,
                    role_id INTEGER,
                    emoji TEXT,
                    role_description TEXT,
                    PRIMARY KEY (menu_id, role_id)
                )
            ''')
            await db.commit()

    async def load_menus(self):
        async with aiosqlite.connect("dbs/menus.db") as db:
            async with db.execute("SELECT * FROM menus") as cursor:
                async for row in cursor:
                    menu_id, message_id, guild_id, selection_format, title, description, color, include_role_name = row
                    self.menus[menu_id] = {
                        "message_id": message_id,
                        "guild_id": guild_id,
                        "selection_format": selection_format,
                        "title": title,
                        "description": description,
                        "color": color,
                        "include_role_name": include_role_name,
                        "roles": {}
                    }
            async with db.execute("SELECT * FROM menu_roles") as cursor:
                async for row in cursor:
                    menu_id, role_id, emoji, role_description = row
                    if menu_id in self.menus:
                        self.menus[menu_id]["roles"][str(role_id)] = {
                            "emoji": emoji,
                            "description": role_description
                        }
        for menu_id, menu in self.menus.items():
            if menu['selection_format'] in ['buttons', 'dropdown']:
                channel = self.bot.get_channel(menu['guild_id'])
                if channel is not None:
                    try:
                        message = await channel.fetch_message(menu['message_id'])
                        view = self.create_view(menu)
                        await message.edit(view=view)
                    except Exception as e:
                        print(f"Failed to re-register interactions for menu {menu_id}: {e}")

    def create_view(self, menu):
        view = discord.ui.View()
        if menu["selection_format"] == "buttons":
            for role_id, role_data in menu["roles"].items():
                role = self.bot.get_guild(menu['guild_id']).get_role(int(role_id))
                button = discord.ui.Button(label=role.name if menu["include_role_name"] else "", emoji=role_data["emoji"], custom_id=str(role_id))
                button.callback = self.handle_button_interaction
                view.add_item(button)
        elif menu["selection_format"] == "dropdown":
            options = []
            for role_id, role_data in menu["roles"].items():
                role = self.bot.get_guild(menu['guild_id']).get_role(int(role_id))
                options.append(discord.SelectOption(label=role.name, emoji=role_data["emoji"], value=str(role_id)))
            select = discord.ui.Select(placeholder="Choose your role...", options=options)
            select.callback = self.handle_select
            view.add_item(select)
        return view

    async def save_menu(self, menu_id, message_id, guild_id, selection_format, title, description, color, include_role_name, roles):
        async with aiosqlite.connect("dbs/menus.db") as db:
            await db.execute("REPLACE INTO menus (menu_id, message_id, guild_id, selection_format, title, description, color, include_role_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                             (menu_id, message_id, guild_id, selection_format, title, description, color, include_role_name))
            await db.execute("DELETE FROM menu_roles WHERE menu_id = ?", (menu_id,))
            for role_id, role_data in roles.items():
                await db.execute("INSERT INTO menu_roles (menu_id, role_id, emoji, role_description) VALUES (?, ?, ?, ?)",
                                 (menu_id, role_id, role_data["emoji"], role_data["description"]))
            await db.commit()

    async def has_admin_role(self, user, guild_id):
        config = await self.get_config(guild_id)
        if config and config['admin']:
            admin_roles = config['admin'].split(',')
            user_roles = [role.id for role in user.roles]
            if any(int(role) in user_roles for role in admin_roles):
                return True
        return False

    async def get_config(self, guild_id):
        async with aiosqlite.connect("dbs/configs.db") as db:
            async with db.execute("SELECT * FROM server_configs WHERE server_id = ?", (guild_id,)) as cursor:
                result = await cursor.fetchone()
                if result:
                    columns = [column[0] for column in cursor.description]
                    return dict(zip(columns, result))
                return None

    async def get_next_menu_id(self):
        async with aiosqlite.connect("dbs/menus.db") as db:
            async with db.execute("SELECT MAX(menu_id) FROM menus") as cursor:
                result = await cursor.fetchone()
                if result[0] is None:
                    return 1000000001
                return result[0] + 1

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            await self.handle_reaction(payload, add=True)
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        try:
            await self.handle_reaction(payload, add=False)
        except Exception as e:
            print(e)

    async def handle_reaction(self, payload, add):
        try:
            message_id = payload.message_id
            if message_id not in [menu["message_id"] for menu in self.menus.values()]:
                return
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return
            member = guild.get_member(payload.user_id)
            if member is None:
                return
            if member.bot:
                return
            menu = next(menu for menu in self.menus.values() if menu["message_id"] == message_id)
            role_id = next((role_id for role_id, emoji in menu["roles"].items() if emoji == str(payload.emoji)), None)
            if role_id:
                role = guild.get_role(int(role_id))
                if role:
                    if add:
                        await member.add_roles(role)
                    else:
                        await member.remove_roles(role)
                else:
                    print(f"Role not found for ID {role_id}")
            else:
                print(f"Role ID not found for the reaction emoji {payload.emoji}")
        except Exception as e:
            print(f"Error handling reaction: {e}")

    async def handle_button_interaction(self, interaction):
        try:
            custom_id = interaction.data['custom_id']
            role_id = int(custom_id)
            guild = interaction.guild
            member = interaction.user
            role = guild.get_role(role_id)
            if role in member.roles:
                await member.remove_roles(role)
                await interaction.response.send_message(f"❌ Role **{role.name}** removed!", ephemeral=True)
            else:
                await member.add_roles(role)
                await interaction.response.send_message(f"✅ Role **{role.name}** added!", ephemeral=True)
        except Exception as e:
            print(f"Error handling button interaction: {e}")

    async def handle_select(self, interaction):
        try:
            if self.editing_role:
                return
            if 'values' not in interaction.data or not all(value.isdigit() for value in interaction.data['values']):
                return
            role_ids = [int(value) for value in interaction.data['values']]
            guild = interaction.guild
            member = interaction.user
            added_roles = []
            removed_roles = []
            for role_id in role_ids:
                role = guild.get_role(role_id)
                if role not in member.roles:
                    added_roles.append(role)
                    await member.add_roles(role)
                else:
                    removed_roles.append(role)
                    await member.remove_roles(role)
            added_msg = ', '.join([role.mention for role in added_roles]) if added_roles else None
            removed_msg = ', '.join([role.mention for role in removed_roles]) if removed_roles else None
            if added_roles and removed_roles:
                await interaction.response.send_message(f"✅ Roles added: **{added_msg}**\n❌ Roles removed: **{removed_msg}**", ephemeral=True)
            elif added_roles:
                await interaction.response.send_message(f"✅ Role added: **{added_msg}**", ephemeral=True)
            elif removed_roles:
                await interaction.response.send_message(f"❌ Role removed: **{removed_msg}**", ephemeral=True)
        except Exception as e:
            print(f"Error handling select: {e}")

    @commands.hybrid_group(name="menu", description="Manage self role menus")
    async def menu_group(self, ctx):
        if ctx.invoked_subcommand is None:
            return

    @menu_group.command(name="create", description="Create a self role menu")
    async def create(self, ctx):
        if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            e = discord.Embed(color=commie_color)
            e.set_author(name="Commie Self Role Menu Color Choices", icon_url=commie_logo)
            e.set_thumbnail(url=commie_logo)
            e.description = (
                "# 🛍️ Available Color Choices 🛍️\n"
                "> 🔴 Red\n"
                "> 🟠 Orange\n"
                "> 🟡 Yellow\n"
                "> 🟢 Green\n"
                "> 🔵 Blue\n"
                "> 🟣 Purple\n"
                "> 🌸 Pink\n"
                "> 🟤 Brown\n"
                "> ⚫️ Black\n"
                "> 🔘 Grey\n"
                "> ⚪️ White\n\n"
                "### 👾 Custom Colors 👾\n"
                "> To set a custom color use a hex code (**Ex:** `#ff5733`)"
            )
            color_embed = await ctx.send(embed=e)
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            color = msg.content.strip()
            if color.startswith('#') and len(color) == 7:
                color_value = int(color[1:], 16)
            elif color in color_mapping:
                color_value = color_mapping[color]
            else:
                color_value = commie_color
            await msg.delete()
            embed = discord.Embed(title="Placeholder", description="Placeholder", color=color_value)
            message = await ctx.send(embed=embed)
            await color_embed.delete()
            prompt_msg = await ctx.send("What should be the **title** of your menu?")
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            embed.title = msg.content.strip()
            await message.edit(embed=embed)
            await msg.delete()
            await prompt_msg.delete()
            prompt_msg = await ctx.send(f"What should be the **description** of the **{embed.title}** menu? If none, say **skip**!")
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            if msg.content.lower() == "skip":
                embed.description = ""
            else:
                embed.description = msg.content.strip()
            await message.edit(embed=embed)
            await msg.delete()
            await prompt_msg.delete()
            roles = {}
            prompt_msg = await ctx.send(f"Add a role to the **{embed.title}** menu! Send it in this format: `:emoji: @role [Optional Description]`\n-# Mention the next role or say **complete** when you're finished adding roles!")
            while True:
                msg = await self.bot.wait_for('message', check=check, timeout=120)
                if msg.content.lower() == "complete":
                    await msg.delete()
                    break
                parts = msg.content.split(' ', 2)
                if len(parts) < 2 or not msg.role_mentions:
                    await ctx.send("Invalid format. Please use the `:emoji: @role [Optional description]` format.", ephemeral=True, delete_after=10)
                    await msg.delete()
                    continue
                emoji, role_mention = parts[0], parts[1]
                description = parts[2] if len(parts) > 2 else ""
                role = msg.role_mentions[0]
                custom_emoji_match = custom_emoji_pattern.match(emoji)
                default_emoji_match = default_emoji_pattern.match(emoji)
                if custom_emoji_match or default_emoji_match:
                    roles[str(role.id)] = {
                        "emoji": emoji,
                        "description": description
                    }
                    if description:
                        embed.description += f"\n{emoji} {role.mention}: {description}"
                    else:
                        embed.description += f"\n{emoji} {role.mention}"
                    await message.edit(embed=embed)
                else:
                    await ctx.send("Invalid emoji. Please use a valid emoji.", ephemeral=True, delete_after=10)
                await msg.delete()
            await prompt_msg.delete()
            prompt_msg = await ctx.send("Should the menu use **reactions**, **buttons**, or a **dropdown**?")
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            selection_format = msg.content.strip().lower()
            await msg.delete()
            await prompt_msg.delete()
            if selection_format not in ["reactions", "buttons", "dropdown"]:
                await ctx.send("Invalid selection format. Menu creation cancelled.")
                return
            include_role_name = True
            if selection_format == "buttons":
                prompt_msg = await ctx.send("Should the **role name** be included in the **buttons**? Say **yes** or **no**!")
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                include_role_name = msg.content.strip().lower() == "yes"
                await msg.delete()
                await prompt_msg.delete()
            if selection_format == "reactions":
                for emoji in roles.values():
                    await message.add_reaction(emoji["emoji"])
            elif selection_format == "buttons":
                view = discord.ui.View()
                for role_id, role_data in roles.items():
                    role = ctx.guild.get_role(int(role_id))
                    button = discord.ui.Button(label=role.name if include_role_name else "", emoji=role_data["emoji"], custom_id=str(role_id))
                    button.callback = self.handle_button_interaction
                    view.add_item(button)
                await message.edit(view=view)
            elif selection_format == "dropdown":
                options = []
                for role_id, role_data in roles.items():
                    role = ctx.guild.get_role(int(role_id))
                    options.append(discord.SelectOption(label=role.name, emoji=role_data["emoji"], value=str(role_id)))
                select = discord.ui.Select(placeholder="Choose your role...", options=options)
                select.callback = self.handle_select
                view = discord.ui.View()
                view.add_item(select)
                await message.edit(view=view)
            menu_id = await self.get_next_menu_id()
            await self.save_menu(menu_id, message.id, ctx.guild.id, selection_format, embed.title, embed.description, embed.color.value, include_role_name, roles)
            self.menus[menu_id] = {
                "message_id": message.id,
                "guild_id": ctx.guild.id,
                "selection_format": selection_format,
                "title": embed.title,
                "description": embed.description,
                "color": embed.color.value,
                "include_role_name": include_role_name,
                "roles": roles
            }
            await self.send_menu_id(ctx, embed.title, menu_id)
        except Exception as e:
            print(f"Exception in create command: {e}")

    async def send_menu_id(self, ctx, title, menu_id):
        try:
            await ctx.send(f"The **{title}** menu is complete! **Menu ID:** `{menu_id}`")
        except Exception as e:
            print(f"Failed to send menu ID message with ID: {menu_id} - Exception: {e}")

    @menu_group.command(name="send", description="Send a self role menu")
    async def send(self, ctx, menu_id: int):
        try:
            if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
                await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
                return
            menu = self.menus.get(menu_id)
            if not menu or menu['guild_id'] != ctx.guild.id:
                await ctx.send(f"Invalid **Menu ID** or this menu does not belong to **{ctx.guild.name}**")
                return
            embed = discord.Embed(title=menu["title"], description=menu["description"], color=menu["color"])
            for role_id, role_data in menu["roles"].items():
                role = ctx.guild.get_role(int(role_id))
                if role_data["description"]:
                    embed.description += f"\n{role_data['emoji']} {role.mention}: {role_data['description']}"
                else:
                    embed.description += f"\n{role_data['emoji']} {role.mention}"
            message = await ctx.send(embed=embed)
            if menu["selection_format"] == "reactions":
                for role_data in menu["roles"].values():
                    await message.add_reaction(role_data["emoji"])
            elif menu["selection_format"] == "buttons":
                view = discord.ui.View()
                for role_id, role_data in menu["roles"].items():
                    role = ctx.guild.get_role(int(role_id))
                    button = discord.ui.Button(label=role.name if menu["include_role_name"] else "", emoji=role_data["emoji"], custom_id=str(role_id))
                    button.callback = self.handle_button_interaction
                    view.add_item(button)
                await message.edit(view=view)
            elif menu["selection_format"] == "dropdown":
                options = []
                for role_id, role_data in menu["roles"].items():
                    role = ctx.guild.get_role(int(role_id))
                    options.append(discord.SelectOption(label=role.name, emoji=role_data["emoji"], value=str(role_id)))
                select = discord.ui.Select(placeholder="Choose your role...", options=options)
                select.callback = self.handle_select
                view = discord.ui.View()
                view.add_item(select)
                await message.edit(view=view)
            self.menus[menu_id]["message_id"] = message.id
            await self.save_menu(menu_id, message.id, menu["guild_id"], menu["selection_format"], menu["title"], menu["description"], menu["color"], menu["include_role_name"], menu["roles"])
        except Exception as e:
            print(f"Exception in send command: {e}")

    @menu_group.command(name="edit", description="Edit a self role menu")
    async def edit(self, ctx, menu_id: int):
        try:
            if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
                await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
                return
            menu = self.menus.get(menu_id)
            if not menu:
                await ctx.send("Invalid **Menu ID**.")
                return
            if menu['guild_id'] != ctx.guild.id:
                await ctx.send(f"This menu does not belong to **{ctx.guild.name}**!", ephemeral=True)
                return
            e = discord.Embed(color=commie_color)
            e.title = "⚙️ Commie Menu Editor ⚙️"
            e.set_thumbnail(url=ctx.guild.icon.url)
            e.description = (
                "***Choose your editing option!***\n\n"
                "> 🎨 Change the menu's color\n"
                "> 📌 Change the menu's title\n"
                "> 📑 Change the menu's description\n"
                "> ➕ Add a role to the menu\n"
                "> ➖ Remove a role from the menu\n"
                "> 📝 Change a role's description\n"
                "> 🙂 Change a role's emoji\n"
                "> 📮 Change how users select their role's"
            )
            options = [
                discord.SelectOption(label="🎨 Change the menu's color", value="color"),
                discord.SelectOption(label="📌 Change the menu's title", value="title"),
                discord.SelectOption(label="📑 Change the menu's description", value="description"),
                discord.SelectOption(label="➕ Add a role to the menu", value="add"),
                discord.SelectOption(label="➖ Remove a role from the menu", value="remove"),
                discord.SelectOption(label="📝 Change a role's description", value="role_description"),
                discord.SelectOption(label="🙂 Change a role's emoji", value="role_emoji"),
                discord.SelectOption(label="📮 Change how users select their role's", value="format")
            ]
            select = discord.ui.Select(placeholder="Select an action to edit", options=options)
            view = discord.ui.View()
            view.add_item(select)
            async def select_callback(interaction):
                action = interaction.data['values'][0]
                await self.handle_edit_action(interaction, action, menu_id)
            select.callback = select_callback
            await ctx.send(embed=e, view=view)
            await ctx.message.delete()
        except Exception as e:
            print(f"Exception in edit command: {e}")

    async def handle_edit_action(self, interaction, action, menu_id):
        try:
            menu_id = int(menu_id)
            menu = self.menus.get(menu_id)
            if not menu:
                await interaction.response.send_message("Menu not found!", ephemeral=True)
                return
            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel
            async def check_deleted_roles(menu):
                deleted_roles = []
                guild = interaction.guild
                for role_id in list(menu['roles'].keys()):
                    role = guild.get_role(int(role_id))
                    if role is None:
                        deleted_roles.append(role_id)
                return deleted_roles
            async def remove_deleted_roles(deleted_roles, menu):
                for role_id in deleted_roles:
                    del menu['roles'][role_id]
                await self.save_menu(menu_id, menu['message_id'], menu['guild_id'], menu['selection_format'], menu['title'], menu['description'], menu['color'], menu['include_role_name'], menu['roles'])
            while True:
                deleted_roles = await check_deleted_roles(menu)
                if not deleted_roles:
                    break
                await interaction.response.send_message("There is a **deleted role** in the menu, do you want to remove it? Say **yes** or **no**!", ephemeral=True)
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                if msg.content.strip().lower() == "yes":
                    await remove_deleted_roles(deleted_roles, menu)
                    await interaction.followup.send(f"Deleted roles have been removed from **{menu['title']}**. Use `/menu send <menu_id>` to resend it!", ephemeral=True)
                else:
                    await interaction.followup.send("Deleted roles will not be removed. Continuing.", ephemeral=True)
                    break
                await msg.delete()
            if action == "color":
                await interaction.response.send_message("What will be the new menu color? Or send the hex code! **Ex:** `#ff0000`", ephemeral=True)
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                color = msg.content.strip().lower()
                if color.startswith('#') and len(color) == 7:
                    color_value = int(color[1:], 16)
                elif color in color_mapping:
                    color_value = color_mapping[color]
                else:
                    color_value = commie_color
                menu["color"] = color_value
                await self.save_menu(menu_id, menu["message_id"], menu["guild_id"], menu["selection_format"], menu["title"], menu["description"], color_value, menu["include_role_name"], menu["roles"])
                await msg.delete()
                await interaction.message.delete()
                await self.send_updated_message(interaction, f"Menu color has been updated to **{color}**")
            elif action == "title":
                await interaction.response.send_message("What will be the new menu title?", ephemeral=True)
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                menu["title"] = msg.content.strip()
                await self.save_menu(menu_id, menu["message_id"], menu["guild_id"], menu["selection_format"], menu["title"], menu["description"], menu["color"], menu["include_role_name"], menu["roles"])
                await msg.delete()
                await interaction.message.delete()
                await self.send_updated_message(interaction, f"Menu title has been updated to **{menu['title']}**")
            elif action == "description":
                await self.handle_menu_description(interaction, menu_id)
            elif action == "add":
                await interaction.response.send_message("Mention the roles you want to add! Send it in this format: :emoji: @role [Optional Description]\n-# Mention the next role or say **complete** when you're finished adding roles!", ephemeral=True)
                while True:
                    msg = await self.bot.wait_for('message', check=check, timeout=120)
                    if msg.content.lower() == "complete":
                        await msg.delete()
                        break
                    parts = msg.content.split(' ', 2)
                    if len(parts) < 2 or not msg.role_mentions:
                        await interaction.followup.send("Invalid format. Please use the `:emoji: @role [Optional description]` format.", ephemeral=True, delete_after=10)
                        await msg.delete()
                        continue
                    emoji, role_mention = parts[0], parts[1]
                    description = parts[2] if len(parts) > 2 else ""
                    role = msg.role_mentions[0]
                    if not (custom_emoji_pattern.match(emoji) or default_emoji_pattern.match(emoji)):
                        await interaction.followup.send("Invalid emoji. Please use a valid emoji.", ephemeral=True, delete_after=10)
                        await msg.delete()
                        continue
                    menu["roles"][str(role.id)] = {"emoji": emoji, "description": description}
                    await self.save_menu(menu_id, menu["message_id"], menu["guild_id"], menu["selection_format"], menu["title"], menu["description"], menu["color"], menu["include_role_name"], menu["roles"])
                    await interaction.followup.send(f"**{role.name}** added to **{menu['title']}**", ephemeral=True)
                    await msg.delete()
                await interaction.message.delete()
            elif action == "remove":
                await interaction.response.send_message("Mention the roles you want removed! \n-# Mention the next role or say **complete** when you're finished removing roles!", ephemeral=True)
                while True:
                    msg = await self.bot.wait_for('message', check=check, timeout=120)
                    if msg.content.lower() == "complete":
                        await msg.delete()
                        break
                    role = msg.role_mentions[0]
                    if str(role.id) in menu["roles"]:
                        del menu["roles"][str(role.id)]
                        await self.save_menu(menu_id, menu["message_id"], menu["guild_id"], menu["selection_format"], menu["title"], menu["description"], menu["color"], menu["include_role_name"], menu["roles"])
                        await interaction.followup.send(f"**{role.name}** removed from **{menu['title']}**", ephemeral=True)
                    else:
                        await interaction.followup.send(f"The **{role.name}** role is not in the **{menu['title']}** menu", ephemeral=True)
                    await msg.delete()
                await interaction.message.delete()
            elif action == "role_description":
                await interaction.response.send_message("Do you want to **add**, **remove**, or **edit** the role description?", ephemeral=True)
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                choice = msg.content.strip().lower()
                await msg.delete()
                if choice not in ["add", "remove", "edit"]:
                    await interaction.followup.send("Invalid option. Please choose **add**, **remove**, or **edit**.", ephemeral=True)
                    return
                roles_embed = discord.Embed(title="⚙️ Commie Menu Editor ⚙️", color=discord.Color(menu["color"]))
                roles_embed.description = "\n".join([f"{role_data['emoji']} <@&{role_id}>: {role_data['description']}" if role_data['description'] else f"{role_data['emoji']} <@&{role_id}>" for role_id, role_data in menu["roles"].items()])
                options = [discord.SelectOption(label=interaction.guild.get_role(int(role_id)).name, value=str(role_id), emoji=role_data["emoji"]) for role_id, role_data in menu["roles"].items()]
                select = discord.ui.Select(placeholder="Choose the role to edit", options=options)
                select.callback = lambda select_interaction: self.handle_role_description_action(select_interaction, menu_id, choice)
                view = discord.ui.View()
                view.add_item(select)
                await interaction.followup.send(embed=roles_embed, view=view, ephemeral=True)
            elif action == "role_emoji":
                await self.handle_role_emoji_selection(interaction, menu_id)
            elif action == "format":
                await interaction.response.send_message("What will be the new role choosing format? **Options:** reactions, buttons, dropdown", ephemeral=True)
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                new_format = msg.content.strip().lower()
                if new_format not in ["reactions", "buttons", "dropdown"]:
                    await interaction.followup.send("Invalid selection format. Menu edit cancelled.", ephemeral=True)
                    return
                menu["selection_format"] = new_format
                await self.save_menu(menu_id, menu["message_id"], menu["guild_id"], new_format, menu["title"], menu["description"], menu["color"], menu["include_role_name"], menu["roles"])
                await msg.delete()
                await interaction.message.delete()
                await self.send_updated_message(interaction, f"Role choosing format has been updated to **{new_format}**")
        except Exception as e:
            print(e)
        except asyncio.TimeoutError:
            await interaction.followup.send("Timed out. Menu edit cancelled.", ephemeral=True)

    async def handle_menu_description(self, interaction, menu_id):
        try:
            menu = self.menus.get(menu_id)
            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel
            await interaction.response.send_message("Do you want to **add**, **remove**, or **edit** the menu description?", ephemeral=True)
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            choice = msg.content.strip().lower()
            await msg.delete()
            if choice == "add":
                if menu["description"]:
                    await interaction.followup.send(f"This menu already has a description!", ephemeral=True)
                else:
                    await interaction.followup.send("What should the new menu description be?", ephemeral=True)
                    msg = await self.bot.wait_for('message', check=check, timeout=60)
                    description = msg.content.strip()
                    menu["description"] = description
                    await self.save_menu(menu_id, menu["message_id"], menu["guild_id"], menu["selection_format"], menu["title"], description, menu["color"], menu["include_role_name"], menu["roles"])
                    await msg.delete()
                    await interaction.followup.send(f"Menu Description Updated: {description}", ephemeral=True)
            elif choice == "remove":
                if not menu["description"]:
                    await interaction.followup.send("This menu has no description to remove!", ephemeral=True)
                else:
                    menu["description"] = ""
                    await self.save_menu(menu_id, menu["message_id"], menu["guild_id"], menu["selection_format"], menu["title"], "", menu["color"], menu["include_role_name"], menu["roles"])
                    await interaction.followup.send(f"The description for the **{menu['title']}** menu has been removed!", ephemeral=True)
            elif choice == "edit":
                if not menu["description"]:
                    await interaction.followup.send("This menu has no description to edit!", ephemeral=True)
                else:
                    await interaction.followup.send("What should the new menu description be?", ephemeral=True)
                    msg = await self.bot.wait_for('message', check=check, timeout=60)
                    new_description = msg.content.strip()
                    menu["description"] = new_description
                    await self.save_menu(menu_id, menu["message_id"], menu["guild_id"], menu["selection_format"], menu["title"], new_description, menu["color"], menu["include_role_name"], menu["roles"])
                    await msg.delete()
                    await interaction.followup.send(f"**Menu Description Updated:** {new_description}", ephemeral=True)
        except Exception as e:
            print(f"Error handling menu description action: {e}")

    async def handle_role_description_action(self, interaction, menu_id, action):
        try:
            self.editing_role = True
            menu = self.menus.get(menu_id)
            role_id = interaction.data["values"][0]
            role_data = menu["roles"].get(role_id)
            role = interaction.guild.get_role(int(role_id))
            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel
            if action == "remove":
                if not role_data["description"]:
                    await interaction.response.send_message("This role has no description to remove!", ephemeral=True)
                else:
                    menu["roles"][role_id]["description"] = ""
                    await self.save_menu(menu_id, menu["message_id"], menu["guild_id"], menu["selection_format"], menu["title"], menu["description"], menu["color"], menu["include_role_name"], menu["roles"])
                    await interaction.response.send_message("The role description has been removed!", ephemeral=True)
            elif action == "add":
                if role_data["description"]:
                    await interaction.response.send_message("This role already has a description!", ephemeral=True)
                else:
                    await interaction.response.send_message(f"What should be the role description for **{role.name}**?", ephemeral=True)
                    msg = await self.bot.wait_for('message', check=check, timeout=60)
                    description = msg.content.strip()
                    menu["roles"][role_id]["description"] = description
                    await self.save_menu(menu_id, menu["message_id"], menu["guild_id"], menu["selection_format"], menu["title"], menu["description"], menu["color"], menu["include_role_name"], menu["roles"])
                    await msg.delete()
                    await interaction.followup.send(f"**Role Description Added:** {description}", ephemeral=True)
            elif action == "edit":
                if not role_data["description"]:
                    await interaction.response.send_message("This role has no description to edit!", ephemeral=True)
                else:
                    await interaction.response.send_message(f"What should be the new role description for **{role.name}**?", ephemeral=True)
                    msg = await self.bot.wait_for('message', check=check, timeout=60)
                    new_description = msg.content.strip()
                    menu["roles"][role_id]["description"] = new_description
                    await self.save_menu(menu_id, menu["message_id"], menu["guild_id"], menu["selection_format"], menu["title"], menu["description"], menu["color"], menu["include_role_name"], menu["roles"])
                    await msg.delete()
                    await interaction.followup.send(f"**Role Description Updated:** {new_description}", ephemeral=True)
        except Exception as e:
            print(f"Error handling role description action: {e}")
        finally:
            self.editing_role = False

    async def handle_role_emoji_selection(self, interaction, menu_id):
        try:
            menu = self.menus.get(menu_id)
            if not menu:
                await interaction.response.send_message("Menu not found!", ephemeral=True)
                return
            roles_embed = discord.Embed(title="⚙️ Commie Menu Editor ⚙️", color=discord.Color(menu["color"]))
            roles_embed.description = "\n".join([
                f"{role_data['emoji']} <@&{role_id}>"
                for role_id, role_data in menu["roles"].items()
            ])
            if not menu["roles"]:
                await interaction.response.send_message("No roles available to edit emoji.", ephemeral=True)
                return
            options = [
                discord.SelectOption(
                    label=interaction.guild.get_role(int(role_id)).name, 
                    value=str(role_id), 
                    emoji=role_data["emoji"]
                )
                for role_id, role_data in menu["roles"].items()
            ]
            select = discord.ui.Select(placeholder="Choose the role to change its emoji", options=options)
            async def select_callback(select_interaction):
                selected_role_id = select_interaction.data['values'][0]
                await self.prompt_for_emoji_change(select_interaction, menu_id, selected_role_id)
            select.callback = select_callback
            view = discord.ui.View()
            view.add_item(select)
            await interaction.response.send_message(embed=roles_embed, view=view, ephemeral=True)
        except Exception as e:
            print(f"Error in handle_role_emoji_selection: {e}")
            await interaction.response.send_message("An error occurred while selecting a role.", ephemeral=True)

    async def prompt_for_emoji_change(self, interaction, menu_id, role_id):
        try:
            menu = self.menus.get(menu_id)
            role = interaction.guild.get_role(int(role_id))
            if not role:
                await interaction.response.send_message("Role not found!", ephemeral=True)
                return
            await interaction.response.send_message(f"What should be the new emoji for **{role.name}**?", ephemeral=True)
            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            new_emoji = msg.content.strip()
            custom_emoji_match = custom_emoji_pattern.match(new_emoji)
            default_emoji_match = default_emoji_pattern.match(new_emoji)
            if custom_emoji_match or default_emoji_match:
                menu["roles"][role_id]["emoji"] = new_emoji
                await self.save_menu(menu_id, menu["message_id"], menu["guild_id"], menu["selection_format"], menu["title"], menu["description"], menu["color"], menu["include_role_name"], menu["roles"])
                await interaction.followup.send(f"**Role Emoji Updated:** {new_emoji}", ephemeral=True)
            else:
                await interaction.followup.send("That isn't a valid emoji!", ephemeral=True)
            await msg.delete()
        except Exception as e:
            print(f"Error in prompt_for_emoji_change: {e}")
            await interaction.followup.send("An error occurred while changing the emoji.", ephemeral=True)

    async def send_color_embed(self, interaction):
        e = discord.Embed(color=commie_color)
        e.set_author(name="Commie Self Role Menu Color Choices", icon_url=commie_logo)
        e.set_thumbnail(url=commie_logo)
        e.description = "# 🛍️ Available Color Choices 🛍️ \n> 🔴 Red \n> 🟠 Orange \n> 🟡 Yellow \n> 🟢 Green \n> 🔵 Blue \n> 🟣 Purple \n> 🌸 Pink \n> 🟤 Brown \n> ⚫️ Black \n> 🔘 Grey \n> ⚪️ White\n\n### 👾 Custom Colors 👾 \n> To set a custom color use a hex code (**Ex:** `#ff5733`)!"
        await interaction.response.send_message(embed=e, ephemeral=True)

    async def send_updated_message(self, interaction, message):
        await interaction.followup.send(message, ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data['custom_id']
        if custom_id.isdigit():
            await self.handle_button_interaction(interaction)
        elif custom_id.startswith("edit:"):
            action, menu_id = custom_id.split(":")[1:3]
            await self.handle_edit_action(interaction, action, menu_id)
        elif 'values' in interaction.data:
            await self.handle_select(interaction)

    @menu_group.command(name="info", description="Get info about a self role menu")
    async def info(self, ctx, identifier: str):
        try:
            if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
                await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
                return
            original_identifier = identifier
            menu = None
            if identifier.isdigit():
                identifier = int(identifier)
                if identifier in self.menus:
                    menu = self.menus[identifier]
                else:
                    menu = next((m for m in self.menus.values() if m["message_id"] == identifier), None)
                    if menu:
                        identifier = next(key for key, value in self.menus.items() if value == menu)
            if not menu or menu['guild_id'] != ctx.guild.id:
                await ctx.send("Invalid **Menu ID** or **Message ID**, or this menu does not belong to this guild.", ephemeral=True)
                return
            roles_info = ""
            for role_id, role_data in menu["roles"].items():
                role = ctx.guild.get_role(int(role_id))
                role_desc = f": {role_data['description']}" if role_data["description"] else ""
                roles_info += f"> {role_data['emoji']} {role.mention}{role_desc}\n"
            if not roles_info:
                roles_info = "> No roles assigned"
            e = discord.Embed(title="🔍 Menu Information 🔍", color=menu["color"])
            e.set_thumbnail(url=ctx.guild.icon.url)
            e.add_field(name="📌 Menu ID", value=f"> {identifier}", inline=True)
            e.add_field(name="📌 Message ID", value=f"{menu['message_id']}", inline=True)
            e.add_field(name="📰 Title", value=f"> {menu['title']}", inline=False)
            if menu["description"] and menu["description"].strip() != "":
                e.add_field(name="📑 Description", value=f"> {menu['description']}", inline=False)
            e.add_field(name="📮 Format", value=f"> {menu['selection_format']}", inline=False)
            e.add_field(name="🔰 Roles", value=roles_info, inline=False)
            await ctx.send(embed=e, ephemeral=True)
        except Exception as e:
            print(e)

    @menu_group.command(name="help", description="Show menu help menu")
    async def help(self, ctx):
        try:
            if not ctx.author.guild_permissions.administrator and not await self.has_admin_role(ctx.author, ctx.guild.id):
                await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
                return
            e = discord.Embed(title="⚙️ Menu Help ⚙️", color=commie_color)
            e.description="Here are the available public commands for managing self role menus. \n### 📌 Menu Commands 📌\n> ⚙️ `/menu help` **|** Shows the Menu Help Menu\n> 📌 `/menu info [identifier]` **|** Shows information about a self role menu [`identifier` can be either the **Menu ID** or the **Message ID**]\n> 🧮 `/menu create` **|** Creates a self role menu\n> 🛠 `/menu edit [menu_id]` **|** Edits a self role menu\n> 📇 `/menu send [menu_id]` **|** Sends a self role menu"
            await ctx.send(embed=e, ephemeral=True)
        except Exception as e:
            print(e)

    @menu_group.command(name="count", description="Get the current highest Menu ID")
    async def count(self, ctx):
        if ctx.author.id != 532706491438727169:
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        highest_menu_id = await self.get_next_menu_id() - 1
        await ctx.send(f"**Highest Menu ID:** `{highest_menu_id}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RoleCog(bot))
