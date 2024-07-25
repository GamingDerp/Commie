import re
import discord
from discord.ext import commands
import aiosqlite
from datetime import datetime

commie_logo = "https://media.discordapp.net/attachments/1257979868784758854/1258026914816331807/CommieLogo.png?ex=66868c5d&is=66853add&hm=36c6a57e62eca6ec2954f76efc6d20add7ea2ab786380aab1f1994e55513ef05&=&format=webp&quality=lossless"
commie_color = 0xd40001

class HighlightCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.create_user_table()

    async def create_user_table(self):
        async with aiosqlite.connect("dbs/highlight.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_highlights (
                    user_id INTEGER,
                    server_id INTEGER,
                    word_list TEXT,
                    ignored_words_list TEXT,
                    ignored_channels TEXT,
                    ignored_users TEXT,
                    PRIMARY KEY (user_id, server_id)
                )
            """)
            await db.commit()

    async def get_user_data(self, user_id, server_id):
        await self.create_user_table()
        async with aiosqlite.connect("dbs/highlight.db") as db:
            async with db.execute("SELECT word_list, ignored_words_list, ignored_channels, ignored_users FROM user_highlights WHERE user_id = ? AND server_id = ?", (user_id, server_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0], row[1], row[2], row[3]
                else:
                    return "", "", "", ""

    async def update_user_data(self, user_id, server_id, word_list, ignored_words_list, ignored_channels, ignored_users):
        await self.create_user_table()
        async with aiosqlite.connect("dbs/highlight.db") as db:
            await db.execute("""
                INSERT OR REPLACE INTO user_highlights (user_id, server_id, word_list, ignored_words_list, ignored_channels, ignored_users)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, server_id, word_list, ignored_words_list, ignored_channels, ignored_users))
            await db.commit()

    async def has_permission(self, user, guild):
        config = await self.get_config(guild.id)
        if config:
            admin_roles = config.get('admin', '').split(',')
            mod_roles = config.get('moderator', '').split(',')
            helper_roles = config.get('helper', '').split(',')
            user_roles = [str(role.id) for role in user.roles]
            if any(role in user_roles for role in admin_roles + mod_roles + helper_roles):
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

    @commands.hybrid_group(name="highlight", with_app_command=True, description="Highlight commands")
    async def highlight_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `/highlight help` for information on using highlight commands.")

    @highlight_group.command(name="defaults", description="Add default words to your highlight list")
    async def defaults(self, ctx):
        if not await self.has_permission(ctx.author, ctx.guild):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True)
            return
        default_words = {"bad", "dumb", "mean", "stupid", "weird", "gross", "nasty"}
        await self.create_user_table()
        word_list, ignored_words_list, ignored_channels, ignored_users = await self.get_user_data(ctx.author.id, ctx.guild.id)
        existing_words = set(word_list.split(',')) if word_list else set()
        if default_words.issubset(existing_words):
            await ctx.send("Those words are already in your list!", ephemeral=True)
        else:
            updated_words = existing_words.union(default_words)
            await self.update_user_data(ctx.author.id, ctx.guild.id, ','.join(updated_words), ignored_words_list, ignored_channels, ignored_users)
            await ctx.send("Added default words to your highlight list!", ephemeral=True)

    @highlight_group.command(name="add", description="Add a word to your highlight list")
    async def add(self, ctx, word: str):
        if not await self.has_permission(ctx.author, ctx.guild):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True)
            return
        word = word.lower()
        await self.create_user_table()
        word_list, ignored_words_list, ignored_channels, ignored_users = await self.get_user_data(ctx.author.id, ctx.guild.id)
        words = word_list.split(',') if word_list else []
        if word not in words:
            words.append(word)
            await self.update_user_data(ctx.author.id, ctx.guild.id, ','.join(words), ignored_words_list, ignored_channels, ignored_users)
            await ctx.send(f"Added **{word}** to your highlight list!", ephemeral=True)
        else:
            await ctx.send(f"`**{word}**` is already in your highlight list!", ephemeral=True)

    @highlight_group.command(name="remove", description="Remove a word from your highlight list")
    async def remove(self, ctx, word: str):
        if not await self.has_permission(ctx.author, ctx.guild):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True)
            return
        word = word.lower()
        await self.create_user_table()
        word_list, ignored_words_list, ignored_channels, ignored_users = await self.get_user_data(ctx.author.id, ctx.guild.id)
        words = word_list.split(',') if word_list else []
        if word in words:
            words.remove(word)
            await self.update_user_data(ctx.author.id, ctx.guild.id, ','.join(words), ignored_words_list, ignored_channels, ignored_users)
            await ctx.send(f"Removed **{word}** from your highlight list!", ephemeral=True)
        else:
            await ctx.send(f"`**{word}**` is not in your highlight list!", ephemeral=True)

    @highlight_group.command(name="clear", description="Clear your highlighted word list")
    async def clear(self, ctx):
        if not await self.has_permission(ctx.author, ctx.guild):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True)
            return
        await self.create_user_table()
        _, ignored_words_list, ignored_channels, ignored_users = await self.get_user_data(ctx.author.id, ctx.guild.id)
        await self.update_user_data(ctx.author.id, ctx.guild.id, "", ignored_words_list, ignored_channels, ignored_users)
        await ctx.send("Cleared your highlight list.", ephemeral=True)

    @highlight_group.command(name="ignore", description="Add a word to your ignore list")
    async def ignore(self, ctx, word: str):
        if not await self.has_permission(ctx.author, ctx.guild):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True)
            return
        word = word.lower()
        await self.create_user_table()
        word_list, ignored_words_list, ignored_channels, ignored_users = await self.get_user_data(ctx.author.id, ctx.guild.id)
        ignored_words = ignored_words_list.split(',') if ignored_words_list else []
        if word not in ignored_words:
            ignored_words.append(word)
            await self.update_user_data(ctx.author.id, ctx.guild.id, word_list, ','.join(ignored_words), ignored_channels, ignored_users)
            await ctx.send(f"Added **{word}** to your ignore list!", ephemeral=True)
        else:
            await ctx.send(f"**{word}** is alread in your ignore list!", ephemeral=True)

    @highlight_group.command(name="unignore", description="Remove a word from your ignore list")
    async def unignore(self, ctx, word: str):
        if not await self.has_permission(ctx.author, ctx.guild):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True)
            return
        word = word.lower()
        await self.create_user_table()
        word_list, ignored_words_list, ignored_channels, ignored_users = await self.get_user_data(ctx.author.id, ctx.guild.id)
        ignored_words = ignored_words_list.split(',') if ignored_words_list else []
        if word in ignored_words:
            ignored_words.remove(word)
            await self.update_user_data(ctx.author.id, ctx.guild.id, word_list, ','.join(ignored_words), ignored_channels, ignored_users)
            await ctx.send(f"Removed **{word}** from your ignore list!", ephemeral=True)
        else:
            await ctx.send(f"**{word}** is not ignored in your highlight list!", ephemeral=True)

    @highlight_group.command(name="block", description="Block a user or channel from your highlight list")
    async def block(self, ctx, item: str):
        if not await self.has_permission(ctx.author, ctx.guild):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True)
            return
        id_match = re.search(r'\d+', item)
        if id_match:
            item_id = int(id_match.group(0))
            channel = self.bot.get_channel(item_id)
            user = self.bot.get_user(item_id)
            if channel or user:
                await self.create_user_table()
                word_list, ignored_words_list, ignored_channels, ignored_users = await self.get_user_data(ctx.author.id, ctx.guild.id)
                if channel:
                    ignored_channels_list = ignored_channels.split(',') if ignored_channels else []
                    if str(item_id) not in ignored_channels_list:
                        ignored_channels_list.append(str(item_id))
                        await self.update_user_data(ctx.author.id, ctx.guild.id, word_list, ignored_words_list, ','.join(ignored_channels_list), ignored_users)
                        await ctx.send(f"Blocked channel <#{item_id}>!", ephemeral=True)
                    else:
                        await ctx.send(f"Channel <#{item_id}> is already blocked!", ephemeral=True)
                elif user:
                    ignored_users_list = ignored_users.split(',') if ignored_users else []
                    if str(item_id) not in ignored_users_list:
                        ignored_users_list.append(str(item_id))
                        await self.update_user_data(ctx.author.id, ctx.guild.id, word_list, ignored_words_list, ignored_channels, ','.join(ignored_users_list))
                        await ctx.send(f"Blocked user <@{item_id}>!", ephemeral=True)
                    else:
                        await ctx.send(f"User <@{item_id}> is already blocked!", ephemeral=True)
            else:
                await ctx.send("Invalid user or channel mention.", ephemeral=True)
        else:
            await ctx.send("Invalid user or channel mention.", ephemeral=True)

    @highlight_group.command(name="unblock", description="Unblock a user or channel from your highlight list")
    async def unblock(self, ctx, item: str):
        if not await self.has_permission(ctx.author, ctx.guild):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True)
            return
        id_match = re.search(r'\d+', item)
        if id_match:
            item_id = int(id_match.group(0))
            channel = self.bot.get_channel(item_id)
            user = self.bot.get_user(item_id)
            if channel or user:
                await self.create_user_table()
                word_list, ignored_words_list, ignored_channels, ignored_users = await self.get_user_data(ctx.author.id, ctx.guild.id)
                if channel:
                    ignored_channels_list = ignored_channels.split(',') if ignored_channels else []
                    if str(item_id) in ignored_channels_list:
                        ignored_channels_list.remove(str(item_id))
                        await self.update_user_data(ctx.author.id, ctx.guild.id, word_list, ignored_words_list, ','.join(ignored_channels_list), ignored_users)
                        await ctx.send(f"Unblocked channel <#{item_id}>!", ephemeral=True)
                    else:
                        await ctx.send(f"Channel `<#{item_id}>` is not blocked!", ephemeral=True)
                elif user:
                    ignored_users_list = ignored_users.split(',') if ignored_users else []
                    if str(item_id) in ignored_users_list:
                        ignored_users_list.remove(str(item_id))
                        await self.update_user_data(ctx.author.id, ctx.guild.id, word_list, ignored_words_list, ignored_channels, ','.join(ignored_users_list))
                        await ctx.send(f"Unblocked user <@{item_id}>!", ephemeral=True)
                    else:
                        await ctx.send(f"User <@{item_id}> is not blocked!", ephemeral=True)
            else:
                await ctx.send("Invalid user or channel mention.", ephemeral=True)
        else:
            await ctx.send("Invalid user or channel mention.", ephemeral=True)

    @highlight_group.command(name="show", description="Show your highlight list")
    async def show(self, ctx):
        if not await self.has_permission(ctx.author, ctx.guild):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True)
            return
        await self.create_user_table()
        word_list, ignored_words_list, ignored_channels, ignored_users = await self.get_user_data(ctx.author.id, ctx.guild.id)
        words = word_list.split(',') if word_list else []
        ignored_words = ignored_words_list.split(',') if ignored_words_list else []
        channels = ignored_channels.split(',') if ignored_channels else []
        users = ignored_users.split(',') if ignored_users else []
        user = self.bot.get_user(ctx.author.id)
        username = user.name if user else "Unknown User"
        e = discord.Embed(title=f"🔍 {username}'s Highlight List 🔍", color=commie_color)
        e.add_field(name="📑 Highlighted Words", value='\n'.join([f"> - {word}" for word in words]) if words else "None", inline=False)
        e.add_field(name="🚫 Ignored Words", value='\n'.join([f"> - {word}" for word in ignored_words]) if ignored_words else "None", inline=False)
        e.add_field(name="📰 Blocked Channels", value='\n'.join([f"> - <#{channel}>" for channel in channels]) if channels else "None", inline=False)
        e.add_field(name="👤 Blocked Users", value='\n'.join([f"> - <@{user}>" for user in users]) if users else "None", inline=False)
        await ctx.send(embed=e, ephemeral=True)

    @highlight_group.command(name="help", description="Shows the highlight help menu")
    async def help(self, ctx):
        try:
            if not await self.has_permission(ctx.author, ctx.guild):
                await ctx.send("You don't have the required permissions for this command!", ephemeral=True)
                return
            e = discord.Embed(title=f"⚙️ Highlight Help ⚙️", color=commie_color)
            e.description = "Here are the available public commands for managing highlights. \n### ❓ What does Highlights do ❓ \n'Highlight' commands help with moderation! Each time a word in your 'highlight list' is mentioned, it will **DM** you with information about the user and a link to the message! \n\n### 📌 Highlight Commands 📌 \n> ⚙️ **Highlight help** **|** `highlight help` **|** Sends the Highlight Help Menu \n> 📑 **Highlight defaults** **|** `highlight defaults` **|** Adds a default list of slurs to your highlight list \n> ➕ **Highlight add** **|** `highlight add [word]` **|** Adds a word to your highlight list \n> ➖ **Highlight remove** **|** `highlight remove [word]` **|** Removes a word from your highlight list \n> ♻️ **Highlight clear** **|** `highlight clear` **|** Clears your highlight list \n> 🔕 **Highlight ignore** **|** `highlight ignore [word]` **|** Ignores part of a word in your highlight list **Ex:** You won't get DM'd when someone says 'hit' if you have '**hi**' in your highlight list \n> 🔔 **Highlight unignore** **|** `highlight unignore [word]` **|** Unignores part of a word in your highlight list \n> ❌ **Highlight block** **|** `highlight block [item]` **|** [`item` can either be a channel mention or user mention], when a user or channel is 'blocked' you won't get DM'd when they say a word in your highlight list \n> ✅ **Highlight unblock** **|** `highlight unblock [item]` **|** Unblocks a user or channel you had blocked [`item` can either be a channel mention or user mention]\n> 📰 **Highlight show** **|** `highlight show` **|** Shows all the information about your highlight list"
            await ctx.send(embed=e, ephemeral=True)
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        async with aiosqlite.connect("dbs/highlight.db") as db:
            async with db.execute("SELECT user_id FROM user_highlights WHERE server_id = ?", (message.guild.id,)) as cursor:
                user_ids = await cursor.fetchall()
        for user_id in user_ids:
            user_id = user_id[0]
            word_list, ignored_words_list, ignored_channels, ignored_users = await self.get_user_data(user_id, message.guild.id)
            words = word_list.split(',') if word_list else []
            ignored_words = ignored_words_list.split(',') if ignored_words_list else []
            ignored_channel_ids = [int(cid) for cid in ignored_channels.split(',')] if ignored_channels else []
            ignored_user_ids = [int(uid) for uid in ignored_users.split(',')] if ignored_users else []
            if message.channel.id in ignored_channel_ids or message.author.id in ignored_user_ids:
                continue
            if message.author.id == user_id:
                continue
            user = self.bot.get_user(user_id)
            if f"<@{user_id}>" in message.content:
                continue
            content = message.clean_content.lower()
            for word in words:
                if word in content and not any(ignored_word in content for ignored_word in ignored_words):
                    if user:
                        e = discord.Embed(
                            title=f"🚨 Word Mentioned 🚨",
                            color=commie_color,
                            timestamp=datetime.utcnow()
                        )
                        e.set_author(name=message.guild.name, icon_url=message.guild.icon.url)
                        e.set_thumbnail(url=message.author.avatar.url)
                        e.add_field(name="🔍 Mentioned Word", value=f"> {word}", inline=False)
                        e.add_field(name="💬 Message", value=f"> {message.clean_content}", inline=False)
                        e.add_field(name="👤 Mentioned By", value=f"> {message.author.mention}", inline=False)
                        e.add_field(name="📢 In Channel", value=f"> {message.channel.mention}", inline=False)
                        e.add_field(name="🔗 Jump Link", value=f"> [Message]({message.jump_url})", inline=False)
                        await user.send(embed=e)
                    break

async def setup(bot):
    await bot.add_cog(HighlightCog(bot))
