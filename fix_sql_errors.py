#!/usr/bin/env python3
"""
SQL Table Error Fixer Script
Dynamically fixes common errors in the user_stats table including:
- Date format standardization
- Monetary value formatting
- Spacing consistency
- Data validation
"""

import os
import re
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
POSTGRES_USER = os.getenv("POSTGRES_USER", "toweruser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "yourpassword")
POSTGRES_DB = os.getenv("POSTGRES_DB", "towerscoreboard")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Define suffixes for number formatting
SUFFIXES = {
    'K': 1_000,
    'M': 1_000_000,
    'B': 1_000_000_000,
    'T': 1_000_000_000_000,
    'q': 1_000_000_000_000_000,
    'Q': 1_000_000_000_000_000_000,
    's': 1_000_000_000_000_000_000_000,
    'S': 1_000_000_000_000_000_000_000_000,
    'O': 1_000_000_000_000_000_000_000_000_000,
    'N': 1_000_000_000_000_000_000_000_000_000_000,
    'D': 1_000_000_000_000_000_000_000_000_000_000_000,
    'aa': 1_000_000_000_000_000_000_000_000_000_000_000_000,
    'ab': 1_000_000_000_000_000_000_000_000_000_000_000_000_000,
    'ac': 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000,
    'ad': 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000
}

def fix_date_format(date_str):
    """Fix date format to dd-mm-yyyy"""
    if not date_str or not isinstance(date_str, str):
        return date_str
    
    # Remove any non-digit characters
    date_str = re.sub(r'[^\d]', '', date_str)
    
    # Check if it's in DDMMYYYY format (8 digits)
    if len(date_str) == 8:
        try:
            day = int(date_str[:2])
            month = int(date_str[2:4])
            year = int(date_str[4:8])
            
            # Validate date components
            if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                return f"{day:02d}-{month:02d}-{year:04d}"
        except ValueError:
            pass
    
    # If it's already in dd-mm-yyyy format, return as is
    if re.match(r'^\d{2}-\d{2}-\d{4}$', date_str):
        return date_str
    
    # If it's in yyyy-mm-dd format, convert to dd-mm-yyyy
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        try:
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
            return parsed_date.strftime('%d-%m-%Y')
        except ValueError:
            pass
    
    # If it's a different format, try to parse it
    try:
        # Try common date formats
        for fmt in ['%Y%m%d', '%d%m%Y', '%m%d%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%d-%m-%Y')
            except ValueError:
                continue
    except:
        pass
    
    return date_str  # Return original if can't parse

def fix_monetary_value(value):
    """Fix monetary values to have consistent $ prefix and spacing"""
    if not value or not isinstance(value, str):
        return value
    
    # Remove existing $ and clean up
    cleaned = value.replace('$', '').strip()
    
    # Check if it's a monetary field (cash_earned, interest_earned)
    # For now, we'll add $ to all values that look like money
    if re.match(r'^[\d.,]+(\s*[KMBTqQsSOND]|aa|ab|ac|ad)?$', cleaned):
        # Add space before suffix if missing
        for suffix in sorted(SUFFIXES.keys(), key=len, reverse=True):
            if cleaned.endswith(suffix) and not cleaned.endswith(f' {suffix}'):
                cleaned = cleaned[:-len(suffix)] + f' {suffix}'
                break
        
        return f"${cleaned}"
    
    return value

def fix_number_formatting(value):
    """Fix number formatting to have consistent spacing before suffixes"""
    if not value or not isinstance(value, str):
        return value
    
    # Remove $ prefix for processing
    has_dollar = value.startswith('$')
    cleaned = value.replace('$', '').strip()
    
    # Add space before suffix if missing
    for suffix in sorted(SUFFIXES.keys(), key=len, reverse=True):
        if cleaned.endswith(suffix) and not cleaned.endswith(f' {suffix}'):
            cleaned = cleaned[:-len(suffix)] + f' {suffix}'
            break
    
    # Restore $ prefix if it was there
    if has_dollar:
        return f"${cleaned}"
    
    return cleaned

def validate_and_fix_row(row_data):
    """Validate and fix a single row of data"""
    fixes = {}
    
    # Fix game_started date format
    if 'game_started' in row_data:
        original_date = row_data['game_started']
        fixed_date = fix_date_format(original_date)
        if fixed_date != original_date:
            fixes['game_started'] = (original_date, fixed_date)
            row_data['game_started'] = fixed_date
    
    # Fix monetary values
    monetary_fields = ['cash_earned', 'interest_earned']
    for field in monetary_fields:
        if field in row_data:
            original_value = row_data[field]
            fixed_value = fix_monetary_value(original_value)
            if fixed_value != original_value:
                fixes[field] = (original_value, fixed_value)
                row_data[field] = fixed_value
    
    # Fix number formatting for all numeric fields
    numeric_fields = [
        'coins_earned', 'stones_earned', 'damage_dealt', 'enemies_destroyed',
        'waves_completed', 'upgrades_bought', 'workshop_upgrades', 'workshop_coins_spent',
        'research_completed', 'lab_coins_spent', 'free_upgrades', 'orb_kills',
        'death_ray_kills', 'thorn_damage', 'waves_skipped'
    ]
    
    for field in numeric_fields:
        if field in row_data:
            original_value = row_data[field]
            fixed_value = fix_number_formatting(original_value)
            if fixed_value != original_value:
                fixes[field] = (original_value, fixed_value)
                row_data[field] = fixed_value
    
    return fixes

def fix_sql_table():
    """Main function to fix errors in the user_stats table"""
    print("🔧 Starting SQL table error fixing process...")
    
    # Create engine
    engine = create_engine(DATABASE_URL, echo=False, future=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        with engine.connect() as conn:
            # Get all rows from user_stats table
            result = conn.execute(text("SELECT * FROM user_stats"))
            rows = result.fetchall()
            
            if not rows:
                print("ℹ️ No rows found in user_stats table")
                return
            
            print(f"📊 Found {len(rows)} rows to process")
            
            total_fixes = 0
            rows_with_fixes = 0
            
            for row in rows:
                row_dict = dict(row._mapping)
                row_id = row_dict['id']
                
                # Validate and fix the row
                fixes = validate_and_fix_row(row_dict)
                
                if fixes:
                    rows_with_fixes += 1
                    print(f"\n🔧 Row {row_id} ({row_dict['discordname']}):")
                    
                    for field, (old_value, new_value) in fixes.items():
                        print(f"  {field}: '{old_value}' → '{new_value}'")
                        total_fixes += 1
                    
                    # Update the row in the database
                    update_query = text("""
                        UPDATE user_stats SET
                            game_started = :game_started,
                            coins_earned = :coins_earned,
                            cash_earned = :cash_earned,
                            stones_earned = :stones_earned,
                            damage_dealt = :damage_dealt,
                            enemies_destroyed = :enemies_destroyed,
                            waves_completed = :waves_completed,
                            upgrades_bought = :upgrades_bought,
                            workshop_upgrades = :workshop_upgrades,
                            workshop_coins_spent = :workshop_coins_spent,
                            research_completed = :research_completed,
                            lab_coins_spent = :lab_coins_spent,
                            free_upgrades = :free_upgrades,
                            interest_earned = :interest_earned,
                            orb_kills = :orb_kills,
                            death_ray_kills = :death_ray_kills,
                            thorn_damage = :thorn_damage,
                            waves_skipped = :waves_skipped
                        WHERE id = :id
                    """)
                    
                    conn.execute(update_query, row_dict)
            
            # Commit all changes
            conn.commit()
            
            print(f"\n✅ Error fixing completed!")
            print(f"📈 Summary:")
            print(f"  - Total rows processed: {len(rows)}")
            print(f"  - Rows with fixes: {rows_with_fixes}")
            print(f"  - Total fixes applied: {total_fixes}")
            
            if total_fixes == 0:
                print("  - No errors found! 🎉")
            
    except Exception as e:
        print(f"❌ Error during table fixing: {e}")
        raise
    finally:
        engine.dispose()

def preview_fixes():
    """Preview what fixes would be applied without making changes"""
    print("🔍 Previewing potential fixes (no changes will be made)...")
    
    # Create engine
    engine = create_engine(DATABASE_URL, echo=False, future=True)
    
    try:
        with engine.connect() as conn:
            # Get all rows from user_stats table
            result = conn.execute(text("SELECT * FROM user_stats"))
            rows = result.fetchall()
            
            if not rows:
                print("ℹ️ No rows found in user_stats table")
                return
            
            print(f"📊 Found {len(rows)} rows to analyze")
            
            total_fixes = 0
            rows_with_fixes = 0
            
            for row in rows:
                row_dict = dict(row._mapping)
                row_id = row_dict['id']
                
                # Validate and fix the row (without updating)
                fixes = validate_and_fix_row(row_dict)
                
                if fixes:
                    rows_with_fixes += 1
                    print(f"\n🔧 Row {row_id} ({row_dict['discordname']}):")
                    
                    for field, (old_value, new_value) in fixes.items():
                        print(f"  {field}: '{old_value}' → '{new_value}'")
                        total_fixes += 1
            
            print(f"\n📈 Preview Summary:")
            print(f"  - Total rows analyzed: {len(rows)}")
            print(f"  - Rows that would be fixed: {rows_with_fixes}")
            print(f"  - Total fixes that would be applied: {total_fixes}")
            
            if total_fixes == 0:
                print("  - No errors found! 🎉")
            else:
                print(f"\n💡 Run fix_sql_table() to apply these fixes")
            
    except Exception as e:
        print(f"❌ Error during preview: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        preview_fixes()
    else:
        # Ask for confirmation before making changes
        print("⚠️ This script will modify data in the user_stats table.")
        response = input("Do you want to proceed? (y/N): ")
        
        if response.lower() in ['y', 'yes']:
            fix_sql_table()
        else:
            print("❌ Operation cancelled.")
            print("💡 Use --preview flag to see what would be changed without making modifications.") 