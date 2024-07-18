import discord
from discord.ext import commands
import random

commie_logo = "https://media.discordapp.net/attachments/1257979868784758854/1258026914816331807/CommieLogo.png?ex=66868c5d&is=66853add&hm=36c6a57e62eca6ec2954f76efc6d20add7ea2ab786380aab1f1994e55513ef05&=&format=webp&quality=lossless"
commie_color = 0xd40001
owner_id = 532706491438727169

class ActionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
    
    @commands.hybrid_command(description="Bite another user")
    async def bite(self, ctx, user:discord.Member):
        e = discord.Embed(color=commie_color)
        e.description = f"{ctx.author.mention} **bites** {user.mention}!"
        bitegifs = [
            "https://media.discordapp.net/attachments/807071768258805764/1131664029052588122/AnimeBite3.gif", 
            "https://media.discordapp.net/attachments/807071768258805764/1131664029505556561/AnimeBite1.gif", 
            "https://media.discordapp.net/attachments/807071768258805764/1131664029929189516/AnimeBite2.gif"
        ]
        e.set_image(url=random.choice(bitegifs)),
        await ctx.send(embed=e)
    
    @commands.hybrid_command(description="Bonk another user")
    async def bonk(self, ctx, user:discord.Member):
        e = discord.Embed(color=commie_color)
        e.description = f"{ctx.author.mention} **bonks** {user.mention}!"
        bonkgifs = [
            "https://media.discordapp.net/attachments/807071768258805764/1109240042238513233/BonkGif.gif",
            "https://media.discordapp.net/attachments/807071768258805764/1124387823076769863/Bonk2Gif.gif"
        ]
        e.set_image(url=random.choice(bonkgifs)),
        await ctx.send(embed=e)

    @commands.hybrid_command(description="Slap another user")
    async def slap(self, ctx, user:discord.Member):
        e = discord.Embed(color=commie_color)
        e.description = f"{ctx.author.mention} **slaps** {user.mention}!"
        e.set_image(url="https://media.discordapp.net/attachments/807071768258805764/1106847432907685928/AnimeSlappingGif.gif")
        await ctx.send(embed=e)
        
    @commands.hybrid_command(description="Punch another user")
    async def punch(self, ctx, user:discord.Member):
        e = discord.Embed(color=commie_color)
        e.description = f"{ctx.author.mention} **punches** {user.mention}!"
        e.set_image(url="https://media.discordapp.net/attachments/807071768258805764/1131018538577039390/PunchingGif.gif")
        await ctx.send(embed=e)

    @commands.hybrid_command(description="Throw another user")
    async def throw(self, ctx, user:discord.Member):
        e = discord.Embed(color=commie_color)
        e.description = f"{ctx.author.mention} **throws** {user.mention} **off a cliff!**"
        e.set_image(url="https://media.discordapp.net/attachments/807071768258805764/1116579751897878558/ThrowGif.gif")
        await ctx.send(embed=e)
    
    @commands.hybrid_command(description="Punt another user")
    async def punt(self, ctx, user:discord.Member):
        e = discord.Embed(color=commie_color)
        e.description = f"{ctx.author.mention} **punts** {user.mention}!"
        e.set_image(url="https://cdn.discordapp.com/attachments/807071768258805764/1123844694888165417/KickGif.gif")
        await ctx.send(embed=e)

    @commands.hybrid_command(description="Highfive another user")
    async def highfive(self, ctx, user:discord.Member): 
        e = discord.Embed(color=commie_color)
        e.description = f"{ctx.author.mention} **highfives** {user.mention}!"
        e.set_image(url="https://media.discordapp.net/attachments/807071768258805764/1106851182279934072/AnimeHighfiveGif.gif")
        await ctx.send(embed=e)

    @commands.hybrid_command(description="Poke another user")
    async def poke(self, ctx, user:discord.Member):
        e = discord.Embed(color=commie_color)
        e.description = f"{ctx.author.mention} **pokes** {user.mention}!"
        e.set_image(url="https://media.discordapp.net/attachments/807071768258805764/1117137231950401617/PokeGif.gif")
        await ctx.send(embed=e)

    @commands.hybrid_command(description="Pat another user")
    async def pat(self, ctx, user:discord.Member):
        e = discord.Embed(color=commie_color)
        e.description = f"{ctx.author.mention} **pats** {user.mention}!"
        e.set_image(url="https://cdn.discordapp.com/attachments/807071768258805764/1106851615320846386/AnimePatGif.gif")
        await ctx.send(embed=e)

    @commands.hybrid_command(description="Hug another user")
    async def hug(self, ctx, user:discord.Member):  
        e = discord.Embed(color=commie_color)
        e.description = f"{ctx.author.mention} **hugs** {user.mention}!"
        e.set_image(url="https://media.discordapp.net/attachments/807071768258805764/1106847914019536926/AnimeHuggingGif.gif")
        await ctx.send(embed=e)

    @commands.hybrid_command(description="Kiss another user")
    async def kiss(self, ctx, user:discord.Member):
        e = discord.Embed(color=commie_color)
        e.description = f"{ctx.author.mention} **kisses** {user.mention}!"
        e.set_image(url="https://media.discordapp.net/attachments/807071768258805764/1106848342966800404/AnimeKissingGif.gif")
        await ctx.send(embed=e)

    @commands.hybrid_command(description="Cuddle with another user")
    async def cuddle(self, ctx, user:discord.Member): 
        e = discord.Embed(color=commie_color)
        e.description = f"{ctx.author.mention} **cuddles with** {user.mention}!"
        e.set_image(url="https://media.discordapp.net/attachments/807071768258805764/1106848675025666128/AnimeCuddlingGif.gif")
        await ctx.send(embed=e)

async def setup(bot):
    await bot.add_cog(ActionCog(bot))
