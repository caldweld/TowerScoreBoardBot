#!/usr/bin/env python3
"""
Test script for SQL integration with Gemini data
"""

from gemini_processor import process_image
from gemini_sql_parser import process_gemini_result

def test_full_integration():
    """Test the complete flow: Gemini -> SQL"""
    print("🧪 Testing Full Integration: Gemini -> SQL")
    print("=" * 60)
    
    # Get image URL from user
    image_url = input("Enter Discord image URL to test: ").strip()
    
    if not image_url:
        print("❌ No image URL provided")
        return
    
    # Test user info
    discord_id = "123456789"
    discord_name = "TestUser"
    
    print(f"\n🔗 Processing image: {image_url}")
    print(f"👤 User: {discord_name} ({discord_id})")
    print("-" * 60)
    
    try:
        # Step 1: Process image with Gemini
        print("📊 Step 1: Processing image with Gemini...")
        gemini_result = process_image(image_url)
        
        if not gemini_result["success"]:
            print(f"❌ Gemini processing failed: {gemini_result.get('error', 'Unknown error')}")
            return
        
        print(f"✅ Gemini processing successful!")
        print(f"📋 Image type: {gemini_result['image_type']}")
        print(f"🎯 Confidence: {gemini_result['confidence']}")
        
        # Step 2: Parse and save to SQL
        print("\n💾 Step 2: Saving to database...")
        sql_result = process_gemini_result(gemini_result, discord_id, discord_name)
        
        print(f"✅ SQL Result: {sql_result}")
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 INTEGRATION TEST COMPLETE")
        print("=" * 60)
        
        if sql_result["success"]:
            print("✅ SUCCESS: Data saved to database!")
            print(f"📝 Message: {sql_result['message']}")
            
            if gemini_result["image_type"] == "stats":
                print(f"📊 Stats ID: {sql_result.get('stats_id', 'N/A')}")
            elif gemini_result["image_type"] == "tier":
                print(f"🏆 Tiers updated: {sql_result.get('tier_data', {}).get('tiers_updated', 'N/A')}")
        else:
            print("❌ FAILED: Database save failed!")
            print(f"🚨 Error: {sql_result['message']}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_integration() 