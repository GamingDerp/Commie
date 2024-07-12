import discord
from discord.ext import commands
import random
import asyncio
        
commie_logo = "https://media.discordapp.net/attachments/1257979868784758854/1258026914816331807/CommieLogo.png?ex=66868c5d&is=66853add&hm=36c6a57e62eca6ec2954f76efc6d20add7ea2ab786380aab1f1994e55513ef05&=&format=webp&quality=lossless"
commie_color = 0xd40001

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(description="Flip a coin")
    async def coinflip(self, ctx):
        choice = ["Heads", "Tails"]
        await ctx.send(f"{random.choice(choice)}!")

    @commands.hybrid_command(description="Ask the bot a question")
    async def ask(self, ctx):
        choice = ["Yes", "No", "Obviously", "Wtf??", "I'm not sure..", "Maybe...?", "Stop asking.", "Find out for yourself, smh", "Perchance"]
        await ctx.send(f"{random.choice(choice)}")

    @commands.hybrid_command(description="Reverse a message")
    async def reverse(self, ctx, *, arg):
        await ctx.send(arg[::-1])

    @commands.hybrid_command(description="Have the bot say a message")
    async def say(self, ctx, *, arg):
        await ctx.send(arg)
        await ctx.message.delete()

    @commands.hybrid_command(description="Give two users a love test")
    async def lovetest(self, ctx, user1: discord.Member, user2: discord.Member):
        love_rate = random.randrange(0, 101)
        if love_rate <= 25:
            emoji = "😓"
            footers = [
                "Yikes!",
                "Better luck next time..",
                "Best to avoid each other..."
            ]
        elif love_rate <= 50:
            emoji = "😬"
            footers = [
                "Could be worse...right?",
                "Not quite there yet!",
                "Maybe just friends?..."
            ]
        elif love_rate <= 75:
            emoji = "🤭"
            footers = [
                "Getting warmer!",
                "There's potential!",
                "You better slide in those DM's ;)"
            ]
        elif love_rate <= 99:
            emoji = "😍"
            footers = [
                "Welcome to the Love Shack!",
                "Almost perfect!",
                "Love is in the air!"
            ]
        else:
            emoji = "💍"
            footers = [
                "So when's the wedding?",
                "Perfect match!",
                "Meant to be!"
            ]
        footer = random.choice(footers)
        e = discord.Embed(color=commie_color)
        e.title = "❤️ Love Test ❤️"
        e.description = f"**{user1.mention}** and **{user2.mention}** are a **{love_rate}%** match! {emoji}"
        e.set_footer(text=footer)
        await ctx.send(embed=e)
    
    @commands.hybrid_command(description="Sends a cute animal picture")
    async def cute(self, ctx):
        e = discord.Embed(color=commie_color)
        e.set_author(name="Cute", icon_url=commie_logo)
        with open("txts/cute.txt") as f:
            cute = f.readlines()
        e.set_image(url=random.choice(cute))
        await ctx.send(embed=e)
    
async def setup(bot):
    await bot.add_cog(FunCog(bot))