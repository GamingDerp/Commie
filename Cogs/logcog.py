import discord
from discord.ext import commands
from datetime import datetime
import aiosqlite

commie_logo = "https://media.discordapp.net/attachments/1257979868784758854/1258026914816331807/CommieLogo.png?ex=66868c5d&is=66853add&hm=36c6a57e62eca6ec2954f76efc6d20add7ea2ab786380aab1f1994e55513ef05&=&format=webp&quality=lossless"
commie_color = 0xd40001

class LogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_logging_channel(self, guild_id):
        if guild_id is None:
            return None
        try:
            async with aiosqlite.connect("dbs/configs.db") as db:
                async with db.execute("SELECT logging_channel, toggle_logging FROM server_configs WHERE server_id = ?", (guild_id,)) as cursor:
                    result = await cursor.fetchone()
                    if result and result[1]:
                        return result[0]
        except Exception as e:
            print(f"Error getting logging channel for guild {guild_id}: {e}")
        return None

    async def log_event(self, guild, embed):
        if guild is None or guild.id is None:
            return
        logging_channel_id = await self.get_logging_channel(guild.id)
        if logging_channel_id:
            channel = self.bot.get_channel(logging_channel_id)
            if channel:
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        try:
            if message.author.bot:
                return
            if message.guild is None:
                return
            guild_id = message.guild.id
            if not guild_id:
                return
            logging_channel = await self.get_logging_channel(guild_id)
            if logging_channel is None:
                return
            channel = self.bot.get_channel(logging_channel)
            if channel is None:
                return
            e = discord.Embed(color=0xff0000)
            e.set_author(name="🗑️ Message Deleted")
            if message.author and message.author.avatar:
                e.set_thumbnail(url=f"{message.author.avatar.url}")
            author_type = "**bot**" if message.author.bot else "**user**"
            e.description = f"A message by a {author_type}, {message.author.mention}, was deleted \n<:ChainReply:1259287285845725214> In <#{message.channel.id}> \n<:Reply:1259287286814740541> **ID:** {message.id}"
            if message.content:
                e.add_field(name="Content", value=f"> {message.content}", inline=False)
            if message.attachments:
                attachment_url = message.attachments[0].url
                e.set_image(url=attachment_url)
            e.timestamp = datetime.utcnow()
            await channel.send(embed=e)
        except AttributeError as attr_err:
            print(f"AttributeError in on_message_delete: {attr_err}")
        except Exception as error:
            print(f"Error in on_message_delete: {error}")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        try:
            if before.author.bot:
                return
            if before.guild is None or after.guild is None:
                return
            guild_id = before.guild.id
            if not guild_id:
                return
            logging_channel = await self.get_logging_channel(guild_id)
            if logging_channel is None:
                return
            channel = self.bot.get_channel(logging_channel)
            if channel is None:
                return
            e = discord.Embed(color=0xffc200)
            e.set_author(name="📝 Message Edited")
            if before.author and before.author.avatar:
                e.set_thumbnail(url=f"{before.author.avatar.url}")
            author_type = "**bot**" if before.author.bot else "**user**"
            e.description = f"A {author_type}, {before.author.mention}, edited their message \n<:ChainReply:1259287285845725214> In <#{before.channel.id}> \n<:ChainReply:1259287285845725214> **ID:** {before.id} \n<:Reply:1259287286814740541> [**Jump to Message**]({after.jump_url})"
            e.add_field(name="__Before__", value=f"> {before.content if before.content else 'No content'}")
            e.add_field(name="__After__", value=f"> {after.content if after.content else 'No content'}", inline=False)
            e.timestamp = datetime.utcnow()
            await channel.send(embed=e)
        except AttributeError:
            pass
        except Exception as error:
            print(f"Error in on_message_edit: {error}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        e = discord.Embed(color=0x00ff06)
        e.set_author(name="📈 Member Joined")
        if member.avatar:
            e.set_thumbnail(url=member.avatar.url)
        e.add_field(name="__Member__", value=f"> {member.mention}")
        e.timestamp = datetime.utcnow()
        await self.log_event(member.guild, e)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        e = discord.Embed(color=0xff0000)
        e.set_author(name="📉 Member Left")
        if member.avatar:
            e.set_thumbnail(url=member.avatar.url)
        e.add_field(name="__Member__", value=f"> {member.mention}")
        e.timestamp = datetime.utcnow()
        await self.log_event(member.guild, e)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, member):
        logging_channel = await self.get_logging_channel(guild.id)
        if logging_channel:
            logs = [log async for log in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban)]
            logs = logs[0]
            e = discord.Embed(color=0xff0000)
            e.set_author(name="<:BanHammer:1259651231127965716> Member Banned")
            if member.avatar:
                e.set_thumbnail(url=member.avatar.url)
            e.add_field(name="__Member__", value=f"> {member.mention}")
            e.add_field(name="__Ban Reason__", value=f"> {logs.reason}", inline=False)
            e.add_field(name="__Staff Member__", value=f"> {logs.user.mention}", inline=False)
            e.timestamp = datetime.utcnow()
            await self.log_event(guild, e)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, member):
        e = discord.Embed(color=0x00ff06)
        e.set_author(name="⚖️ Member Unbanned")
        if member.avatar:
            e.set_thumbnail(url=member.avatar.url)
        e.add_field(name="__Member__", value=f"> {member.mention}")
        e.timestamp = datetime.utcnow()
        await self.log_event(guild, e)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        e = None
        if len(before.roles) > len(after.roles):
            droles = next(droles for droles in before.roles if droles not in after.roles)
            e = discord.Embed(color=0xff0000)
            e.set_author(name="🧮 Role Update")
            if before.avatar:
                e.set_thumbnail(url=before.avatar.url)
            e.add_field(name="__Member__", value=f"> {before.mention}")
            e.add_field(name="__Role__", value=f"> ❌ {droles}", inline=False)
        elif len(before.roles) < len(after.roles):
            aroles = next(aroles for aroles in after.roles if aroles not in before.roles)
            e = discord.Embed(color=0x00ff06)
            e.set_author(name="🧮 Role Update")
            if before.avatar:
                e.set_thumbnail(url=before.avatar.url)
            e.add_field(name="__Member__", value=f"> {before.mention}")
            e.add_field(name="__Role__", value=f"> ✅ {aroles}", inline=False)
        if before.display_name != after.display_name:
            e = discord.Embed(color=0xffc200)
            e.set_author(name="🧾 Nickname Update")
            if before.avatar:
                e.set_thumbnail(url=before.avatar.url)
            e.add_field(name="__Member__", value=f"> {before.mention}")
            e.add_field(name="__Before__", value=f"> {before.display_name}", inline=False)
            e.add_field(name="__After__", value=f"> {after.display_name}", inline=False)
        if e:
            e.timestamp = datetime.utcnow()
            await self.log_event(before.guild, e)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        e = discord.Embed(color=0x00ff06)
        e.set_author(name="📥 Channel Created")
        e.add_field(name="__Name__", value=f"> {channel.name}")
        e.add_field(name="__Mention__", value=f"> {channel.mention}", inline=False)
        e.add_field(name="__Channel ID__", value=f"> {channel.id}", inline=False)
        e.timestamp = datetime.utcnow()
        await self.log_event(channel.guild, e)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        e = discord.Embed(color=0xff0000)
        e.set_author(name="📤 Channel Deleted")
        e.add_field(name="__Name__", value=f"> {channel.name}")
        e.add_field(name="__Mention__", value=f"> {channel.mention}", inline=False)
        e.add_field(name="__Channel ID__", value=f"> {channel.id}", inline=False)
        e.timestamp = datetime.utcnow()
        await self.log_event(channel.guild, e)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        e = None
        if before.channel and after.channel and before.channel != after.channel:
            e = discord.Embed(color=0xffc200)
            e.set_author(name="🔊 Moved VC's")
            e.add_field(name="__User__", value=f"> {member.mention}")
            e.add_field(name="__Moved From__", value=f"> {before.channel.name}", inline=False)
            e.add_field(name="__Moved To__", value=f"> {after.channel.name}", inline=False)
        elif before.channel and not after.channel:
            e = discord.Embed(color=0xff0000)
            e.set_author(name="🔊 Left VC")
            e.add_field(name="__User__", value=f"> {member.mention}")
            e.add_field(name="__Left__", value=f"> {before.channel.name}", inline=False)
        elif not before.channel and after.channel:
            e = discord.Embed(color=0x00ff06)
            e.set_author(name="🔊 Joined VC")
            e.add_field(name="__User__", value=f"> {member.mention}")
            e.add_field(name="__Joined__", value=f"> {after.channel.name}", inline=False)
        if e:
            e.timestamp = datetime.utcnow()
            await self.log_event(member.guild, e)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        e = discord.Embed(color=0x00ff06)
        e.set_author(name="🎭 Role Created")
        e.add_field(name="__Role Mention__", value=f"> {role.mention}")
        e.add_field(name="__Role Name__", value=f"> {role.name}", inline=False)
        e.add_field(name="__Role ID__", value=f"> {role.id}", inline=False)
        e.timestamp = datetime.utcnow()
        await self.log_event(role.guild, e)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        e = discord.Embed(color=0xff0000)
        e.set_author(name="🎭 Role Deleted")
        e.add_field(name="__Role Mention__", value=f"> {role.mention}")
        e.add_field(name="__Role Name__", value=f"> {role.name}", inline=False)
        e.add_field(name="__Role ID__", value=f"> {role.id}", inline=False)
        e.timestamp = datetime.utcnow()
        await self.log_event(role.guild, e)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        e = None
        if before.name != after.name:
            e = discord.Embed(color=0xffc200)
            e.set_author(name="🎭 Role Update")
            e.add_field(name="__Before__", value=f"> {before.name}")
            e.add_field(name="__After__", value=f"> {after.name}", inline=False)
            e.add_field(name="__Role ID__", value=f"> {after.id}", inline=False)
            e.add_field(name="__Role Mention__", value=f"> {after.mention}")
        if before.color != after.color:
            e = discord.Embed(color=0xffc200)
            e.set_author(name="🎭 Role Update")
            e.add_field(name="__Before__", value=f"> {before.color}")
            e.add_field(name="__After__", value=f"> {after.color}", inline=False)
            e.add_field(name="__Role ID__", value=f"> {after.id}", inline=False)
            e.add_field(name="__Role Mention__", value=f"> {after.mention}")
        if e:
            e.timestamp = datetime.utcnow()
            await self.log_event(before.guild, e)

async def setup(bot):
    await bot.add_cog(LogCog(bot))