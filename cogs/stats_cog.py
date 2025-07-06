import discord
from discord.ext import commands
from dashboard_backend.database import SessionLocal
from dashboard_backend.models import UserStats
from image_stats import extract_stats_from_image_url

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="uploadstats", help="Upload your stats screenshot to save your stats.")
    async def uploadstats(self, ctx):
        if not ctx.message.attachments:
            await ctx.send("Please attach a screenshot of your stats.")
            return
        attachment = ctx.message.attachments[0]
        try:
            stats = extract_stats_from_image_url(attachment.url)
            session = SessionLocal()
            user_stats = UserStats(
                discordid=str(ctx.author.id),
                discordname=str(ctx.author),
                **{k: stats.get(k) for k in stats if k != 'raw_text'}
            )
            session.add(user_stats)
            session.commit()
            session.close()
            await ctx.send("Your stats have been saved successfully!")
        except Exception as e:
            await ctx.send(f"Failed to process your stats: {e}")

async def setup(bot):
    await bot.add_cog(StatsCog(bot)) 