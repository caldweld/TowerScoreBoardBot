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
            # Fetch the most recent entry for this user
            prev = session.query(UserStats).filter(UserStats.discordid == str(ctx.author.id)).order_by(UserStats.timestamp.desc()).first()
            numeric_fields = [
                "coins_earned", "cash_earned", "stones_earned", "damage_dealt", "enemies_destroyed", "waves_completed",
                "upgrades_bought", "workshop_upgrades", "workshop_coins_spent", "research_completed", "lab_coins_spent",
                "free_upgrades", "interest_earned", "orb_kills", "death_ray_kills", "thorn_damage", "waves_skipped"
            ]
            def parse_num(val):
                if val is None:
                    return 0
                val = str(val).replace(",", "").replace("$", "").strip()
                
                # Define suffixes in order with their multipliers
                suffixes = {
                    'K': 1_000,
                    'M': 1_000_000,
                    'B': 1_000_000_000,
                    'T': 1_000_000_000_000,
                    'q': 1_000_000_000_000_000,
                    'Q': 1_000_000_000_000_000_000,
                    's': 1_000_000_000_000_000_000_000,
                    'S': 1_000_000_000_000_000_000_000_000,
                    'O': 1_000_000_000_000_000_000_000_000_000,
                    'N': 1_000_000_000_000_000_000_000_000_000_000,
                    'D': 1_000_000_000_000_000_000_000_000_000_000_000,
                    'aa': 1_000_000_000_000_000_000_000_000_000_000_000_000,
                    'ab': 1_000_000_000_000_000_000_000_000_000_000_000_000_000,
                    'ac': 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000,
                    'ad': 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000
                }
                
                # Use regex to match number with optional suffix
                # Pattern: ^(\d+(?:\.\d{1,2})?)([KMBTqQsSOND]|aa|ab|ac|ad)?$
                import re
                pattern = r'^(\d+(?:\.\d{1,2})?)([KMBTqQsSOND]|aa|ab|ac|ad)?$'
                match = re.match(pattern, val)
                
                if match:
                    number_part, suffix = match.groups()
                    try:
                        number = float(number_part)
                        multiplier = suffixes.get(suffix, 1) if suffix else 1
                        return number * multiplier
                    except ValueError:
                        return 0
                
                # If regex doesn't match, try to handle edge cases
                # Check if it ends with any of our suffixes
                for suffix in sorted(suffixes.keys(), key=len, reverse=True):
                    if val.endswith(suffix):
                        try:
                            number_part = val[:-len(suffix)]
                            number = float(number_part)
                            return number * suffixes[suffix]
                        except ValueError:
                            continue
                
                # If no suffix found, try to parse as regular number
                try:
                    return float(val)
                except ValueError:
                    return 0
            should_save = True
            increased_fields = []
            if prev:
                should_save = False
                for field in numeric_fields:
                    new_val = parse_num(stats.get(field))
                    prev_val = parse_num(getattr(prev, field))
                    if new_val > prev_val:
                        should_save = True
                        increased_fields.append((field, prev_val, new_val, new_val - prev_val))
            if should_save:
                user_stats = UserStats(
                    discordid=str(ctx.author.id),
                    discordname=str(ctx.author),
                    **{k: stats.get(k) for k in stats if k != 'raw_text'}
                )
                session.add(user_stats)
                session.commit()
                await ctx.send("Your stats have been saved successfully!")
                if increased_fields:
                    diff_msg = "**Stats Increased:**\n"
                    for field, prev_val, new_val, diff in increased_fields:
                        diff_msg += f"**{field.replace('_', ' ').title()}**: {prev_val} → {new_val} (Δ {diff})\n"
                    await ctx.send(diff_msg)
            else:
                await ctx.send("No stats have increased since your last upload. Nothing was saved.")
            session.close()
        except Exception as e:
            await ctx.send(f"Failed to process your stats: {e}")

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
                msg += f"**{label}:** {value if value is not None else 'N/A'}\n"
            await ctx.send(msg)
        except Exception as e:
            await ctx.send(f"❌ Error retrieving your stats: {e}")
        finally:
            session.close()

async def setup(bot):
    await bot.add_cog(StatsCog(bot)) 