import discord
import os
import re
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from discord.ext import commands
from sqlalchemy.orm import Session
from dashboard_backend.database import SessionLocal
from dashboard_backend.models import UserData, UserDataHistory, BotAdmin
from gemini_processor import process_image
from gemini_sql_parser import process_gemini_result

load_dotenv()

TOKEN = os.environ.get("DISCORD_TOKEN")

if TOKEN is None:
    raise ValueError("No Discord bot token found in environment variables.")

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class UploadOnlyHelp(commands.MinimalHelpCommand):
    async def send_bot_help(self, mapping):
        ctx = self.context
        embed = discord.Embed(
            title="Tower Scoreboard Bot — Help",
            color=0x2f3136
        )
        embed.description = (
            "Overview: Upload a single game screenshot. The bot auto-detects whether it’s stats or tier data and saves it."
        )
        embed.add_field(
            name="How to use",
            value="• Type `!upload`\n• Attach a clear PNG/JPG of your game screen\n• Send the message; you’ll get a processing update and a summary",
            inline=False
        )
        await ctx.send(embed=embed)

bot.help_command = UploadOnlyHelp()

_user_locks = {}

def get_user_lock(user_id: str) -> asyncio.Lock:
    """Return an asyncio.Lock dedicated to a single user.

    Ensures that concurrent uploads from the same user do not race when
    updating shared resources like the database.
    """
    lock = _user_locks.get(user_id)
    if lock is None:
        lock = asyncio.Lock()
        _user_locks[user_id] = lock
    return lock

async def async_process_image(image_url: str, force_type: str = None) -> dict:
    """Run synchronous image processing in a background thread.

    Offloads CPU/IO heavy work to a thread so the event loop remains responsive.
    """
    return await asyncio.to_thread(process_image, image_url, force_type)

async def async_process_gemini_result(gemini_result: dict, discord_id: str, discord_name: str) -> dict:
    """Run synchronous database work in a background thread.

    Prevents blocking the event loop during DB operations.
    """
    return await asyncio.to_thread(process_gemini_result, gemini_result, discord_id, discord_name)

def get_db_session():
    """Create and return a new database session.
    
    Returns:
        Session: A new SQLAlchemy database session instance.
    """
    return SessionLocal()


def parse_wave_coins(tier_str):
    """Parse wave number and coin amount from a tier string.
    
    Args:
        tier_str (str): Tier string in format "Wave: X Coins: Y"
        
    Returns:
        tuple: (wave_number, coin_amount) where wave is int and coins is float
    """
    # Extract wave number using regex
    wave_match = re.search(r"Wave:\s*(\d+)", tier_str)
    # Extract coins with optional suffix (K, M, B, T, Q)
    coins_match = re.search(r"Coins:\s*([\d.,]+[KMBTQ]?)", tier_str)

    wave = int(wave_match.group(1)) if wave_match else 0

    coins_str = coins_match.group(1) if coins_match else "0"
    multiplier = 1
    
    # Convert suffix to numeric multiplier
    if coins_str.endswith("K"):
        multiplier = 1_000
        coins_str = coins_str[:-1]
    elif coins_str.endswith("M"):
        multiplier = 1_000_000
        coins_str = coins_str[:-1]
    elif coins_str.endswith("B"):
        multiplier = 1_000_000_000
        coins_str = coins_str[:-1]
    elif coins_str.endswith("T"):
        multiplier = 1_000_000_000_000
        coins_str = coins_str[:-1]
    elif coins_str.endswith("Q"):
        multiplier = 1_000_000_000_000_000
        coins_str = coins_str[:-1]

    try:
        coins = float(coins_str.replace(",", "")) * multiplier
    except:
        coins = 0

    return wave, coins

def save_user_data(discord_id, discord_name, tier_data):
    """Save or update user tier data in the database.
    
    Args:
        discord_id (str): Discord user ID
        discord_name (str): Discord username
        tier_data (list): List of 18 tier strings in "Wave: X Coins: Y" format
        
    Updates existing user data or creates new user record.
    Also adds entry to history table for tracking.
    """
    session = get_db_session()
    try:
        # Check if user already exists
        existing_user = session.query(UserData).filter(UserData.discordid == discord_id).first()
        if existing_user:
            # Update existing user
            existing_user.discordname = discord_name
            for i, tier in enumerate(tier_data):
                setattr(existing_user, f"T{i+1}", tier)
        else:
            # Create new user
            user_data = UserData(
                discordid=discord_id,
                discordname=discord_name,
                date=datetime.now(),
                **{f"T{i+1}": tier_data[i] for i in range(18)}
            )
            session.add(user_data)
        
        # Add to history
        history_entry = UserDataHistory(
            discordid=discord_id,
            discordname=discord_name,
            **{f"T{i+1}": tier_data[i] for i in range(18)}
        )
        session.add(history_entry)
        
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error saving user data: {e}")
    finally:
        session.close()

def get_user_data(discord_id):
    """Retrieve user's tier data from the database.
    
    Args:
        discord_id (str): Discord user ID to look up
        
    Returns:
        list: List of 18 tier strings, or None if user not found
    """
    session = get_db_session()
    try:
        user = session.query(UserData).filter(UserData.discordid == discord_id).first()
        if user:
            return [getattr(user, f"T{i+1}") for i in range(18)]
        return None
    finally:
        session.close()

def is_bot_admin(discord_id):
    """Check if a user is a bot administrator.
    
    Args:
        discord_id (str): Discord user ID to check
        
    Returns:
        bool: True if user is a bot admin, False otherwise
    """
    session = get_db_session()
    try:
        admin = session.query(BotAdmin).filter(BotAdmin.discordid == discord_id).first()
        return admin is not None
    finally:
        session.close()


@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    print(f"🤖 Gemini AI integration active")
    print(f"📊 Database connection established")
    print(f"🎯 Ready to process game screenshots!")

# MOTHBALLED: commands_list moved to mothballed_commands.py

# MOTHBALLED: mydata moved to mothballed_commands.py

# MOTHBALLED: leaderboard moved to mothballed_commands.py

# MOTHBALLED: leaderwaves moved to mothballed_commands.py

def format_number_suffix(num: float) -> str:
    """Format a number with a suffix (K, M, B, T, Q) and one decimal if needed."""
    abs_num = abs(num)
    if abs_num >= 1_000_000_000_000_000:
        return f"{num/1_000_000_000_000_000:.2f}Q".rstrip('0').rstrip('.')
    elif abs_num >= 1_000_000_000_000:
        return f"{num/1_000_000_000_000:.2f}T".rstrip('0').rstrip('.')
    elif abs_num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f}B".rstrip('0').rstrip('.')
    elif abs_num >= 1_000_000:
        return f"{num/1_000_000:.2f}M".rstrip('0').rstrip('.')
    elif abs_num >= 1_000:
        return f"{num/1_000:.2f}K".rstrip('0').rstrip('.')
    else:
        return str(int(num))

# MOTHBALLED: leadercoins moved to mothballed_commands.py

# MOTHBALLED: leadertier moved to mothballed_commands.py

# MOTHBALLED: leadertier_error moved to mothballed_commands.py

@bot.command(help="Show all current and historical user data.")
async def showdata(ctx):
    """Shows all current and historical user data. (Bot Admins only)"""
    if not is_bot_admin(str(ctx.author.id)):
        await ctx.send("❌ You do not have permission to use this command.")
        return
    
    session = get_db_session()
    try:
        response = ""
        rows = session.query(UserData).all()
        if rows:
            response += "**Current User Data:**\n"
            for row in rows:
                discordname = row.discordname
                tiers = "\n".join([f"T{i+1}: {getattr(row, f'T{i+1}')}" for i in range(18)])
                response += f"__{discordname}__\n{tiers}\n\n"
        else:
            response += "No current user data found.\n"
        
        rows = session.query(UserDataHistory).all()
        if rows:
            response += "**Historical Entries:**\n"
            for row in rows:
                discordname = row.discordname
                timestamp = row.timestamp
                tiers = "\n".join([f"T{i+1}: {getattr(row, f'T{i+1}')}" for i in range(18)])
                response += f"__{discordname}__ at {timestamp}\n{tiers}\n\n"
        else:
            response += "No history found.\n"
        
        for chunk in [response[i:i+1900] for i in range(0, len(response), 1900)]:
            await ctx.send(f"```{chunk}```")
    except Exception as e:
        await ctx.send(f"❌ Error retrieving data: {e}")
    finally:
        session.close()

showdata.hidden = True

@showdata.error
async def showdata_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You do not have permission to use this command.")



@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    # Only process commands, do not auto-process images
    await bot.process_commands(message)

@bot.command(help="Add a user to the bot admin list. Usage: !addbotadmin @user")
@commands.has_permissions(administrator=True)
async def addbotadmin(ctx, user: discord.Member):
    session = get_db_session()
    try:
        # Check if already an admin
        existing_admin = session.query(BotAdmin).filter(BotAdmin.discordid == str(user.id)).first()
        if existing_admin:
            await ctx.send(f"✅ {user.mention} is already a bot admin.")
            return
        
        # Add as admin
        new_admin = BotAdmin(discordid=str(user.id))
        session.add(new_admin)
        session.commit()
        await ctx.send(f"✅ {user.mention} has been added as a bot admin.")
    except Exception as e:
        session.rollback()
        await ctx.send(f"❌ Error adding bot admin: {e}")
    finally:
        session.close()

@bot.command(help="Remove a user from the bot admin list. Usage: !removebotadmin @user")
@commands.has_permissions(administrator=True)
async def removebotadmin(ctx, user: discord.Member):
    session = get_db_session()
    try:
        # Remove admin
        admin = session.query(BotAdmin).filter(BotAdmin.discordid == str(user.id)).first()
        if admin:
            session.delete(admin)
            session.commit()
            await ctx.send(f"✅ {user.mention} has been removed from the bot admin list.")
        else:
            await ctx.send(f"❌ {user.mention} is not a bot admin.")
    except Exception as e:
        session.rollback()
        await ctx.send(f"❌ Error removing bot admin: {e}")
    finally:
        session.close()

@bot.command(help="List all bot admins.")
@commands.has_permissions(administrator=True)
async def listbotadmins(ctx):
    session = get_db_session()
    try:
        admins = session.query(BotAdmin).all()
        if admins:
            admin_list = [f"<@{admin.discordid}>" for admin in admins]
            await ctx.send(f"**Bot Admins:**\n{', '.join(admin_list)}")
        else:
            await ctx.send("No bot admins set.")
    except Exception as e:
        await ctx.send(f"❌ Error listing bot admins: {e}")
    finally:
        session.close()


@bot.command(name="upload", help="Upload any game screenshot (stats or tier) - AI will auto-detect the type.")
async def upload(ctx):
    """Process uploaded game screenshots concurrently using background tasks.

    Supports both stats screenshots and tier screenshots. Uses Gemini AI to extract
    data and saves to the appropriate database table. Heavy work is offloaded to
    threads to keep the bot responsive. A per-user lock prevents races if the
    same user uploads multiple images simultaneously.
    """
    if not ctx.message.attachments:
        await ctx.send("Please attach a screenshot of your game data (stats or tier).")
        return
    
    attachment = ctx.message.attachments[0]
    processing_msg = await ctx.send("🔄 Processing image... Please wait.")

    async def process_upload_task():
        try:
            # Run CPU/IO-heavy image handling in a background thread
            gemini_result = await async_process_image(attachment.url)

            if not gemini_result.get("success"):
                await processing_msg.edit(content=f"❌ Failed to process image: {gemini_result.get('error', 'Unknown error')}")
                return

            # Per-user lock prevents concurrent writes racing for the same user
            lock = get_user_lock(str(ctx.author.id))
            async with lock:
                sql_result = await async_process_gemini_result(
                    gemini_result,
                    str(ctx.author.id),
                    str(ctx.author)
                )

            if sql_result.get("success"):
                if gemini_result.get("image_type") == "stats":
                    stats_id = sql_result.get('stats_id', 'N/A')
                    improvements = sql_result.get('improvements', [])
                    improvement_text = f"\n📈 Improvements: {', '.join(improvements)}" if improvements else "\n📊 Status: No significant improvements detected"
                    await processing_msg.edit(content=f"✅ Stats saved. ID: {stats_id}{improvement_text}")
                elif gemini_result.get("image_type") == "tier":
                    tier_data = sql_result.get("tier_data", {})
                    improvements = tier_data.get("improvements", [])
                    skipped = tier_data.get("skipped", [])
                    improvement_text = f"\n🏆 Improved Tiers: {', '.join(improvements)}" if improvements else "\n⚠️ No improvements found"
                    skipped_text = f"\n⏭️ Skipped (no improvement): {', '.join(skipped)}" if skipped else ""
                    await processing_msg.edit(content=f"✅ Tier data processed.{improvement_text}{skipped_text}")
                else:
                    await processing_msg.edit(content="❌ Invalid image. Please upload either a stats screenshot or a tier screenshot.")
            else:
                await processing_msg.edit(content=f"❌ **Database Error:** {sql_result.get('message', 'Unknown error')}")

        except Exception as e:
            # Ensure other uploads continue even if this one fails
            await processing_msg.edit(content=f"❌ **Processing Error:** {str(e)}\n\nPlease make sure you uploaded a clear game screenshot.")

    # Fire-and-forget to avoid blocking this command on processing
    asyncio.create_task(process_upload_task())

## MOTHBALLED: uploadwaves moved to mothballed_commands.py

async def main():
    # await bot.load_extension("cogs.stats_cog")  # Mothballed while building new commands
    await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())