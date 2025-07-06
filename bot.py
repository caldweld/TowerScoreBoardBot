import discord
import os
import pytesseract
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
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

load_dotenv()

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

if TOKEN is None:
    raise ValueError("No Discord bot token found in environment variables.")

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def get_db_session():
    return SessionLocal()

def extract_tiers(text):
    tier_data = ["Wave: 0 Coins: 0"] * 18
    lines = text.splitlines()
    
    print(f"[DEBUG] Full OCR text:\n{text}")
    
    # Multiple patterns to handle different OCR outputs
    patterns = [
        # Pattern 1: "Tier X Y Z" where Y=wave, Z=coins
        re.compile(r"Tier\s*(\d+)\s+(\d+)\s+([\d.,]+[KMBTQ]?)", re.IGNORECASE),
        # Pattern 2: "Tier X Z" where Z=coins (no wave, assume 0)
        re.compile(r"Tier\s*(\d+)\s+([\d.,]+[KMBTQ]?)", re.IGNORECASE),
        # Pattern 3: "Tier X" (no data, assume 0)
        re.compile(r"Tier\s*(\d+)", re.IGNORECASE)
    ]

    for line in lines:
        line = line.strip()
        if not line.lower().startswith("tier"):
            continue
            
        print(f"[DEBUG] Processing line: '{line}'")
        matched = False
        for i, pattern in enumerate(patterns):
            match = pattern.search(line)
            if match:
                print(f"[DEBUG] Matched pattern {i+1}: {match.groups()}")
                tier = int(match.group(1))
                if 1 <= tier <= 18:
                    if len(match.groups()) == 3:
                        # Pattern 1: Tier X Y Z
                        wave = match.group(2).strip()
                        coins = match.group(3).strip()
                        tier_data[tier - 1] = f"Wave: {wave} Coins: {coins}"
                        print(f"[DEBUG] Set tier {tier} to Wave: {wave} Coins: {coins}")
                    elif len(match.groups()) == 2:
                        # Pattern 2: Tier X Z (no wave)
                        coins = match.group(2).strip()
                        tier_data[tier - 1] = f"Wave: 0 Coins: {coins}"
                        print(f"[DEBUG] Set tier {tier} to Wave: 0 Coins: {coins}")
                    else:
                        # Pattern 3: Tier X (no data)
                        tier_data[tier - 1] = f"Wave: 0 Coins: 0"
                        print(f"[DEBUG] Set tier {tier} to Wave: 0 Coins: 0")
                    matched = True
                    break
        
        if not matched and line.lower().startswith("tier"):
            print(f"[Skipped line]: {line}")

    return tier_data

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

def find_stats_line(ocr_text):
    pattern = re.compile(r"\b[s5\$][t7][a@][t7][s5\$]\b.*", re.IGNORECASE)
    lines = ocr_text.splitlines()
    for i, line in enumerate(lines):
        if pattern.search(line):
            return i
    return -1

def create_canvas_table(tiers):
    width, height = 350, 450
    background_color = (30, 30, 30)
    text_color = (255, 255, 255)
    header_color = (100, 200, 255)
    line_color = (70, 70, 70)

    img = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 16)
        font_bold = ImageFont.truetype("arialbd.ttf", 18)
    except IOError:
        font = ImageFont.load_default()
        font_bold = font

    # Headers
    draw.text((10, 10), "Tier", fill=header_color, font=font_bold)
    draw.text((80, 10), "Wave", fill=header_color, font=font_bold)
    draw.text((180, 10), "Coins", fill=header_color, font=font_bold)

    y_start = 40
    row_height = 22
    draw.line((10, 35, width - 10, 35), fill=line_color)

    for i, entry in enumerate(tiers):
        tier_num = f"T{i+1}"
        wave_match = re.search(r"Wave: (\S+)", entry)
        coin_match = re.search(r"Coins: (\S+)", entry)
        wave = wave_match.group(1) if wave_match else "0"
        coins = coin_match.group(1) if coin_match else "0"

        y = y_start + i * row_height
        draw.text((10, y), tier_num, fill=text_color, font=font)
        draw.text((80, y), wave, fill=text_color, font=font)
        draw.text((180, y), coins, fill=text_color, font=font)
        draw.line((10, y + row_height - 4, width - 10, y + row_height - 4), fill=line_color)

    return img

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

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

@bot.command(help="Show your wave progress over time for a specific tier. Usage: !progress t1")
async def progress(ctx, tier: str):
    """Shows a graph of your wave progress over time for the specified tier."""
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
        user_id = str(ctx.author.id)
        history = session.query(UserDataHistory).filter(UserDataHistory.discordid == user_id).all()
        user_history = []
        for row in history:
            tier_str = getattr(row, f"T{tier_num}")
            if tier_str:
                user_history.append(row)
        
        if not user_history:
            await ctx.send("❌ No historical data found for you. Upload images to start tracking!")
            return
        
        timestamps = []
        waves = []
        for row in user_history:
            timestamp = row.timestamp
            tier_str = getattr(row, f"T{tier_num}")
            wave, _ = parse_wave_coins(tier_str)
            if wave > 0:
                timestamps.append(timestamp)
                waves.append(wave)
        
        if not waves:
            await ctx.send(f"❌ No wave data found for {tier.upper()}.")
            return
        
        # Discord color palette
        bg_color = '#23272A'
        grid_color = '#99AAB5'
        line_color = '#5865F2'
        font_family = 'DejaVu Sans'
        
        # Prepare dates (YYYY-MM-DD only)
        dates = [ts.strftime('%Y-%m-%d') for ts in timestamps]
        
        # Plot
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(8, 4), facecolor=bg_color)
        ax.set_facecolor(bg_color)
        ax.plot(dates, waves, marker='o', linestyle='-', color=line_color, linewidth=2, markersize=8)
        ax.set_title(f"{ctx.author.name}'s {tier.upper()} Wave Progress", fontsize=16, fontweight='bold', color=grid_color, fontname=font_family)
        ax.set_xlabel("Date", fontsize=12, color=grid_color, fontname=font_family)
        ax.set_ylabel("Wave", fontsize=12, color=grid_color, fontname=font_family)
        ax.tick_params(axis='x', colors=grid_color, labelsize=10, labelrotation=30)
        ax.tick_params(axis='y', colors=grid_color, labelsize=10)
        ax.grid(True, which='both', linestyle='--', linewidth=0.7, alpha=0.7, color=grid_color)
        
        # Save the plot
        plt.tight_layout()
        plt.savefig('progress.png', facecolor=bg_color, edgecolor='none', dpi=150, bbox_inches='tight')
        plt.close()
        
        # Send the image
        with open('progress.png', 'rb') as f:
            await ctx.send(file=discord.File(f, 'progress.png'))
        
        # Clean up
        os.remove('progress.png')
    except Exception as e:
        await ctx.send(f"❌ Error creating progress graph: {e}")
    finally:
        session.close()

@progress.error
async def progress_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Please specify a tier, e.g. `!progress t1`")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Process commands first
    await bot.process_commands(message)

    # Check if message has an image
    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith('image'):
                try:
                    # Download the image
                    response = requests.get(attachment.url)
                    img = Image.open(BytesIO(response.content))
                    
                    # Extract text using OCR
                    custom_config = r'--oem 3 --psm 6'
                    ocr_text = pytesseract.image_to_string(img, config=custom_config)
                    
                    # Find the stats line
                    stats_line_index = find_stats_line(ocr_text)
                    if stats_line_index != -1:
                        # Extract tier data
                        tier_data = extract_tiers(ocr_text)
                        
                        # Save to database
                        save_user_data(str(message.author.id), message.author.name, tier_data)
                        
                        # Create and send a formatted table
                        table_img = create_canvas_table(tier_data)
                        img_buffer = BytesIO()
                        table_img.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        
                        await message.channel.send(
                            f"✅ Data saved for {message.author.mention}!",
                            file=discord.File(img_buffer, 'tier_data.png')
                        )
                    else:
                        await message.channel.send("❌ Could not find stats in the image. Please make sure the image contains tier information.")
                        
                except Exception as e:
                    await message.channel.send(f"❌ Error processing image: {e}")

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

@bot.command(help="[Debug] Add yourself as a bot admin.")
async def debugaddme(ctx):
    # Check if user is already an admin
    if is_bot_admin(str(ctx.author.id)):
        await ctx.send("❌ You are already a bot admin.")
        return
    
    session = get_db_session()
    try:
        new_admin = BotAdmin(discordid=str(ctx.author.id))
        session.add(new_admin)
        session.commit()
        await ctx.send(f"✅ {ctx.author.mention} added as a bot admin (debug mode).")
    except Exception as e:
        session.rollback()
        await ctx.send(f"❌ Error adding yourself as admin: {e}")
    finally:
        session.close()

@bot.command(help="[Debug] Remove yourself from the bot admin list.")
async def debugremoveme(ctx):
    # Check if user is an admin
    if not is_bot_admin(str(ctx.author.id)):
        await ctx.send("❌ You are not a bot admin.")
        return
    
    session = get_db_session()
    try:
        admin = session.query(BotAdmin).filter(BotAdmin.discordid == str(ctx.author.id)).first()
        if admin:
            session.delete(admin)
            session.commit()
            await ctx.send(f"✅ {ctx.author.mention} removed from bot admin list (debug mode).")
        else:
            await ctx.send("❌ You are not a bot admin.")
    except Exception as e:
        session.rollback()
        await ctx.send(f"❌ Error removing yourself as admin: {e}")
    finally:
        session.close()

bot.load_extension("cogs.stats_cog")

if __name__ == "__main__":
    bot.run(TOKEN)