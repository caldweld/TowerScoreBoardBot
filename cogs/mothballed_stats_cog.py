"""
Mothballed StatsCog preserved from cogs/stats_cog.py.
All contents commented out so it does not register commands.
Restore by moving back/renaming and loading in bot.py's main().
"""

# import discord
# from discord.ext import commands
# from dashboard_backend.database import SessionLocal
# from dashboard_backend.models import UserStats
# from gemini_processor import process_image
# from gemini_sql_parser import process_gemini_result
# 
# class StatsCog(commands.Cog):
# 	def __init__(self, bot):
# 		self.bot = bot
# 	
# 	def format_stat_value(self, value):
# 		"""Format stat value to add space between number and letter suffix, and compact large numbers with suffixes."""
# 		...
# 	
# 	@commands.command(name="uploadstats", help="Upload your stats screenshot to save your stats.")
# 	async def uploadstats(self, ctx):
# 		...
# 	
# 	@commands.command(name="mystats", help="View your most recently uploaded stats.")
# 	async def mystats(self, ctx):
# 		...
# 
# async def setup(bot):
# 	await bot.add_cog(StatsCog(bot))


