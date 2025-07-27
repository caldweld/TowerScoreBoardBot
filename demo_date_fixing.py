#!/usr/bin/env python3
"""
Demonstration script showing the updated date format fixing
"""

import re
from datetime import datetime

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

def demo_date_fixing():
    """Demonstrate the date format fixing functionality"""
    
    # Test cases from your SQL table
    test_dates = [
        "22052025",  # DDMMYYYY format
        "23012025",  # DDMMYYYY format  
        "29022024",  # DDMMYYYY format
        "22-05-2025",  # Already in dd-mm-yyyy format
        "2025-05-22",  # yyyy-mm-dd format
        "22/05/2025",  # dd/mm/yyyy format
        "20250522",    # YYYYMMDD format
        "invalid_date", # Invalid format
        "",            # Empty string
        None           # None value
    ]
    
    print("🔍 Date Format Fixing Demonstration")
    print("=" * 50)
    print("Converting dates to dd-mm-yyyy format...")
    print()
    
    for date_input in test_dates:
        fixed_date = fix_date_format(date_input)
        status = "✅" if fixed_date != date_input else "ℹ️"
        print(f"{status} '{date_input}' → '{fixed_date}'")
    
    print()
    print("📋 Summary:")
    print("- DDMMYYYY format (like 22052025) → dd-mm-yyyy (22-05-2025)")
    print("- yyyy-mm-dd format → dd-mm-yyyy")
    print("- Already correct formats remain unchanged")
    print("- Invalid formats return original value")
    print()
    print("🚀 This will be applied to:")
    print("  1. Existing data via fix_sql_errors.py")
    print("  2. New data via gemini_sql_parser.py (preventive)")

if __name__ == "__main__":
    demo_date_fixing() 