import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dashboard_backend.models import UserStats, UserData, UserDataHistory
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database connection (using same config as dashboard_backend)
POSTGRES_USER = os.getenv("POSTGRES_USER", "toweruser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "yourpassword")
POSTGRES_DB = os.getenv("POSTGRES_DB", "towerscoreboard")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

print(f"[DEBUG] Database URL: {DATABASE_URL}")
print(f"[DEBUG] Using host: {POSTGRES_HOST}, port: {POSTGRES_PORT}, db: {POSTGRES_DB}")

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def parse_gemini_stats_to_sql(gemini_result: dict, discord_id: str, discord_name: str) -> dict:
    """
    Parse Gemini stats result and insert into UserStats table
    Returns: {"success": bool, "message": str, "stats_id": int}
    """
    try:
        # Validate input
        if not gemini_result.get("success") or gemini_result.get("image_type") != "stats":
            return {"success": False, "message": "Invalid stats data from Gemini"}
        
        stats_data = gemini_result.get("data", {})
        if not stats_data or "error" in stats_data:
            return {"success": False, "message": f"Stats extraction failed: {stats_data.get('error', 'Unknown error')}"}
        
        # Create database session
        db = SessionLocal()
        
        # Create new UserStats record
        new_stats = UserStats(
            discordid=discord_id,
            discordname=discord_name,
            game_started=stats_data.get("game_started"),
            coins_earned=stats_data.get("coins_earned"),
            cash_earned=stats_data.get("cash_earned"),
            stones_earned=stats_data.get("stones_earned"),
            damage_dealt=stats_data.get("damage_dealt"),
            enemies_destroyed=stats_data.get("enemies_destroyed"),
            waves_completed=stats_data.get("waves_completed"),
            upgrades_bought=stats_data.get("upgrades_bought"),
            workshop_upgrades=stats_data.get("workshop_upgrades"),
            workshop_coins_spent=stats_data.get("workshop_coins_spent"),
            research_completed=stats_data.get("research_completed"),
            lab_coins_spent=stats_data.get("lab_coins_spent"),
            free_upgrades=stats_data.get("free_upgrades"),
            interest_earned=stats_data.get("interest_earned"),
            orb_kills=stats_data.get("orb_kills"),
            death_ray_kills=stats_data.get("death_ray_kills"),
            thorn_damage=stats_data.get("thorn_damage"),
            waves_skipped=stats_data.get("waves_skipped")
        )
        
        # Insert into database
        db.add(new_stats)
        db.commit()
        db.refresh(new_stats)
        
        db.close()
        
        return {
            "success": True, 
            "message": f"Stats saved successfully! ID: {new_stats.id}",
            "stats_id": new_stats.id
        }
        
    except Exception as e:
        if 'db' in locals():
            db.rollback()
            db.close()
        return {"success": False, "message": f"Database error: {str(e)}"}

def parse_gemini_tier_to_sql(gemini_result: dict, discord_id: str, discord_name: str) -> dict:
    """
    Parse Gemini tier result and insert into UserData and UserDataHistory tables
    Returns: {"success": bool, "message": str, "tier_data": dict}
    """
    try:
        # Validate input
        if not gemini_result.get("success") or gemini_result.get("image_type") != "tier":
            return {"success": False, "message": "Invalid tier data from Gemini"}
        
        tier_data = gemini_result.get("data", {})
        if not tier_data or "error" in tier_data:
            return {"success": False, "message": f"Tier extraction failed: {tier_data.get('error', 'Unknown error')}"}
        
        # Create database session
        db = SessionLocal()
        
        # Prepare tier data for database
        tiers = tier_data.get("tiers", {})
        tier_values = {}
        
        for tier_num in range(1, 19):
            tier_key = str(tier_num)
            tier_info = tiers.get(tier_key, {})
            wave = tier_info.get("wave", 0)
            coins = tier_info.get("coins", "0")
            
            # Format: "Wave: {wave} Coins: {coins}" (e.g., "Wave: 11453 Coins: 16.78B")
            tier_values[f"T{tier_num}"] = f"Wave: {wave} Coins: {coins}"
        
        # Update or insert UserData
        existing_user = db.query(UserData).filter(UserData.discordid == discord_id).first()
        
        if existing_user:
            # Update existing user
            for tier_key, tier_value in tier_values.items():
                setattr(existing_user, tier_key, tier_value)
            existing_user.discordname = discord_name
        else:
            # Create new user
            new_user = UserData(
                discordid=discord_id,
                discordname=discord_name,
                **tier_values
            )
            db.add(new_user)
        
        # Add to history
        new_history = UserDataHistory(
            discordid=discord_id,
            discordname=discord_name,
            **tier_values
        )
        db.add(new_history)
        
        # Commit changes
        db.commit()
        db.close()
        
        return {
            "success": True,
            "message": f"Tier data saved successfully!",
            "tier_data": {
                "summary": tier_data.get("summary", {}),
                "tiers_updated": len([v for v in tier_values.values() if v != "Wave: 0 Coins: 0"])
            }
        }
        
    except Exception as e:
        if 'db' in locals():
            db.rollback()
            db.close()
        return {"success": False, "message": f"Database error: {str(e)}"}

def process_gemini_result(gemini_result: dict, discord_id: str, discord_name: str) -> dict:
    """
    Main function to process Gemini result and save to appropriate database table
    Returns: {"success": bool, "message": str, "data": dict}
    """
    print(f"[DEBUG] Processing Gemini result for {discord_name} ({discord_id})")
    print(f"[DEBUG] Image type: {gemini_result.get('image_type')}")
    
    if gemini_result.get("image_type") == "stats":
        return parse_gemini_stats_to_sql(gemini_result, discord_id, discord_name)
    elif gemini_result.get("image_type") == "tier":
        return parse_gemini_tier_to_sql(gemini_result, discord_id, discord_name)
    else:
        return {"success": False, "message": f"Unsupported image type: {gemini_result.get('image_type')}"}

# Test function
def test_sql_parser():
    """Test the SQL parser with sample data"""
    print("🧪 Testing SQL Parser")
    print("=" * 50)
    
    # Sample stats data
    sample_stats = {
        "success": True,
        "image_type": "stats",
        "confidence": 1.0,
        "data": {
            "game_started": "22052025",
            "coins_earned": "8.32B",
            "cash_earned": "$105.97B",
            "stones_earned": "855",
            "damage_dealt": "2.260",
            "enemies_destroyed": "40.10M",
            "waves_completed": "304.15K",
            "upgrades_bought": "243.54K",
            "workshop_upgrades": "4.08K",
            "workshop_coins_spent": "3.96B",
            "research_completed": "400",
            "lab_coins_spent": "3.76B",
            "free_upgrades": "495.75K",
            "interest_earned": "$15.03M",
            "orb_kills": "29.07M",
            "death_ray_kills": "0",
            "thorn_damage": "525.69S",
            "waves_skipped": "18004"
        }
    }
    
    # Test stats parsing
    result = process_gemini_result(sample_stats, "123456789", "TestUser")
    print(f"Stats Test Result: {result}")
    
    # Sample tier data
    sample_tier = {
        "success": True,
        "image_type": "tier",
        "confidence": 1.0,
        "data": {
            "summary": {"thorn_damage": "1.04D", "waves_skipped": 71572},
            "tiers": {
                "1": {"wave": 11453, "coins": "16.78B"},
                "2": {"wave": 6520, "coins": "11.46B"},
                "3": {"wave": 5873, "coins": "13.43B"}
            }
        }
    }
    
    # Test tier parsing
    result = process_gemini_result(sample_tier, "123456789", "TestUser")
    print(f"Tier Test Result: {result}")

if __name__ == "__main__":
    test_sql_parser() 