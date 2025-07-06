import pytesseract
import re
from PIL import Image
from io import BytesIO
import requests

STAT_FIELDS = [
    ("game_started", r"Game Started\s+([\w\s]+\d{4})"),
    ("coins_earned", r"Coins Earned\s+([\d.,]+[KMBTQ]?)"),
    ("cash_earned", r"Cash Earned\s+([\$\d.,]+[KMBTQ]?)"),
    ("stones_earned", r"Stones Earned\s+([\d.,]+[KMBTQ]?)"),
    ("damage_dealt", r"Damage Dealt\s+([\d.,]+[KMBTQ]?)"),
    ("enemies_destroyed", r"Enemies Destroyed\s+([\d.,]+[KMBTQ]?)"),
    ("waves_completed", r"Waves Completed\s+([\d.,]+[KMBTQ]?)"),
    ("upgrades_bought", r"Upgrades Bought\s+([\d.,]+[KMBTQ]?)"),
    ("workshop_upgrades", r"Workshop Upgrades\s+([\d.,]+[KMBTQ]?)"),
    ("workshop_coins_spent", r"Workshop Coins Spent\s+([\d.,]+[KMBTQ]?)"),
    ("research_completed", r"Research Completed\s+([\d.,]+[KMBTQ]?)"),
    ("lab_coins_spent", r"Lab Coins Spent\s+([\d.,]+[KMBTQ]?)"),
    ("free_upgrades", r"Free Upgrades\s+([\d.,]+[KMBTQ]?)"),
    ("interest_earned", r"Interest Earned\s+([\$\d.,]+[KMBTQ]?)"),
    ("orb_kills", r"Orb Kills\s+([\d.,]+[KMBTQ]?)"),
    ("death_ray_kills", r"Death Ray Kills\s+([\d.,]+[KMBTQ]?)"),
    ("thorn_damage", r"Thorn Damage\s+([\d.,]+[KMBTQ]?)"),
    ("waves_skipped", r"Waves Skipped\s+([\d.,]+[KMBTQ]?)"),
]

def normalize_stat_value(val):
    if not val:
        return val
    # Match pattern like 419.720 or 1.06B
    m = re.match(r"^(\d+\.\d{2})([A-Z0-9])$", val)
    if m:
        num, unit = m.groups()
        if unit == '0':
            unit = 'O'
        return f"{num}{unit}"
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