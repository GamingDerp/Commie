import os
import discord
import aiosqlite
import asyncio
from discord.ext import commands
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

async def get_prefix(bot, message):
    async with aiosqlite.connect("dbs/prefix.db") as conn:
        async with conn.execute("SELECT prefix FROM prefixes WHERE server_id = ?", (message.guild.id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else "!"

bot = commands.Bot(command_prefix=lambda bot, message: bot.get_prefix(message), intents=intents)
bot.remove_command('help')    

owner_id = 532706491438727169

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Guilds: {len(bot.guilds)}")
    await bot.tree.sync()

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    await load_cogs()
    await bot.start("TOKEN")

@bot.command()
async def reload(ctx, cog_name: str):
    if ctx.author.id == owner_id:
        try:
            await bot.unload_extension(f"cogs.{cog_name}")
            await bot.load_extension(f"cogs.{cog_name}")
            await ctx.send(f"**{cog_name}** has been reloaded successfully!")
        except Exception as e:
            await ctx.send(f"An error occurred while reloading {cog_name}: {e}")
    else:
        await ctx.send("You do not have permission to reload cogs.")

@bot.command()
async def loadcog(ctx, cog_name: str):
    if ctx.author.id == owner_id:
        try:
            await bot.load_extension(f"cogs.{cog_name}")
            await ctx.send(f"**{cog_name}** has been loaded successfully!")
        except Exception as e:
            await ctx.send(f"An error occurred while loading {cog_name}: {e}")
    else:
        await ctx.send("You do not have permission to load cogs.")

@bot.command()
async def unloadcog(ctx, cog_name: str):
    if ctx.author.id == owner_id:
        try:
            await bot.unload_extension(f"cogs.{cog_name}")
            await ctx.send(f"**{cog_name}** has been unloaded successfully!")
        except Exception as e:
            await ctx.send(f"An error occurred while unloading {cog_name}: {e}")
    else:
        await ctx.send("You do not have permission to unload cogs.")

@bot.command()
async def sync(ctx):
    if ctx.author.id == owner_id:
        try:
            await bot.tree.sync()
            await ctx.send("The bot has been synced!")
        except Exception as e:
            await ctx.send(f"An error occurred while syncing: {e}")
    else:
        await ctx.send("You do not have permission to sync the bot.")

asyncio.run(main())
