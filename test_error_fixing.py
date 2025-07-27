#!/usr/bin/env python3
"""
Test script to demonstrate SQL error fixing with the provided table data
"""

import re
from datetime import datetime

# Define suffixes for number formatting (same as in fix_sql_errors.py)
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
    
    return date_str

def fix_monetary_value(value):
    """Fix monetary values to have consistent $ prefix and spacing"""
    if not value or not isinstance(value, str):
        return value
    
    # Remove existing $ and clean up
    cleaned = value.replace('$', '').strip()
    
    # Check if it's a monetary field
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

def test_with_provided_data():
    """Test the error fixing functions with the provided SQL table data"""
    
    # Sample data from the provided SQL table
    test_data = [
        {
            'id': 15,
            'discordid': '224043534884274176',
            'discordname': '_teedo',
            'game_started': '22052025',
            'coins_earned': '8.42 B',
            'cash_earned': '$107.11 B',
            'stones_earned': '855',
            'damage_dealt': '2.26 O',
            'enemies_destroyed': '40.44 M',
            'waves_completed': '307.18 K',
            'upgrades_bought': '245.57 K',
            'workshop_upgrades': '4.10 K',
            'workshop_coins_spent': '4.09 B',
            'research_completed': '401',
            'lab_coins_spent': '3.76 B',
            'free_upgrades': '502.40 K',
            'interest_earned': '$15.18 M',
            'orb_kills': '29.19 M',
            'death_ray_kills': '0',
            'thorn_damage': '525.69 S',
            'waves_skipped': '18334'
        },
        {
            'id': 16,
            'discordid': '280638532928798723',
            'discordname': 'caldweld',
            'game_started': '23012025',
            'coins_earned': '1.54 T',
            'cash_earned': '$1.01 T',
            'stones_earned': '10178',
            'damage_dealt': '3.11D',
            'enemies_destroyed': '58.44 M',
            'waves_completed': '423.02 K',
            'upgrades_bought': '384.33 K',
            'workshop_upgrades': '24.19 K',
            'workshop_coins_spent': '1.16 T',
            'research_completed': '695',
            'lab_coins_spent': '127.12 B',
            'free_upgrades': '857.88 K',
            'interest_earned': '$42.62 M',
            'orb_kills': '31.07 M',
            'death_ray_kills': '467.27 K',
            'thorn_damage': '1.04D',
            'waves_skipped': '61696'
        },
        {
            'id': 17,
            'discordid': '98583066418626560',
            'discordname': 'tydal',
            'game_started': '29022024',
            'coins_earned': '157.68 T',
            'cash_earned': '$46.06 T',
            'stones_earned': '9881',
            'damage_dealt': '1.63D',
            'enemies_destroyed': '348.70 M',
            'waves_completed': '2.50 M',
            'upgrades_bought': '3.92 M',
            'workshop_upgrades': '22.68 K',
            'workshop_coins_spent': '12.02 T',
            'research_completed': '1.60 K',
            'lab_coins_spent': '113.22 T',
            'free_upgrades': '4.69 M',
            'interest_earned': '$39.88 B',
            'orb_kills': '147.50 M',
            'death_ray_kills': '58.13 M',
            'thorn_damage': '216.73N',
            'waves_skipped': '730434'
        }
    ]
    
    print("🔍 Testing error fixing functions with provided SQL table data...")
    print("=" * 80)
    
    total_fixes = 0
    
    for row in test_data:
        print(f"\n📊 Row {row['id']} ({row['discordname']}):")
        fixes = []
        
        # Test date fixing
        original_date = row['game_started']
        fixed_date = fix_date_format(original_date)
        if fixed_date != original_date:
            fixes.append(f"game_started: '{original_date}' → '{fixed_date}'")
        
        # Test monetary value fixing
        monetary_fields = ['cash_earned', 'interest_earned']
        for field in monetary_fields:
            original_value = row[field]
            fixed_value = fix_monetary_value(original_value)
            if fixed_value != original_value:
                fixes.append(f"{field}: '{original_value}' → '{fixed_value}'")
        
        # Test number formatting fixing
        numeric_fields = [
            'coins_earned', 'stones_earned', 'damage_dealt', 'enemies_destroyed',
            'waves_completed', 'upgrades_bought', 'workshop_upgrades', 'workshop_coins_spent',
            'research_completed', 'lab_coins_spent', 'free_upgrades', 'orb_kills',
            'death_ray_kills', 'thorn_damage', 'waves_skipped'
        ]
        
        for field in numeric_fields:
            original_value = row[field]
            fixed_value = fix_number_formatting(original_value)
            if fixed_value != original_value:
                fixes.append(f"{field}: '{original_value}' → '{fixed_value}'")
        
        if fixes:
            for fix in fixes:
                print(f"  🔧 {fix}")
                total_fixes += 1
        else:
            print("  ✅ No fixes needed")
    
    print("\n" + "=" * 80)
    print(f"📈 Summary: {total_fixes} fixes would be applied")
    
    if total_fixes > 0:
        print("\n💡 Common errors found:")
        print("  - Date format: DDMMYYYY → YYYY-MM-DD")
        print("  - Missing spaces before number suffixes")
        print("  - Inconsistent monetary value formatting")
        print("\n🚀 Run the fix_sql_errors.py script to apply these fixes to your database!")

if __name__ == "__main__":
    test_with_provided_data() 