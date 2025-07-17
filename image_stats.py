import pytesseract
import re
from PIL import Image
from io import BytesIO
import requests

STAT_FIELDS = [
    ("game_started", r"Game Started\s+([\w\s]+\d{4})"),
    ("coins_earned", r"Coins Earned\s+([\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("cash_earned", r"Cash Earned\s+([\$\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("stones_earned", r"Stones Earned\s+([\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("damage_dealt", r"Damage Dealt\s+([\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("enemies_destroyed", r"Enemies Destroyed\s+([\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("waves_completed", r"Waves Completed\s+([\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("upgrades_bought", r"Upgrades Bought\s+([\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("workshop_upgrades", r"Workshop Upgrades\s+([\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("workshop_coins_spent", r"Workshop Coins Spent\s+([\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("research_completed", r"Research Completed\s+([\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("lab_coins_spent", r"Lab Coins Spent\s+([\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("free_upgrades", r"Free Upgrades\s+([\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("interest_earned", r"Interest Earned\s+([\$\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("orb_kills", r"Orb Kills\s+([\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("death_ray_kills", r"Death Ray Kills\s+([\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("thorn_damage", r"Thorn Damage\s+([\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
    ("waves_skipped", r"Waves Skipped\s+([\d.,]+[KMBTqQsSOND]|aa|ab|ac|ad)"),
]

def normalize_stat_value(val):
    if not val:
        return val
    val = val.strip()
    print(f"[DEBUG] Raw stat value before normalization: '{val}'")
    
    # Define all possible suffixes in order
    suffixes = ['K', 'M', 'B', 'T', 'q', 'Q', 's', 'S', 'O', 'N', 'D', 'aa', 'ab', 'ac', 'ad']
    
    # If it matches pattern like 419.720 or 1.06B, treat the last char as a unit
    # But be careful with 3rd decimal place - if it's a letter, it's a suffix
    m = re.match(r"^(\d+\.\d{2})([A-Za-z0-9])$", val)
    if m:
        num, unit = m.groups()
        # Check if the unit is a valid suffix
        if unit in suffixes or unit.upper() in suffixes:
            if unit == '0':
                unit = 'O'
            elif unit.lower() in ['q', 's']:
                unit = unit.lower()  # Keep lowercase for q and s
            else:
                unit = unit.upper()  # Convert to uppercase for others
            return f"{num}{unit}"
    
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
    print(f"[DEBUG] Raw OCR text:\n{ocr_text}")
    stats = {}
    for field, pattern in STAT_FIELDS:
        match = re.search(pattern, ocr_text, re.IGNORECASE)
        value = match.group(1).strip() if match else None
        print(f"[DEBUG] {field}: extracted='{value}'")
        # Normalize all numeric stat fields
        if field != 'game_started' and value:
            value = normalize_stat_value(value)
            print(f"[DEBUG] {field}: normalized='{value}'")
        stats[field] = value
    stats['raw_text'] = ocr_text
    return stats 