import discord
import os
import requests
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
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

def get_db_session():
    return SessionLocal()



def parse_wave_coins(tier_str):
    wave_match = re.search(r"Wave:\s*(\d+)", tier_str)
    coins_match = re.search(r"Coins:\s*([\d.,]+[KMBTQ]?)", tier_str)

    wave = int(wave_match.group(1)) if wave_match else 0

    coins_str = coins_match.group(1) if coins_match else "0"
    multiplier = 1
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
    session = get_db_session()
    try:
        user = session.query(UserData).filter(UserData.discordid == discord_id).first()
        if user:
            return [getattr(user, f"T{i+1}") for i in range(18)]
        return None
    finally:
        session.close()

def is_bot_admin(discord_id):
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

@bot.command(name="commands", help="List all available commands and their descriptions.")
async def commands_list(ctx):
    """Lists all available commands and their descriptions."""
    description = ""
    for command in bot.commands:
        if not command.hidden:
            description += f"**!{command.name}**: {command.help or command.short_doc or 'No description'}\n"
    await ctx.send(description)

@bot.command(help="Show your saved tier data (waves and coins for each tier).")
async def mydata(ctx):
    """Shows the user their saved tier data (waves and coins for each tier)."""
    data = get_user_data(str(ctx.author.id))
    if data:
        formatted = "Tier | Wave     | Coins\n" + "-----|----------|--------\n"
        for i, entry in enumerate(data):
            wave_match = re.search(r"Wave: (\S+)", entry)
            coin_match = re.search(r"Coins: (\S+)", entry)
            wave = wave_match.group(1) if wave_match else "0"
            coins = coin_match.group(1) if coin_match else "0"
            formatted += f"T{i+1:<3} | {wave:<8} | {coins}\n"
        await ctx.send(f"📊 Your saved tiers:\n```\n{formatted}```")
    else:
        await ctx.send("❌ No data found. Upload an image to start tracking.")

@bot.command(help="Show the leaderboard with the highest wave and coins per user.")
async def leaderboard(ctx):
    """Shows a leaderboard of all users, displaying the tier with the highest wave and the tier with the highest coins for each user."""
    session = get_db_session()
    try:
        users = session.query(UserData).all()
        header = ["Player", "Tier(s) with Highest Wave and Coins"]
        lines = [" | ".join(header)]
        lines.append("-" * 70)
        for user in users:
            name = user.discordname
            tiers = [getattr(user, f"T{i+1}") for i in range(18)]
            max_wave = -1
            max_coins = -1
            wave_idx = -1
            coins_idx = -1
            for i, t in enumerate(tiers):
                if not t:
                    continue
                wave, coins = parse_wave_coins(t)
                if wave > max_wave:
                    max_wave = wave
                    wave_idx = i
                if coins > max_coins:
                    max_coins = coins
                    coins_idx = i
            if wave_idx == -1:
                wave_idx = 0
                max_wave = 0
            if coins_idx == -1:
                coins_idx = 0
                max_coins = 0
            wave_str = f"T{wave_idx + 1} Wave: {max_wave}"
            coins_str = f"T{coins_idx + 1} Coins: {tiers[coins_idx].split('Coins: ')[1]}" if tiers[coins_idx] and tiers[coins_idx].count("Coins: ") > 0 else f"T{coins_idx + 1} Coins: 0"
            line = f"{name} | Highest wave: {wave_str} ; Highest coins: {coins_str}"
            lines.append(line)
            if len(lines) > 12:
                break
        response = "\n".join(lines)
        await ctx.send(f"🏆 **Leaderboard**\n```\n{response}```")
    except Exception as e:
        await ctx.send(f"❌ Error retrieving leaderboard: {e}")
    finally:
        session.close()

@bot.command(help="Show all users and their highest wave for each tier.")
async def leaderwaves(ctx):
    """Shows all users and their highest wave for each tier."""
    session = get_db_session()
    try:
        users = session.query(UserData).all()
        header = ["Player", "Waves per Tier"]
        lines = [" | ".join(header)]
        lines.append("-" * 70)
        for user in users:
            name = user.discordname
            tiers = [getattr(user, f"T{i+1}") for i in range(18)]
            waves_list = []
            for i, t in enumerate(tiers):
                if t:
                    wave, _ = parse_wave_coins(t)
                    if wave > 0:
                        waves_list.append(f"T{i+1}: {wave}")
            if not waves_list:
                waves_list.append("No waves recorded")
            waves_str = " ; ".join(waves_list)
            line = f"{name} | {waves_str}"
            lines.append(line)
            if len(lines) > 12:
                break
        leaderboard_text = "\n".join(lines)
        await ctx.send(f"📊 Leaderwaves:\n```\n{leaderboard_text}```")
    except Exception as e:
        await ctx.send(f"❌ Error retrieving leaderwaves: {e}")
    finally:
        session.close()

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

@bot.command(help="Show all users and their highest coins for each tier.")
async def leadercoins(ctx):
    """Shows all users and their highest coins for each tier in a readable, suffixed format."""
    session = get_db_session()
    try:
        users = session.query(UserData).all()
        header = ["Player", "Coins per Tier"]
        lines = [" | ".join(header)]
        lines.append("-" * 70)
        for user in users:
            name = user.discordname
            tiers = [getattr(user, f"T{i+1}") for i in range(18)]
            coins_list = []
            for i, t in enumerate(tiers):
                if t:
                    _, coins = parse_wave_coins(t)
                    if coins > 0:
                        coins_str = format_number_suffix(coins)
                        coins_list.append(f"T{i+1}: {coins_str}")
            if not coins_list:
                coins_list.append("No coins recorded")
            coins_str = " ; ".join(coins_list)
            line = f"{name} | {coins_str}"
            lines.append(line)
            if len(lines) > 12:
                break
        leaderboard_text = "\n".join(lines)
        await ctx.send(f"📊 Leadercoins:\n```\n{leaderboard_text}```")
    except Exception as e:
        await ctx.send(f"❌ Error retrieving leadercoins: {e}")
    finally:
        session.close()

@bot.command(name="leadertier", help="Show the top 5 users for a specific tier, ranked by wave. Usage: !leadertier t1")
async def leadertier(ctx, tier: str):
    """Shows the top 5 users for a specific tier, ranked by wave, including their coin count."""
    match = re.match(r"t(\d+)", tier.lower())
    if not match:
        await ctx.send("❌ Invalid tier format. Use e.g. `t1`, `t2`, etc.")
        return
    tier_num = int(match.group(1))
    if not (1 <= tier_num <= 18):
        await ctx.send("❌ Tier number must be between 1 and 18.")
        return
    
    session = get_db_session()
    try:
        users = session.query(UserData).all()
        results = []
        for user in users:
            tier_str = getattr(user, f"T{tier_num}")
            if tier_str:
                wave, coins = parse_wave_coins(tier_str)
                if wave > 0:
                    results.append((user.discordname, wave, coins))
        results.sort(key=lambda x: x[1], reverse=True)
        top5 = results[:5]
        header = f"Top 5 Players for Tier {tier_num} by Wave"
        lines = [header, "-" * len(header)]
        for name, wave, coins in top5:
            coins_str = format_number_suffix(coins)
            lines.append(f"{name} Wave: {wave} | Coins: {coins_str}")
        leaderboard_text = "\n".join(lines)
        await ctx.send(f"📊 {header}:\n```\n{leaderboard_text}```")
    except Exception as e:
        await ctx.send(f"❌ Error retrieving tier leaderboard: {e}")
    finally:
        session.close()

@leadertier.error
async def leadertier_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Please specify a tier, e.g. `!leadertier t1`")

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
    if not ctx.message.attachments:
        await ctx.send("Please attach a screenshot of your game data (stats or tier).")
        return
    
    attachment = ctx.message.attachments[0]
    
    # Send initial processing message
    processing_msg = await ctx.send("🔄 Processing image... Please wait.")
    
    try:
        # Process image with Gemini
        gemini_result = process_image(attachment.url)
        
        if not gemini_result["success"]:
            await processing_msg.edit(content=f"❌ Failed to process image: {gemini_result.get('error', 'Unknown error')}")
            return
        
        # Proceed without exposing or gating on AI confidence
        
        # Save to database using our SQL parser
        sql_result = process_gemini_result(gemini_result, str(ctx.author.id), str(ctx.author))
        
        if sql_result["success"]:
            if gemini_result["image_type"] == "stats":
                stats_id = sql_result.get('stats_id', 'N/A')
                improvements = sql_result.get('improvements', [])
                improvement_text = f"\n📈 Improvements: {', '.join(improvements)}" if improvements else "\n📊 Status: No significant improvements detected"
                await processing_msg.edit(content=f"✅ Stats saved. ID: {stats_id}{improvement_text}")
            elif gemini_result["image_type"] == "tier":
                tier_data = sql_result.get("tier_data", {})
                tiers_updated = tier_data.get("tiers_updated", 0)
                improvements = tier_data.get("improvements", [])
                skipped = tier_data.get("skipped", [])
                improvement_text = f"\n🏆 Improved Tiers: {', '.join(improvements)}" if improvements else "\n⚠️ No improvements found"
                skipped_text = f"\n⏭️ Skipped (no improvement): {', '.join(skipped)}" if skipped else ""
                await processing_msg.edit(content=f"✅ Tier data processed.{improvement_text}{skipped_text}")
            else:
                await processing_msg.edit(content="❌ Invalid image. Please upload either a stats screenshot or a tier screenshot.")
        else:
            await processing_msg.edit(content=f"❌ **Database Error:** {sql_result['message']}")
            
    except Exception as e:
        await processing_msg.edit(content=f"❌ **Processing Error:** {str(e)}\n\nPlease make sure you uploaded a clear game screenshot.")

@bot.command(name="uploadwaves", help="Upload your tier screenshot to save your waves/coins data.")
async def uploadwaves(ctx):
    if not ctx.message.attachments:
        await ctx.send("Please attach a screenshot of your tier data.")
        return
    
    attachment = ctx.message.attachments[0]
    
    # Send initial processing message
    processing_msg = await ctx.send("🔄 Processing tier image... Please wait.")
    
    try:
        # Process image with Gemini, force tier classification for this command
        gemini_result = process_image(attachment.url, force_type="tier")
        
        if not gemini_result["success"]:
            await processing_msg.edit(content=f"❌ Failed to process image: {gemini_result.get('error', 'Unknown error')}")
            return
        
        # Check if it's actually a tier image
        if gemini_result["image_type"] != "tier":
            await processing_msg.edit(content="❌ This doesn't appear to be a tier screenshot. Please upload a tier image that contains tier progress data with 'Tier 1', 'Tier 2', etc.")
            return
        
        # Proceed without exposing or gating on AI confidence
        
        # Save to database using our SQL parser
        sql_result = process_gemini_result(gemini_result, str(ctx.author.id), str(ctx.author))
        
        if sql_result["success"]:
            tier_data = sql_result.get("tier_data", {})
            tiers_updated = tier_data.get("tiers_updated", 0)
            improvements = tier_data.get("improvements", [])
            skipped = tier_data.get("skipped", [])
            improvement_text = f"\n🏆 Improved Tiers: {', '.join(improvements)}" if improvements else "\n⚠️ No improvements found"
            skipped_text = f"\n⏭️ Skipped (no improvement): {', '.join(skipped)}" if skipped else ""
            await processing_msg.edit(content=f"✅ Tier data processed.{improvement_text}{skipped_text}")
        else:
            await processing_msg.edit(content=f"❌ **Database Error:** {sql_result['message']}")
            
    except Exception as e:
        await processing_msg.edit(content=f"❌ **Processing Error:** {str(e)}\n\nPlease make sure you uploaded a clear tier screenshot.")

async def main():
    await bot.load_extension("cogs.stats_cog")
    await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())