import discord
import os
import sqlite3
import pytesseract
import requests
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # loads environment variables from .env file

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

if TOKEN is None:
    raise ValueError("No Discord bot token found in environment variables.")


# Set up intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Database setup
conn = sqlite3.connect("data.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_data (
    discordid TEXT PRIMARY KEY,
    discordname TEXT,
    T1 TEXT, T2 TEXT, T3 TEXT, T4 TEXT, T5 TEXT, T6 TEXT,
    T7 TEXT, T8 TEXT, T9 TEXT, T10 TEXT, T11 TEXT, T12 TEXT,
    T13 TEXT, T14 TEXT, T15 TEXT, T16 TEXT, T17 TEXT, T18 TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_data_history (
    discordid TEXT,
    discordname TEXT,
    timestamp TEXT,
    T1 TEXT, T2 TEXT, T3 TEXT, T4 TEXT, T5 TEXT, T6 TEXT,
    T7 TEXT, T8 TEXT, T9 TEXT, T10 TEXT, T11 TEXT, T12 TEXT,
    T13 TEXT, T14 TEXT, T15 TEXT, T16 TEXT, T17 TEXT, T18 TEXT
)
""")
conn.commit()

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
    values = [discord_id, discord_name] + tier_data
    placeholders = ','.join(['?'] * len(values))
    cursor.execute(f"""
        INSERT OR REPLACE INTO user_data (
            discordid, discordname,
            T1, T2, T3, T4, T5, T6,
            T7, T8, T9, T10, T11, T12,
            T13, T14, T15, T16, T17, T18
        ) VALUES ({placeholders})
    """, values)

    timestamp = datetime.utcnow().isoformat()
    values_with_time = [discord_id, discord_name, timestamp] + tier_data
    placeholders_hist = ','.join(['?'] * len(values_with_time))

    # Check if identical record exists
    cursor.execute("""
        SELECT 1 FROM user_data_history
        WHERE discordid = ? AND T1 = ? AND T2 = ? AND T3 = ? AND T4 = ? AND T5 = ? AND T6 = ? AND
              T7 = ? AND T8 = ? AND T9 = ? AND T10 = ? AND T11 = ? AND T12 = ? AND
              T13 = ? AND T14 = ? AND T15 = ? AND T16 = ? AND T17 = ? AND T18 = ?
    """, [discord_id] + tier_data)

    if not cursor.fetchone():
        cursor.execute(f"""
            INSERT INTO user_data_history (
                discordid, discordname, timestamp,
                T1, T2, T3, T4, T5, T6,
                T7, T8, T9, T10, T11, T12,
                T13, T14, T15, T16, T17, T18
            ) VALUES ({placeholders_hist})
        """, values_with_time)

    conn.commit()

def get_user_data(discord_id):
    cursor.execute("SELECT T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18 FROM user_data WHERE discordid = ?", (discord_id,))
    return cursor.fetchone()

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

@client.event
async def on_ready():
    print(f"✅ Bot is online as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower().startswith("!mydata"):
        data = get_user_data(str(message.author.id))
        if data:
            # Send as text here (optional)
            formatted = "Tier | Wave     | Coins\n" + "-----|----------|--------\n"
            for i, entry in enumerate(data):
                wave_match = re.search(r"Wave: (\S+)", entry)
                coin_match = re.search(r"Coins: (\S+)", entry)
                wave = wave_match.group(1) if wave_match else "0"
                coins = coin_match.group(1) if coin_match else "0"
                formatted += f"T{i+1:<3} | {wave:<8} | {coins}\n"
            await message.channel.send(f"📊 Your saved tiers:\n```\n{formatted}```")
        else:
            await message.channel.send("❌ No data found. Upload an image to start tracking.")
        return

    if message.attachments:
        for attachment in message.attachments:
            if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg')):

                response = requests.get(attachment.url)
                image = Image.open(BytesIO(response.content))
                custom_config = r'--oem 3 --psm 6'
                text = pytesseract.image_to_string(image, config=custom_config)

                # Debug raw OCR output
                #print("\n--- OCR RAW TEXT ---")
                #print(text)
                #print("--- END RAW TEXT ---\n")
                # NEW: Only process if image starts with 'STATS'
                stats_line_index = find_stats_line(text)
                if stats_line_index == -1:
                    return
                await message.channel.send("🕵️ Processing image...")

                # Optional: send raw OCR text for inspection (trimmed)
                #await message.channel.send(f"🪵 Raw OCR output:\n```\n{text[:1900]}```")

                tiers = extract_tiers(text)
                save_user_data(str(message.author.id), str(message.author.name), tiers)

                # Create image and send it
                img = create_canvas_table(tiers)
                with BytesIO() as image_binary:
                    img.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    await message.channel.send(
                        file=discord.File(fp=image_binary, filename='tiers.png'),
                        content=f"✅ Data saved for <@{message.author.id}>!"
                    )
    if message.content.lower().startswith("!leaderboard"):
        cursor.execute("SELECT discordname, T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18 FROM user_data")
        users = cursor.fetchall()

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

            # Defensive fallback if no tiers found
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

            if len(lines) > 12:  # Limit output for neatness
                break

        leaderboard_text = "\n".join(lines)
        await message.channel.send(f"📊 Leaderboard:\n```\n{leaderboard_text}```")
        return
    if message.content.lower().startswith("!leaderwaves"):
        cursor.execute("SELECT discordname, T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18 FROM user_data")
        users = cursor.fetchall()

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

            if len(lines) > 12:  # limit output for neatness
                break

        leaderboard_text = "\n".join(lines)
        await message.channel.send(f"📊 Leaderwaves:\n```\n{leaderboard_text}```")
        return
    if message.content.lower().startswith("!leadercoins"):
        cursor.execute("SELECT discordname, T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18 FROM user_data")
        users = cursor.fetchall()

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
                        coins_list.append(f"T{i+1}: {coins}")

            if not coins_list:
                coins_list.append("No coins recorded")

            coins_str = " ; ".join(coins_list)
            line = f"{name} | {coins_str}"
            lines.append(line)

            if len(lines) > 12:  # limit output for neatness
                break

        leaderboard_text = "\n".join(lines)
        await message.channel.send(f"📊 Leadercoins:\n```\n{leaderboard_text}```")
        return
    if message.content.lower().startswith("!leaderwave"):
        parts = message.content.lower().split()
        if len(parts) < 2:
            await message.channel.send("❌ Please specify a tier, e.g. `!leaderwave t1`")
            return
        
        tier_input = parts[1]
        match = re.match(r"t(\d+)", tier_input)
        if not match:
            await message.channel.send("❌ Invalid tier format. Use e.g. `t1`, `t2`, etc.")
            return
        
        tier_num = int(match.group(1))
        if not (1 <= tier_num <= 18):
            await message.channel.send("❌ Tier number must be between 1 and 18.")
            return

        cursor.execute(f"SELECT discordname, T{tier_num} FROM user_data")
        users = cursor.fetchall()

        # Parse and filter only entries with wave > 0
        results = []
        for name, tier_str in users:
            if not tier_str:
                continue
            wave, _ = parse_wave_coins(tier_str)
            if wave > 0:
                results.append((name, wave))

        # Sort descending by wave
        results.sort(key=lambda x: x[1], reverse=True)

        # Take top 5
        top5 = results[:5]

        header = f"Top 5 Players for Tier {tier_num} by Wave"
        lines = [header, "-" * len(header)]

        for name, wave in top5:
            lines.append(f"{name} Wave: {wave}")

        leaderboard_text = "\n".join(lines)
        await message.channel.send(f"📊 {header}:\n```\n{leaderboard_text}```")
        return
    if message.content.startswith("!showdata"):
        response = ""

        cursor.execute("SELECT * FROM user_data")
        rows = cursor.fetchall()
        if rows:
            response += "**Current User Data:**\n"
            for row in rows:
                discordname = row[1]
                tiers = "\n".join([f"T{i+1}: {row[i+2]}" for i in range(18)])
                response += f"__{discordname}__\n{tiers}\n\n"
        else:
            response += "No current user data found.\n"

        cursor.execute("SELECT * FROM user_data_history")
        rows = cursor.fetchall()
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
            await message.channel.send(f"```{chunk}```")

# Replace with your bot token


client.run(TOKEN)