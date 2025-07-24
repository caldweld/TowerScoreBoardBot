#!/usr/bin/env python3
"""
Test script for Gemini image processing
"""

from gemini_processor import test_image_processing

def main():
    print("🧪 Testing Gemini Image Processing")
    print("=" * 50)
    
    # Test with a sample image URL
    # You can replace this with any Discord image URL for testing
    test_image_url = input("Enter Discord image URL to test: ").strip()
    
    if not test_image_url:
        print("❌ No image URL provided")
        return
    
    print(f"\n🔗 Testing with URL: {test_image_url}")
    print("-" * 50)
    
    try:
        result = test_image_processing(test_image_url)
        
        print("\n" + "=" * 50)
        print("TEST COMPLETE")
        print("=" * 50)
        
        if result["success"]:
            print("✅ Processing successful!")
            print(f"📊 Image type: {result['image_type']}")
            print(f"🎯 Confidence: {result['confidence']}")
            print(f"💭 Reason: {result['reason']}")
            
            if result["data"]:
                print(f"📋 Data extracted: {len(str(result['data']))} characters")
            else:
                print("❌ No data extracted")
        else:
            print("❌ Processing failed!")
            print(f"🚨 Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 