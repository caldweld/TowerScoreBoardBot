import google.generativeai as genai
import os
import re
import json
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-pro-002')

def download_image(image_url: str) -> Image.Image:
    """Download image from URL and return PIL Image object"""
    response = requests.get(image_url, timeout=20)
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
    
    TIER IMAGE (look for these specific indicators):
    - Contains "Tier 1", "Tier 2", "Tier 3", etc. (this is the PRIMARY indicator)
    - Shows tier progress data with wave numbers and coin amounts for each tier
    - May have a grid or list format showing multiple tiers
    - Contains tier-specific terminology like "Tier Progress" or tier numbers
    - If you see "Tier 1", "Tier 2", etc. anywhere in the image, it's ALWAYS a tier image
    
    STATS IMAGE (look for these indicators):
    - Shows individual game statistics like "Coins Earned", "Damage Dealt", "Enemies Destroyed"
    - Contains a list of various game metrics and achievements
    - Shows overall game performance data
    - Does NOT contain tier numbers (Tier 1, Tier 2, etc.)
    
    INVALID:
    - Not a game screenshot
    - Unclear what type of data it contains
    - Neither stats nor tier indicators are present
    
    IMPORTANT: If you see ANY tier numbers (Tier 1, Tier 2, etc.), classify as "tier" regardless of other content.
    
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

def validate_tier_detection(image: Image.Image, initial_classification: dict) -> dict:
    """Strict validation: Stats if 'Game Started'+'Coins Earned'+'Cash Earned'; else require ALL tiers 1-18, otherwise invalid."""
    text_prompt = (
        "Extract ALL readable text from this image. Return ONLY the raw text, no formatting, no JSON, no extra words."
    )
    try:
        text_response = model.generate_content([text_prompt, image])
        extracted_text = text_response.text.strip().lower()
        print(f"[DEBUG] Extracted text for validation: {extracted_text}")

        # 1) Stats check: must include all three labels
        has_game_started = "game started" in extracted_text
        has_coins_earned = "coins earned" in extracted_text
        has_cash_earned = "cash earned" in extracted_text
        if has_game_started and has_coins_earned and has_cash_earned:
            print("[DEBUG] Detected required stats labels → classifying as stats")
            return {
                "image_type": "stats",
                "confidence": 0.99,
                "reason": "Detected 'Game Started', 'Coins Earned', and 'Cash Earned'"
            }

        # 2) Tier check: require all tiers 1..18 present
        missing_tiers = []
        for i in range(1, 19):
            if f"tier {i}" not in extracted_text:
                missing_tiers.append(i)
        if not missing_tiers:
            print("[DEBUG] Detected all tier labels 1..18 → classifying as tier")
            return {
                "image_type": "tier",
                "confidence": 0.99,
                "reason": "Detected all tiers 1-18"
            }

        # 3) Otherwise invalid
        print(f"[DEBUG] Missing tier labels: {missing_tiers} → invalid")
        return {
            "image_type": "invalid",
            "confidence": 0.95,
            "reason": f"Missing tier labels: {', '.join(map(str, missing_tiers))}"
        }

    except Exception as e:
        print(f"[DEBUG] Error in validation: {e}")
        return initial_classification



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
    
    Look for:
    - Tier numbers (Tier 1, Tier 2, Tier 3, etc.)
    - Wave numbers for each tier
    - Coin amounts for each tier
    - Any summary statistics at the top or bottom
    
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
    - Look carefully for tier numbers in the image
    - If you can't find specific tier data, return empty values but don't fail
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

def process_image(image_url: str, force_type: str = None) -> dict:
    """Main function to process any game screenshot"""
    print(f"[DEBUG] Processing image: {image_url}")
    
    try:
        # Download and process image
        image = download_image(image_url)
        print(f"[DEBUG] Image downloaded successfully: {image.size}")
        
        # Detect image type
        type_result = detect_image_type(image)
        print(f"[DEBUG] Initial image type: {type_result['image_type']} (confidence: {type_result['confidence']})")
        
        # Secondary validation for tier detection
        validated_result = validate_tier_detection(image, type_result)
        print(f"[DEBUG] Validated image type: {validated_result['image_type']} (confidence: {validated_result['confidence']})")
        
        result = {
            "success": True,
            "image_type": validated_result["image_type"],
            "confidence": validated_result["confidence"],
            "reason": validated_result["reason"],
            "data": None
        }
        
        # Allow callers to force a specific type
        if force_type in ("stats", "tier"):
            print(f"[DEBUG] Force type override requested: {force_type}")
            result["image_type"] = force_type
            result["reason"] = f"Forced as {force_type} by caller"

        # Extract data based on (possibly forced) type
        if result["image_type"] == "stats":
            result["data"] = extract_stats_data(image)
        elif result["image_type"] == "tier":
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

 