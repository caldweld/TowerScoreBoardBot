import pytesseract
import re
from PIL import Image
from io import BytesIO
import requests

def extract_tier_data_from_image_url(image_url: str) -> dict:
    """Extract tier data from a tier screenshot URL"""
    response = requests.get(image_url)
    response.raise_for_status()
    image = Image.open(BytesIO(response.content))
    return extract_tier_data_from_image(image)

def extract_tier_data_from_image(image: Image.Image) -> dict:
    """Extract tier data from a tier screenshot image"""
    ocr_text = pytesseract.image_to_string(image)
    return extract_tier_data_from_text(ocr_text)

def extract_tier_data_from_text(ocr_text: str) -> dict:
    """Extract tier data from OCR text"""
    print(f"[DEBUG] Raw OCR text from tier image:\n{ocr_text}")
    
    tier_data = {
        'tiers': {},
        'summary_stats': {},
        'raw_text': ocr_text
    }
    
    # Extract summary stats (like Thorn Damage, Waves Skipped)
    summary_patterns = [
        (r"Thorn Damage\s+([\d.,]+[KMBTqQsSOND]?|aa|ab|ac|ad)", "thorn_damage"),
        (r"Waves Skipped\s+([\d.,]+[KMBTqQsSOND]?|aa|ab|ac|ad)", "waves_skipped"),
    ]
    
    for pattern, field_name in summary_patterns:
        match = re.search(pattern, ocr_text, re.IGNORECASE)
        if match:
            tier_data['summary_stats'][field_name] = match.group(1).strip()
            print(f"[DEBUG] {field_name}: {match.group(1).strip()}")
    
    # Extract tier data (Tier X: Wave Y, Coins Z)
    tier_pattern = r"Tier\s+(\d+).*?Wave.*?(\d+).*?Coins.*?([\d.,]+[KMBTqQsSOND]?|aa|ab|ac|ad)"
    tier_matches = re.finditer(tier_pattern, ocr_text, re.IGNORECASE | re.DOTALL)
    
    for match in tier_matches:
        tier_num = int(match.group(1))
        wave_count = int(match.group(2))
        coins = match.group(3).strip()
        
        tier_data['tiers'][tier_num] = {
            'wave': wave_count,
            'coins': coins
        }
        print(f"[DEBUG] Tier {tier_num}: Wave {wave_count}, Coins {coins}")
    
    return tier_data

def format_tier_data(tier_data: dict) -> str:
    """Format tier data into a readable string"""
    if not tier_data.get('tiers'):
        return "No tier data found"
    
    output = "📊 **Tier Progress Data:**\n\n"
    
    # Add summary stats if available
    if tier_data.get('summary_stats'):
        output += "**Summary Stats:**\n"
        for stat_name, value in tier_data['summary_stats'].items():
            formatted_name = stat_name.replace('_', ' ').title()
            output += f"• {formatted_name}: {value}\n"
        output += "\n"
    
    # Add tier data
    output += "**Tier Progress:**\n"
    for tier_num in sorted(tier_data['tiers'].keys()):
        tier_info = tier_data['tiers'][tier_num]
        output += f"• **Tier {tier_num}**: Wave {tier_info['wave']:,}, Coins {tier_info['coins']}\n"
    
    return output

# Example usage
if __name__ == "__main__":
    # This would be used when testing with a file
    pass 