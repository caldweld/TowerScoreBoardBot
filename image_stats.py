import pytesseract
import re
from PIL import Image
from io import BytesIO
import requests

STAT_FIELDS = [
    ("game_started", r"Game Started\s+([\w\s]+\d{4})"),
    ("coins_earned", r"Coins Earned\s+([\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("cash_earned", r"Cash Earned\s+([\$\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("stones_earned", r"Stones Earned\s+([\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("damage_dealt", r"Damage Dealt\s+([\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("enemies_destroyed", r"Enemies Destroyed\s+([\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("waves_completed", r"Waves Completed\s+([\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("upgrades_bought", r"Upgrades Bought\s+([\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("workshop_upgrades", r"Workshop Upgrades\s+([\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("workshop_coins_spent", r"Workshop Coins Spent\s+([\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("research_completed", r"Research Completed\s+([\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("lab_coins_spent", r"Lab Coins Spent\s+([\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("free_upgrades", r"Free Upgrades\s+([\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("interest_earned", r"Interest Earned\s+([\$\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("orb_kills", r"Orb Kills\s+([\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("death_ray_kills", r"Death Ray Kills\s+([\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("thorn_damage", r"Thorn Damage\s+([\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
    ("waves_skipped", r"Waves Skipped\s+([\d.,]+(?:[KMBTqQsSOND]|aa|ab|ac|ad)?)"),
]

def normalize_stat_value(val):
    if not val:
        return val
    val = val.strip()
    
    # Define all possible suffixes in order
    suffixes = ['K', 'M', 'B', 'T', 'q', 'Q', 's', 'S', 'O', 'N', 'D', 'aa', 'ab', 'ac', 'ad']
    
    # If it matches pattern like 419.720 or 1.06B, treat the last char as a unit
    # Handle 3 decimal places where the last digit might be a suffix
    m = re.match(r"^(\d+\.\d{3})$", val)
    if m:
        num = m.group(1)
        # Extract the last digit and treat it as a suffix
        base_num = num[:-1]  # Remove last digit
        last_digit = num[-1]  # Get last digit
        # Convert digit to appropriate suffix
        if last_digit == '0':
            suffix = 'O'
        else:
            # For other digits, we might need to handle differently
            # For now, just return the base number
            return base_num
        return f"{base_num}{suffix}"
    
    # If it's a valid float, just return as is
    try:
        float(val)
        return val
    except:
        return val

def extract_stats_from_image_url(image_url: str) -> dict:
    response = requests.get(image_url)
    response.raise_for_status()
    image = Image.open(BytesIO(response.content))
    return extract_stats_from_image(image)

def extract_stats_from_image(image: Image.Image) -> dict:
    ocr_text = pytesseract.image_to_string(image)
    return extract_stats_from_text(ocr_text)

def extract_stats_from_text(ocr_text: str) -> dict:
    stats = {}
    for field, pattern in STAT_FIELDS:
        match = re.search(pattern, ocr_text, re.IGNORECASE)
        value = match.group(1).strip() if match else None
        # Normalize all numeric stat fields
        if field != 'game_started' and value:
            value = normalize_stat_value(value)
        stats[field] = value
    stats['raw_text'] = ocr_text
    return stats 