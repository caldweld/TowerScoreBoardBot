import google.generativeai as genai
import os
from dotenv import load_dotenv

def test_gemini_api():
    """Test if Gemini API is working correctly"""
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment variables")
        print("Please add GOOGLE_API_KEY=your_key_here to your .env file")
        return False
    
    print(f"🔑 API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        print("✅ Gemini configured successfully")
        
        # Test with a simple text prompt (no image needed for basic test)
        model = genai.GenerativeModel('gemini-pro')
        
        response = model.generate_content("Say 'Hello from Gemini!' if you can see this message.")
        
        if response and response.text:
            print("✅ Gemini API is working!")
            print(f"Response: {response.text}")
            return True
        else:
            print("❌ No response from Gemini")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Gemini API: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Gemini API...")
    success = test_gemini_api()
    
    if success:
        print("\n🎉 Gemini API is ready to use!")
        print("You can now integrate it into your bot for better image processing.")
    else:
        print("\n❌ Gemini API test failed. Please check your API key and try again.") 