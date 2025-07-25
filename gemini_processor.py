import google.generativeai as genai
import os
import json
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-pro')

def download_image(image_url: str) -> Image.Image:
    """Download image from URL and return PIL Image object"""
    response = requests.get(image_url)
    response.raise_for_status()
    return Image.open(BytesIO(response.content))

def clean_gemini_response(response_text: str) -> str:
    """Clean Gemini response by removing markdown code blocks"""
    response_text = response_text.strip()
    if not response_text:
        raise ValueError("Empty response from Gemini")
    
    # Remove markdown code blocks if present
    if response_text.startswith('```json'):
        response_text = response_text[7:]  # Remove ```json
    if response_text.startswith('```'):
        response_text = response_text[3:]  # Remove ```
    if response_text.endswith('```'):
        response_text = response_text[:-3]  # Remove trailing ```
    
    return response_text.strip()

def normalize_stat_value(value: str) -> str:
    """Normalize stat values to fix common OCR misreads and formatting"""
    if not value or value == "null":
        return value
    
    # Fix the 3-decimal issue: 2.260 -> 2.26O
    import re
    if re.match(r"^(\d+\.\d{3})$", value):
        # Convert last digit '0' to 'O' for 3-decimal numbers
        value = value[:-1] + "O"
        print(f"[DEBUG] Normalized {value[:-1] + '0'} -> {value}")
    
    # Add space before suffixes: 15.03M -> 15.03 M
    # Match patterns like: 123.45K, 1.23M, 456.78B, 789.01T, 123.45O, $105.97B, etc.
    suffix_pattern = r'^(\$?)(\d+(?:\.\d+)?)([KMBTOS])$'
    match = re.match(suffix_pattern, value)
    if match:
        currency_symbol = match.group(1)  # $ or empty
        number_part = match.group(2)
        suffix = match.group(3)
        value = f"{currency_symbol}{number_part} {suffix}"
        print(f"[DEBUG] Formatted suffix: {match.group(0)} -> {value}")
    
    return value

def detect_image_type(image: Image.Image) -> dict:
    """Detect if image is stats, tier, or invalid"""
    prompt = """
    Analyze this game screenshot and determine its type.
    
    You must respond with ONLY a valid JSON object in this exact format:
    {
        "image_type": "stats" | "tier" | "invalid",
        "confidence": 0.0-1.0,
        "reason": "brief explanation of why this classification was made"
    }
    
    Classification rules:
    - "stats": Shows individual game statistics like "Coins Earned", "Damage Dealt", "Enemies Destroyed", etc.
    - "tier": Shows tier progress data with "Tier 1", "Tier 2", etc. and wave/coin information
    - "invalid": Not a game screenshot or unclear what type of data it contains
    
    Do not include any other text, only the JSON object.
    """
    
    try:
        response = model.generate_content([prompt, image])
        print(f"[DEBUG] Raw Gemini response: {response.text}")
        
        # Clean the response text
        response_text = clean_gemini_response(response.text)
        print(f"[DEBUG] Cleaned response text: {response_text}")
            
        result = json.loads(response_text)
        print(f"[DEBUG] Image type detection result: {result}")
        return result
    except Exception as e:
        print(f"[DEBUG] Error in image type detection: {e}")
        print(f"[DEBUG] Response text was: {getattr(response, 'text', 'No response')}")
        return {
            "image_type": "invalid",
            "confidence": 0.0,
            "reason": f"Error processing image: {str(e)}"
        }

def extract_stats_data(image: Image.Image) -> dict:
    """Extract stats data from a stats screenshot"""
    prompt = """
    Extract game statistics from this screenshot.
    
    You must respond with ONLY a valid JSON object in this exact format:
    {
        "game_started": "DDMMYYYY format",
        "coins_earned": "value with suffix (e.g., 616.32B)",
        "cash_earned": "value with suffix (e.g., $1.01T)",
        "stones_earned": "value with suffix or number",
        "damage_dealt": "value with suffix (e.g., 419.72O)",
        "enemies_destroyed": "value with suffix",
        "waves_completed": "value with suffix",
        "upgrades_bought": "value with suffix",
        "workshop_upgrades": "value with suffix",
        "workshop_coins_spent": "value with suffix",
        "research_completed": "value with suffix",
        "lab_coins_spent": "value with suffix",
        "free_upgrades": "value with suffix",
        "interest_earned": "value with suffix",
        "orb_kills": "value with suffix",
        "death_ray_kills": "value with suffix",
        "thorn_damage": "value with suffix",
        "waves_skipped": "value with suffix"
    }
    
    Rules:
    - Use null for missing values
    - Keep original suffixes (K, M, B, T, O, etc.)
    - For game_started, convert to DDMMYYYY format
    - Be very precise with the values
    
    Do not include any other text, only the JSON object.
    """
    
    try:
        response = model.generate_content([prompt, image])
        print(f"[DEBUG] Raw Gemini stats response: {response.text}")
        
        # Clean the response text
        response_text = clean_gemini_response(response.text)
        print(f"[DEBUG] Cleaned stats response text: {response_text}")
            
        result = json.loads(response_text)
        
        # Normalize stat values to fix OCR misreads
        if result and isinstance(result, dict):
            for key, value in result.items():
                if key != "game_started" and value:  # Don't normalize dates
                    result[key] = normalize_stat_value(str(value))
        
        print(f"[DEBUG] Stats extraction result: {result}")
        return result
    except Exception as e:
        print(f"[DEBUG] Error in stats extraction: {e}")
        print(f"[DEBUG] Response text was: {getattr(response, 'text', 'No response')}")
        return {"error": f"Failed to extract stats: {str(e)}"}

def extract_tier_data(image: Image.Image) -> dict:
    """Extract tier data from a tier screenshot"""
    prompt = """
    Extract tier progress data from this screenshot.
    
    Return ONLY a JSON object with this exact format:
    {
        "summary": {
            "thorn_damage": "value with suffix",
            "waves_skipped": "number"
        },
        "tiers": {
            "1": {"wave": number, "coins": "value with suffix"},
            "2": {"wave": number, "coins": "value with suffix"},
            "3": {"wave": number, "coins": "value with suffix"},
            "4": {"wave": number, "coins": "value with suffix"},
            "5": {"wave": number, "coins": "value with suffix"},
            "6": {"wave": number, "coins": "value with suffix"},
            "7": {"wave": number, "coins": "value with suffix"},
            "8": {"wave": number, "coins": "value with suffix"},
            "9": {"wave": number, "coins": "value with suffix"},
            "10": {"wave": number, "coins": "value with suffix"},
            "11": {"wave": number, "coins": "value with suffix"},
            "12": {"wave": number, "coins": "value with suffix"},
            "13": {"wave": number, "coins": "value with suffix"},
            "14": {"wave": number, "coins": "value with suffix"},
            "15": {"wave": number, "coins": "value with suffix"},
            "16": {"wave": number, "coins": "value with suffix"},
            "17": {"wave": number, "coins": "value with suffix"},
            "18": {"wave": number, "coins": "value with suffix"}
        }
    }
    
    Rules:
    - Use 0 for wave and "0" for coins if tier has no data
    - Keep original suffixes (K, M, B, T, etc.)
    - Be very precise with the values
    """
    
    try:
        response = model.generate_content([prompt, image])
        print(f"[DEBUG] Raw Gemini tier response: {response.text}")
        
        # Clean the response text
        response_text = clean_gemini_response(response.text)
        print(f"[DEBUG] Cleaned tier response text: {response_text}")
            
        result = json.loads(response_text)
        print(f"[DEBUG] Tier extraction result: {result}")
        return result
    except Exception as e:
        print(f"[DEBUG] Error in tier extraction: {e}")
        return {"error": f"Failed to extract tier data: {str(e)}"}

def process_image(image_url: str) -> dict:
    """Main function to process any game screenshot"""
    print(f"[DEBUG] Processing image: {image_url}")
    
    try:
        # Download and process image
        image = download_image(image_url)
        print(f"[DEBUG] Image downloaded successfully: {image.size}")
        
        # Detect image type
        type_result = detect_image_type(image)
        print(f"[DEBUG] Image type: {type_result['image_type']} (confidence: {type_result['confidence']})")
        
        result = {
            "success": True,
            "image_type": type_result["image_type"],
            "confidence": type_result["confidence"],
            "reason": type_result["reason"],
            "data": None
        }
        
        # Extract data based on type
        if type_result["image_type"] == "stats":
            result["data"] = extract_stats_data(image)
        elif type_result["image_type"] == "tier":
            result["data"] = extract_tier_data(image)
        else:
            result["data"] = {"error": "Invalid image type"}
            
        return result
        
    except Exception as e:
        print(f"[DEBUG] Error processing image: {e}")
        return {
            "success": False,
            "error": str(e),
            "image_type": "unknown",
            "confidence": 0.0,
            "reason": f"Processing error: {str(e)}",
            "data": None
        }

# Test function for debugging
def test_image_processing(image_url: str):
    """Test function to process an image and show detailed debug info"""
    print("=" * 50)
    print("GEMINI IMAGE PROCESSING TEST")
    print("=" * 50)
    
    result = process_image(image_url)
    
    print("\n" + "=" * 50)
    print("FINAL RESULT:")
    print("=" * 50)
    print(json.dumps(result, indent=2))
    
    return result 