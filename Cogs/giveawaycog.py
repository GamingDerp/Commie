import os
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random
import asyncio
import aiosqlite

commie_logo = "https://media.discordapp.net/attachments/1257979868784758854/1258026914816331807/CommieLogo.png?ex=66868c5d&is=66853add&hm=36c6a57e62eca6ec2954f76efc6d20add7ea2ab786380aab1f1994e55513ef05&=&format=webp&quality=lossless"
commie_color = 0xd40001

class GiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.participants = {}

    def has_joined(self, user, giveaway_id):
        return user.id in self.participants.get(giveaway_id, [])

    async def has_moderator_role(self, user, guild_id):
        async with aiosqlite.connect("dbs/staff.db") as db:
            async with db.execute("SELECT moderator_roles, admin_roles FROM staffroles WHERE server_id = ?", (guild_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    moderator_roles = row[0].split(',')
                    admin_roles = row[1].split(',')
                    user_roles = [role.id for role in user.roles]
                    if any(int(role) in user_roles for role in moderator_roles + admin_roles):
                        return True
        return False

    @commands.hybrid_command(description="Start a giveaway | s, m, h, d")
    async def giveaway(self, ctx, time, *, prize: str):
        if not await self.has_moderator_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        converted_duration = self.convert_duration(time)
        if converted_duration == -1:
            await ctx.send("Invalid duration format! Please use **s**, **m**, **h**, or **d**.")
            return
        end_time = datetime.utcnow() + converted_duration
        e = discord.Embed(
            title="🎉 Giveaway 🎉",
            color=commie_color
        )
        e.add_field(
            name="Time",
            value=f"⏰ {time}",
            inline=False
        )
        e.add_field(
            name="Prize",
            value=f"🎁 {prize}",
            inline=False
        )
        e.add_field(
            name="Entries",
            value=f"📬 0",
            inline=False
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label="📮 Join", custom_id="join"))
        message = await ctx.send(embed=e, view=view)
        await asyncio.sleep(converted_duration.total_seconds())
        giveaway_key = (ctx.guild.id, message.id)
        if giveaway_key not in self.participants:
            await ctx.send("No participants in the giveaway.")
            return
        winner = random.choice(self.participants[giveaway_key])
        winner_text = f"<@{winner}>"
        winners_embed = discord.Embed(
            title="🎉 Giveaway Results 🎉",
            description=f"**🎁 Prize:** {prize}\n**👑 Winner:** {winner_text}",
            color=commie_color
        )
        await ctx.send(embed=winners_embed)
        view.clear_items()
        await message.edit(view=view)
        del self.participants[giveaway_key]

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        try:
            if interaction.type == discord.InteractionType.component:
                if interaction.data['custom_id'] == 'join':
                    user = interaction.user
                    giveaway_key = (interaction.guild.id, interaction.message.id)
                    if giveaway_key not in self.participants:
                        self.participants[giveaway_key] = []
                    if not self.has_joined(user, giveaway_key):
                        self.participants[giveaway_key].append(user.id)
                        entries = len(self.participants.get(giveaway_key, []))
                        e = interaction.message.embeds[0]
                        e.set_field_at(2, name="Entries", value=f"📬 {entries}", inline=False)
                        await interaction.message.edit(embed=e)
                        e = discord.Embed(color=commie_color)
                        e.title = f"🎉 Giveaway Joined! 🎉"
                        e.description = f"You joined the giveaway!"
                        await interaction.response.send_message(embed=e, ephemeral=True)
                    else:
                        self.participants[giveaway_key].remove(user.id)
                        entries = len(self.participants.get(giveaway_key, []))
                        e = interaction.message.embeds[0]
                        e.set_field_at(2, name="Entries", value=f"📬 {entries}", inline=False)
                        await interaction.message.edit(embed=e)
                        e = discord.Embed(color=commie_color)
                        e.title = f"🎉 Giveaway Left! 🎉"
                        e.description = f"You left the giveaway!"
                        await interaction.response.send_message(embed=e, ephemeral=True)
        except Exception as e:
            print(e)

    def convert_duration(self, duration):
        pos = ['s', 'm', 'h', 'd']
        time_dict = {"s": 1, "m": 60, "h": 3600, "d": 3600 * 24}
        unit = duration[-1]
        if unit not in pos:
            return -1
        try:
            val = int(duration[:-1])
        except ValueError:
            return -1
        return timedelta(seconds=val * time_dict[unit])

    @commands.hybrid_command(description="Reroll the winner of the last giveaway")
    async def reroll(self, ctx):
        if not await self.has_moderator_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return

        try:
            last_giveaway_key = max((key for key in self.participants if key[0] == ctx.guild.id), default=None)
            if last_giveaway_key is not None:
                last_winners = self.participants.get(last_giveaway_key, [])
                last_giveaway_message = await ctx.channel.fetch_message(last_giveaway_key[1])
                if last_winners:
                    prize = last_giveaway_message.embeds[0].fields[1].value
                    rerolled_winner = random.choice(last_winners)
                    winner_text = f"<@{rerolled_winner}>"
                    winners_embed = discord.Embed(
                        title="🎉 Giveaway Results (Reroll) 🎉",
                        description=f"**🎁 Prize:** {prize}\n**👑 Winner:** {winner_text}",
                        color=commie_color
                    )
                    await ctx.send(embed=winners_embed)
                else:
                    await ctx.send("No participants in the last giveaway.", ephemeral=True)
            else:
                await ctx.send("No giveaway has been conducted yet.", ephemeral=True)
        except Exception as e:
            print(e)

async def setup(bot):
    await bot.add_cog(GiveawayCog(bot))