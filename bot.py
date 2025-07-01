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
from database import DatabaseManager
import matplotlib.pyplot as plt

load_dotenv()  # loads environment variables from .env file

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

if TOKEN is None:
    raise ValueError("No Discord bot token found in environment variables.")


# Set up intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Database setup
db_manager = DatabaseManager()

def extract_tiers(text):
    tier_data = ["Wave: 0 Coins: 0"] * 18
    lines = text.splitlines()
    tier_pattern = re.compile(r"Tier\s*(\d+)\s+(\d+)\s+([\d.,]+[KMBTQ]?)", re.IGNORECASE)

    print("\n--- OCR Output Debug ---")
    print(text)
    print("------------------------\n")

    for line in lines:
        match = tier_pattern.search(line)
        if match:
            tier = int(match.group(1))
            wave = match.group(2).strip()
            coins = match.group(3).strip()
            if 1 <= tier <= 18:
                tier_data[tier - 1] = f"Wave: {wave} Coins: {coins}"
        elif line.lower().startswith("tier"):
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
    db_manager.save_user_data(discord_id, discord_name, tier_data)

def get_user_data(discord_id):
    return db_manager.get_user_data(discord_id)

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
    users = db_manager.get_all_users()
    header = ["Player", "Tier(s) with Highest Wave and Coins"]
    lines = [" | ".join(header)]
    lines.append("-" * 70)
    for user in users:
        name = user[0]
        tiers = user[1:]
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
        coins_str = f"T{coins_idx + 1} Coins: {tiers[coins_idx].split('Coins: ')[1]}" if tiers[coins_idx].count("Coins: ") > 0 else f"T{coins_idx + 1} Coins: 0"
        line = f"{name} | Highest wave: {wave_str} ; Highest coins: {coins_str}"
        lines.append(line)
        if len(lines) > 12:
            break
    leaderboard_text = "\n".join(lines)
    await ctx.send(f"📊 Leaderboard:\n```\n{leaderboard_text}```")

@bot.command(help="Show all users and their highest wave for each tier.")
async def leaderwaves(ctx):
    """Shows all users and their highest wave for each tier."""
    users = db_manager.get_all_users()
    header = ["Player", "Waves per Tier"]
    lines = [" | ".join(header)]
    lines.append("-" * 70)
    for user in users:
        name = user[0]
        tiers = user[1:]
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
    users = db_manager.get_all_users()
    header = ["Player", "Coins per Tier"]
    lines = [" | ".join(header)]
    lines.append("-" * 70)
    for user in users:
        name = user[0]
        tiers = user[1:]
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
    users = db_manager.get_tier_for_all_users(tier_num)
    results = []
    for name, tier_str in users:
        if not tier_str:
            continue
        wave, coins = parse_wave_coins(tier_str)
        if wave > 0:
            results.append((name, wave, coins))
    results.sort(key=lambda x: x[1], reverse=True)
    top5 = results[:5]
    header = f"Top 5 Players for Tier {tier_num} by Wave"
    lines = [header, "-" * len(header)]
    for name, wave, coins in top5:
        coins_str = format_number_suffix(coins)
        lines.append(f"{name} Wave: {wave} | Coins: {coins_str}")
    leaderboard_text = "\n".join(lines)
    await ctx.send(f"📊 {header}:\n```\n{leaderboard_text}```")

@leadertier.error
async def leadertier_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Please specify a tier, e.g. `!leadertier t1`")

@bot.command(help="Show all current and historical user data.")
async def showdata(ctx):
    """Shows all current and historical user data."""
    response = ""
    rows = db_manager.get_all_user_data()
    if rows:
        response += "**Current User Data:**\n"
        for row in rows:
            discordname = row[1]
            tiers = "\n".join([f"T{i+1}: {row[i+2]}" for i in range(18)])
            response += f"__{discordname}__\n{tiers}\n\n"
    else:
        response += "No current user data found.\n"
    rows = db_manager.get_all_user_data_history()
    if rows:
        response += "**Historical Entries:**\n"
        for row in rows:
            discordname = row[1]
            timestamp = row[2]
            tiers = "\n".join([f"T{i+1}: {row[i+3]}" for i in range(18)])
            response += f"__{discordname}__ at {timestamp}\n{tiers}\n\n"
    else:
        response += "No history found.\n"
    for chunk in [response[i:i+1900] for i in range(0, len(response), 1900)]:
        await ctx.send(f"```{chunk}```")

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
    user_id = str(ctx.author.id)
    history = db_manager.get_all_user_data_history()
    # Filter for this user and tier
    user_history = [row for row in history if row[0] == user_id]
    if not user_history:
        await ctx.send("❌ No historical data found for you. Upload images to start tracking!")
        return
    timestamps = []
    waves = []
    for row in user_history:
        timestamp = row[2]
        tier_str = row[3 + (tier_num - 1)]
        wave, _ = parse_wave_coins(tier_str)
        if wave > 0:
            timestamps.append(timestamp)
            waves.append(wave)
    if not waves:
        await ctx.send(f"❌ No wave data found for {tier.upper()}.")
        return
    # Plot
    plt.figure(figsize=(8, 4))
    plt.plot(timestamps, waves, marker='o', linestyle='-', color='b')
    plt.title(f"{ctx.author.name}'s {tier.upper()} Wave Progress")
    plt.xlabel("Time")
    plt.ylabel("Wave")
    plt.xticks(rotation=30, ha='right', fontsize=8)
    plt.tight_layout()
    # Save to buffer
    from io import BytesIO
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    await ctx.send(file=discord.File(buf, filename=f'{tier}_progress.png'), content=f"📈 {ctx.author.mention} {tier.upper()} wave progress:")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.attachments:
        for attachment in message.attachments:
            if attachment.filename.lower().endswith((".png", ".jpg", ".jpeg")):
                response = requests.get(attachment.url)
                image = Image.open(BytesIO(response.content))
                custom_config = r'--oem 3 --psm 6'
                text = pytesseract.image_to_string(image, config=custom_config)
                stats_line_index = find_stats_line(text)
                if stats_line_index == -1:
                    return
                await message.channel.send("🕵️ Processing image...")
                tiers = extract_tiers(text)
                save_user_data(str(message.author.id), str(message.author.name), tiers)
                img = create_canvas_table(tiers)
                with BytesIO() as image_binary:
                    img.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    await message.channel.send(
                        file=discord.File(fp=image_binary, filename='tiers.png'),
                        content=f"✅ Data saved for <@{message.author.id}>!"
                    )
    await bot.process_commands(message)

# Replace with your bot token

bot.run(TOKEN)