import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import aiosqlite

commie_logo = "https://media.discordapp.net/attachments/1257979868784758854/1258026914816331807/CommieLogo.png?ex=66868c5d&is=66853add&hm=36c6a57e62eca6ec2954f76efc6d20add7ea2ab786380aab1f1994e55513ef05&=&format=webp&quality=lossless"
commie_color = 0xd40001

class StaffCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_conn = None

    @commands.Cog.listener()
    async def on_ready(self):
        await self.create_warn_table()
        await self.initialize_database()

    async def create_warn_table(self):
        async with aiosqlite.connect("dbs/warnlist.db") as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS warns (
                    server_id INTEGER,
                    user_id INTEGER,
                    warn1 TEXT,
                    warn1_timestamp TEXT,
                    warn2 TEXT,
                    warn2_timestamp TEXT,
                    warn3 TEXT,
                    warn3_timestamp TEXT,
                    warn4 TEXT,
                    warn4_timestamp TEXT,
                    warn5 TEXT,
                    warn5_timestamp TEXT,
                    warn6 TEXT,
                    warn6_timestamp TEXT,
                    warn7 TEXT,
                    warn7_timestamp TEXT,
                    warn8 TEXT,
                    warn8_timestamp TEXT,
                    warn9 TEXT,
                    warn9_timestamp TEXT,
                    warn10 TEXT,
                    warn10_timestamp TEXT,
                    PRIMARY KEY (server_id, user_id)
                )
            ''')
            await db.commit()

    async def get_warns(self, server_id, user_id):
        async with aiosqlite.connect("dbs/warnlist.db") as db:
            cursor = await db.execute("SELECT warn1, warn1_timestamp, warn2, warn2_timestamp, warn3, warn3_timestamp, warn4, warn4_timestamp, warn5, warn5_timestamp, warn6, warn6_timestamp, warn7, warn7_timestamp, warn8, warn8_timestamp, warn9, warn9_timestamp, warn10, warn10_timestamp FROM warns WHERE server_id = ? AND user_id = ?", (server_id, user_id))
            warns = await cursor.fetchone()
            if warns:
                return [(warns[i], warns[i+1]) for i in range(0, len(warns), 2) if warns[i] is not None]
            else:
                return []

    async def add_warn(self, server_id, user_id, reason):
        async with aiosqlite.connect("dbs/warnlist.db") as db:
            warns = await self.get_warns(server_id, user_id)
            if len(warns) < 10:
                column = f"warn{len(warns) + 1}"
                timestamp_column = f"{column}_timestamp"
                timestamp = datetime.utcnow().isoformat()
                await db.execute(f"INSERT OR IGNORE INTO warns (server_id, user_id, {column}, {timestamp_column}) VALUES (?, ?, ?, ?)", (server_id, user_id, reason, timestamp))
                await db.execute(f"UPDATE warns SET {column} = ?, {timestamp_column} = ? WHERE server_id = ? AND user_id = ?", (reason, timestamp, server_id, user_id))
                await db.commit()
                return True
            else:
                return False

    async def delete_warn(self, server_id, user_id, warn_index):
        async with aiosqlite.connect("dbs/warnlist.db") as db:
            warns = await self.get_warns(server_id, user_id)
            if 1 <= warn_index <= len(warns):
                column = f"warn{warn_index}"
                timestamp_column = f"{column}_timestamp"
                reason = warns[warn_index - 1][0]
                await db.execute(f"UPDATE warns SET {column} = NULL, {timestamp_column} = NULL WHERE server_id = ? AND user_id = ?", (server_id, user_id))
                await db.commit()
                return reason
            else:
                return None

    async def initialize_database(self):
        self.db_conn = await aiosqlite.connect("dbs/configs.db")
        if self.db_conn is None:
            print("Database connection failed to initialize.")

    async def get_logging_channel(self, guild_id):
        if self.db_conn is None:
            await self.initialize_database()
        try:
            async with self.db_conn.execute(
                "SELECT logging_channel FROM server_configs WHERE server_id = ?", (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Error fetching logging channel: {e}")
            return None

    async def has_role(self, user, guild_id, role_type):
        async with aiosqlite.connect("dbs/configs.db") as db:
            async with db.execute(f"SELECT admin, moderator, helper FROM server_configs WHERE server_id = ?", (guild_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    roles = {
                        "admin": row[0].split(',') if row[0] else [],
                        "moderator": row[1].split(',') if row[1] else [],
                        "helper": row[2].split(',') if row[2] else []
                    }
                    role_hierarchy = ["helper", "moderator", "admin"]
                    user_roles = [str(role.id) for role in user.roles]
                    for higher_role in role_hierarchy[role_hierarchy.index(role_type):]:
                        if any(role in user_roles for role in roles[higher_role]):
                            return True
        return False

    async def has_admin_role(self, user, guild_id):
        return await self.has_role(user, guild_id, "admin")

    async def has_moderator_role(self, user, guild_id):
        return await self.has_role(user, guild_id, "moderator")

    async def has_helper_role(self, user, guild_id):
        return await self.has_role(user, guild_id, "helper")

    @commands.hybrid_command(description="Purge messages", pass_context=True)
    async def purge(self, ctx, limit: int):
        if not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            await ctx.defer()
            await ctx.channel.purge(limit=limit)
        except Exception as e:
            print(e)

    @commands.hybrid_command(description="Ban a user")
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        if not await self.has_moderator_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            await ctx.defer()
            await member.ban(reason=reason)
            e = discord.Embed(color=commie_color)
            e.title = "<:BanHammer:1281379396275404831> Banned <:BanHammer:1281379396275404831>"
            e.description = f"{member.mention} has been banned! \n\n📝 **Reason:** {reason}"
            await ctx.send(embed=e)
        except Exception as e:
            print(e)

    @commands.hybrid_command(description="Unban a user by ID")
    async def unban(self, ctx, user_id: str):
        if not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            await ctx.defer()
            user_id = int(user_id)
            member = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(member)
            e = discord.Embed(color=commie_color)
            e.title = "⚖️ Unbanned ⚖️"
            e.description = f"{member.mention} has been unbanned!"
            await ctx.send(embed=e)
        except Exception as e:
            print(e)


    @commands.hybrid_command(description="Kick a user")
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        if not await self.has_helper_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            await ctx.defer()
            await member.kick(reason=reason)
            e = discord.Embed(color=commie_color)
            e.title = "🧹 Kicked 🧹"
            e.description = f"{member.mention} has been kicked! \n\n📝 **Reason:** {reason}"
            await ctx.send(embed=e)
            await self.log_action(ctx, "🧹 User Kicked 🧹", member, reason)
        except Exception as e:
            print(e)

    @commands.hybrid_command(description="Put a user in timeout | s, m, h, d")
    async def gulag(self, ctx, member: discord.Member, duration, *, reason=None):
        if not await self.has_helper_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            await ctx.defer()
            time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            unit = duration[-1]
            amount = int(duration[:-1])
            seconds = amount * time_units[unit]
            await member.timeout(timedelta(seconds=seconds), reason=reason)
            e = discord.Embed(color=commie_color)
            e.title = "🔐 Gulag 🔐"
            e.description = f"{member.mention} has been put in the gulag! \n\n📝 **Reason:** {reason} \n⏳ **Duration:** {duration}"
            await ctx.send(embed=e)
            await self.log_action(ctx, "🔐 User Gulag'd 🔐", member, reason, duration)
        except Exception as e:
            print(e)

    @commands.hybrid_command(description="Warn a user")
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        if not await self.has_helper_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            if await self.add_warn(ctx.guild.id, member.id, reason):
                e = discord.Embed(color=commie_color)
                e.title = "⚠️ Warn ⚠️"
                e.description = f"{member.mention} has been warned! \n\n📝 **Reason:** {reason}"
                await ctx.send(embed=e)
                await self.log_action(ctx, "⚠️ User Warned ⚠️", member, reason)
            else:
                await ctx.send("This user has already reached the maximum number of warnings (10).")
        except Exception as e:
            print(e)

    @commands.hybrid_command(description="See a user's warns")
    async def warnlist(self, ctx, member: discord.Member):
        if not await self.has_helper_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            warns = await self.get_warns(ctx.guild.id, member.id)
            if warns:
                e = discord.Embed(color=commie_color)
                e.title = f"📑 {member.name}'s Warn List 📑"
                e.set_thumbnail(url=member.avatar.url)
                user_info = f"🔍 __**User**__ \n{member.mention}\n"
                warn_list_str = "\n\n".join([
                    f"__⚠️ **Warn {index}**__ \n> {warn} \n⏰ <t:{int(datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc).timestamp())}:F>"
                    for index, (warn, timestamp) in enumerate(warns, start=1)
                ])
                e.description = f"{user_info}\n{warn_list_str}"
                await ctx.send(embed=e)
            else:
                await ctx.send(f"No warns found for **{member.name}**.", ephemeral=True)
        except Exception as e:
            print(e)

    @commands.hybrid_command(description="Delete a user's warns")
    async def delwarn(self, ctx, member: discord.Member, warn_number: int):
        if not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            warn_index = warn_number
            warn_reason = await self.delete_warn(ctx.guild.id, member.id, warn_index)
            if warn_reason:
                e = discord.Embed(color=commie_color)
                e.title = "⛔️ Warn Deleted ⛔️"
                e.description = f"Warn **{warn_index}** for {member.mention} has been removed."
                await ctx.send(embed=e, ephemeral=True)
                await self.log_action(ctx, "⛔️ Warn Removed ⛔️", member, warn_reason)
            else:
                await ctx.send("Invalid warn number. Do `delwarn <user> <warn number>`.", ephemeral=True)
        except Exception as e:
            print(e)

    @commands.hybrid_command(description="Clear all warns for a user")
    async def clearwarns(self, ctx, member: discord.Member):
        if not await self.has_admin_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        try:
            async with aiosqlite.connect("dbs/warnlist.db") as db:
                await db.execute('DELETE FROM warns WHERE server_id = ? AND user_id = ?', (ctx.guild.id, member.id))
                await db.commit()
            e = discord.Embed(color=commie_color)
            e.title = "♻️ Warns Cleared ♻️"
            e.description = f"All warns for {member.mention} have been cleared."
            await ctx.send(embed=e, ephemeral=True)
            await self.log_action(ctx, "♻️ All Warns Cleared ♻️", member)
        except Exception as e:
            print(e)

    async def log_action(self, ctx, action, member, reason=None, duration=None):
        try:
            logging_channel_id = await self.get_logging_channel(ctx.guild.id)
            if logging_channel_id:
                channel = self.bot.get_channel(logging_channel_id)
                if channel is None:
                    print(f"Logging channel not found: {logging_channel_id}")
                    return
                e = discord.Embed(color=commie_color)
                e.set_author(name=action)
                e.set_thumbnail(url=member.avatar.url)
                e.add_field(name="__Member__", value=f"> {member.mention}", inline=False)
                if reason:
                    e.add_field(name="__Reason__", value=f"> {reason}", inline=False)
                if duration:
                    e.add_field(name="__Duration__", value=f"> {duration}", inline=False)
                e.add_field(name="__Staff Member__", value=f"> {ctx.author.mention}", inline=False)
                e.timestamp = datetime.utcnow()
                await channel.send(embed=e)
        except discord.Forbidden:
            print(f"Bot does not have permission to send messages in channel {logging_channel_id}")
        except discord.HTTPException as http_err:
            print(f"Failed to send embed due to HTTP exception: {http_err}")
        except Exception as error:
            print(f"Error in log_action: {error}")

async def setup(bot):
    await bot.add_cog(StaffCog(bot))
