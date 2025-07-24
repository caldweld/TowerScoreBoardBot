import discord
from discord.ext import commands
from dashboard_backend.database import SessionLocal
from dashboard_backend.models import UserStats
from gemini_processor import process_image
from gemini_sql_parser import process_gemini_result

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def format_stat_value(self, value):
        """Format stat value to add space between number and letter suffix, and compact large numbers with suffixes."""
        if value is None:
            return 'N/A'
        
        # Try to convert to float for numeric formatting
        try:
            num = float(str(value).replace(',', '').replace('$', '').strip())
        except (ValueError, TypeError):
            # If not a number, try to add space before known suffixes
            suffixes = ['K', 'M', 'B', 'T', 'q', 'Q', 's', 'S', 'O', 'N', 'D', 'aa', 'ab', 'ac', 'ad']
            for suffix in sorted(suffixes, key=len, reverse=True):
                if str(value).endswith(suffix):
                    return str(value)[:-len(suffix)] + ' ' + suffix
            return str(value)
        
        # Compact number formatting
        suffixes = [
            (1e33, 'ad'), (1e30, 'ac'), (1e27, 'ab'), (1e24, 'aa'), (1e21, 'D'), (1e18, 'N'),
            (1e15, 'O'), (1e12, 'S'), (1e9, 's'), (1e6, 'Q'), (1e3, 'q'), (1e12, 'T'), (1e9, 'B'), (1e6, 'M'), (1e3, 'K')
        ]
        # Use the largest suffix that fits
        for factor, suffix in suffixes:
            if abs(num) >= factor:
                val = num / factor
                # Remove trailing .00 for integers, else show 2 decimals
                if val == int(val):
                    val_str = f"{int(val)}"
                else:
                    val_str = f"{val:.2f}"
                return f"{val_str} {suffix}"
        # For numbers < 1000, just show as is (with up to 2 decimals if float)
        if num == int(num):
            return str(int(num))
        else:
            return f"{num:.2f}"

    @commands.command(name="uploadstats", help="Upload your stats screenshot to save your stats.")
    async def uploadstats(self, ctx):
        if not ctx.message.attachments:
            await ctx.send("Please attach a screenshot of your stats.")
            return
        
        attachment = ctx.message.attachments[0]
        
        # Send initial processing message
        processing_msg = await ctx.send("🤖 Processing image with AI... Please wait.")
        
        try:
            # Process image with Gemini
            gemini_result = process_image(attachment.url)
            
            if not gemini_result["success"]:
                await processing_msg.edit(content=f"❌ Failed to process image: {gemini_result.get('error', 'Unknown error')}")
                return
            
            # Check if it's actually a stats image
            if gemini_result["image_type"] != "stats":
                await processing_msg.edit(content=f"❌ This doesn't appear to be a stats screenshot. AI detected: {gemini_result['image_type']} (confidence: {gemini_result['confidence']:.1%})\n\nPlease upload a stats image that contains fields like 'Coins Earned', 'Damage Dealt', 'Enemies Destroyed', etc.")
                return
            
            # Check confidence level
            if gemini_result["confidence"] < 0.7:
                await processing_msg.edit(content=f"⚠️ Low confidence in processing ({gemini_result['confidence']:.1%}). Please ensure the image is clear and contains stats data.")
                return
            
            # Save to database using our SQL parser
            sql_result = process_gemini_result(gemini_result, str(ctx.author.id), str(ctx.author))
            
            if sql_result["success"]:
                await processing_msg.edit(content=f"✅ **Stats saved successfully!**\n\n🎯 **AI Confidence:** {gemini_result['confidence']:.1%}\n📊 **Stats ID:** {sql_result.get('stats_id', 'N/A')}\n\nYour game statistics have been processed and saved to the database.")
            else:
                await processing_msg.edit(content=f"❌ **Database Error:** {sql_result['message']}")
                
        except Exception as e:
            await processing_msg.edit(content=f"❌ **Processing Error:** {str(e)}\n\nPlease make sure you uploaded a clear stats screenshot.")

    @commands.command(name="mystats", help="View your most recently uploaded stats.")
    async def mystats(self, ctx):
        session = SessionLocal()
        try:
            stats = session.query(UserStats).filter(UserStats.discordid == str(ctx.author.id)).order_by(UserStats.timestamp.desc()).first()
            if not stats:
                await ctx.send("❌ No stats found. Use !uploadstats to upload your stats screenshot.")
                return
            # Format the stats nicely
            fields = [
                ("Game Started", stats.game_started),
                ("Coins Earned", stats.coins_earned),
                ("Cash Earned", stats.cash_earned),
                ("Stones Earned", stats.stones_earned),
                ("Damage Dealt", stats.damage_dealt),
                ("Enemies Destroyed", stats.enemies_destroyed),
                ("Waves Completed", stats.waves_completed),
                ("Upgrades Bought", stats.upgrades_bought),
                ("Workshop Upgrades", stats.workshop_upgrades),
                ("Workshop Coins Spent", stats.workshop_coins_spent),
                ("Research Completed", stats.research_completed),
                ("Lab Coins Spent", stats.lab_coins_spent),
                ("Free Upgrades", stats.free_upgrades),
                ("Interest Earned", stats.interest_earned),
                ("Orb Kills", stats.orb_kills),
                ("Death Ray Kills", stats.death_ray_kills),
                ("Thorn Damage", stats.thorn_damage),
                ("Waves Skipped", stats.waves_skipped),
            ]
            msg = f"📊 **Your Most Recent Stats:**\n"
            for label, value in fields:
                formatted_value = self.format_stat_value(value)
                msg += f"**{label}:** {formatted_value}\n"
            await ctx.send(msg)
        except Exception as e:
            await ctx.send(f"❌ Error retrieving your stats: {e}")
        finally:
            session.close()

async def setup(bot):
    await bot.add_cog(StatsCog(bot))  