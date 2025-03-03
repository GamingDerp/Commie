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

    async def has_moderator_role(self, user, guild_id):
        return await self.has_role(user, guild_id, "moderator")

    @commands.hybrid_command(description="Start a giveaway | s, m, h, d")
    async def giveaway(self, ctx, time, *, prize: str):
        if not await self.has_moderator_role(ctx.author, ctx.guild.id):
            await ctx.send("You don't have the required permissions for this command!", ephemeral=True, delete_after=10)
            return
        converted_duration = self.convert_duration(time)
        if converted_duration == -1:
            await ctx.send("Invalid duration format! Please use **s**, **m**, **h**, or **d**.", ephemeral=True)
            return
        e = discord.Embed(
            title="🎉 Giveaway 🎉",
            color=commie_color
        )
        e.add_field(name="Time", value=f"⏰ {time}", inline=False)
        e.add_field(name="Prize", value=f"🎁 {prize}", inline=False)
        e.add_field(name="Entries", value=f"📬 0", inline=False)
        join_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary, 
            label="📮 Join", 
            custom_id=f"join_{ctx.channel.id}_{ctx.message.id}"
        )
        view = discord.ui.View()
        view.add_item(join_button)
        giveaway_message = await ctx.send(embed=e, view=view)
        giveaway_key = (ctx.guild.id, giveaway_message.id)
        self.participants[giveaway_key] = []
        await asyncio.sleep(converted_duration.total_seconds())
        if not self.participants[giveaway_key]:
            await ctx.send("No participants in the giveaway.")
        else:
            winner = random.choice(self.participants[giveaway_key])
            winner_text = f"<@{winner}>"
            winners_embed = discord.Embed(
                title="🎉 Giveaway Results 🎉",
                description=f"**🎁 Prize:** {prize}\n**👑 Winner:** {winner_text}",
                color=commie_color
            )
            await ctx.send(embed=winners_embed)
        try:
            original_message = await ctx.channel.fetch_message(giveaway_message.id)
            disabled_view = discord.ui.View()
            disabled_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary, 
                label="📮 Join", 
                custom_id=f"join_{ctx.channel.id}_{giveaway_message.id}",
                disabled=True
            )
            disabled_view.add_item(disabled_button)
            await original_message.edit(view=disabled_view)
        except discord.NotFound:
            print("Giveaway message not found! It may have been deleted.")
        except discord.HTTPException as e:
            print(f"Failed to edit giveaway message: {e}")
        self.participants[giveaway_key] = self.participants.get(giveaway_key, [])

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        try:
            if interaction.type == discord.InteractionType.component and interaction.data['custom_id'].startswith("join"):
                giveaway_key = (interaction.guild.id, interaction.message.id)
                try:
                    giveaway_message = await interaction.channel.fetch_message(interaction.message.id)
                    if giveaway_message.components:
                        button_disabled = giveaway_message.components[0].children[0].disabled
                        if button_disabled:
                            await interaction.response.send_message("This giveaway has ended!", ephemeral=True)
                            return
                except discord.NotFound:
                    await interaction.response.send_message("This giveaway has ended!", ephemeral=True)
                    return
                if giveaway_key not in self.participants:
                    await interaction.response.send_message("This giveaway has ended!", ephemeral=True)
                    return
                user = interaction.user
                if not self.has_joined(user, giveaway_key):
                    self.participants[giveaway_key].append(user.id)
                    entries = len(self.participants[giveaway_key])
                    e = interaction.message.embeds[0]
                    e.set_field_at(2, name="Entries", value=f"📬 {entries}", inline=False)
                    await interaction.message.edit(embed=e)
                    e = discord.Embed(color=commie_color)
                    e.title = "🎉 Giveaway Joined! 🎉"
                    e.description = "You joined the giveaway!"
                    await interaction.response.send_message(embed=e, ephemeral=True)
                else:
                    self.participants[giveaway_key].remove(user.id)
                    entries = len(self.participants[giveaway_key])
                    e = interaction.message.embeds[0]
                    e.set_field_at(2, name="Entries", value=f"📬 {entries}", inline=False)
                    await interaction.message.edit(embed=e)
                    e = discord.Embed(color=commie_color)
                    e.title = "🎉 Giveaway Left! 🎉"
                    e.description = "You left the giveaway!"
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
            last_giveaway_key = max(
                (key for key in self.participants if key[0] == ctx.guild.id),
                default=None
            )
            if last_giveaway_key is None:
                await ctx.send("No giveaway has been conducted yet.", ephemeral=True)
                return
            last_winners = self.participants.get(last_giveaway_key, [])
            if not last_winners:
                await ctx.send("No participants in the last giveaway.", ephemeral=True)
                return
            try:
                last_giveaway_message = await ctx.channel.fetch_message(last_giveaway_key[1])
            except discord.NotFound:
                await ctx.send("The last giveaway message was deleted, cannot reroll.", ephemeral=True)
                return
            try:
                prize_field = last_giveaway_message.embeds[0].fields[1].value
            except (IndexError, AttributeError):
                prize_field = "Unknown Prize"
            rerolled_winner = random.choice(last_winners)
            winner_text = f"<@{rerolled_winner}>"
            winners_embed = discord.Embed(
                title="🎉 Giveaway Results (Reroll) 🎉",
                description=f"**🎁 Prize:** {prize_field}\n**👑 New Winner:** {winner_text}",
                color=commie_color
            )
            await ctx.send(embed=winners_embed)
        except Exception as e:
            print(f"Error in reroll: {e}")

async def setup(bot):
    await bot.add_cog(GiveawayCog(bot))
