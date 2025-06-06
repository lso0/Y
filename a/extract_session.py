#!/usr/bin/env python3
"""
Helper script to extract Fastmail session information from browser
"""

def extract_session_guide():
    print("=" * 60)
    print("FASTMAIL SESSION EXTRACTION GUIDE")
    print("=" * 60)
    print()
    print("To automate alias creation, you need to extract session data from your browser.")
    print("Follow these steps:")
    print()
    print("1. Open your browser and go to: https://app.fastmail.com")
    print("2. Log in to your Fastmail account")
    print("3. Open Developer Tools (F12 or Right-click → Inspect)")
    print("4. Go to the 'Network' tab")
    print("5. Navigate to Settings → Aliases in Fastmail")
    print("6. Look for a request to 'api.fastmail.com/jmap/api/'")
    print("7. Click on that request and find these values:")
    print()
    print("   REQUEST URL:")
    print("   Copy the 'u=' parameter value (e.g., u=2ef64041)")
    print()
    print("   REQUEST HEADERS:")
    print("   - Authorization: Bearer [long token]")
    print("   - Cookie: [session cookies]")
    print()
    print("8. Update alias_creation.py with these values:")
    print()
    print("   JMAP_URL = 'https://api.fastmail.com/jmap/api/?u=[YOUR_U_VALUE]'")
    print("   BEARER_TOKEN = '[YOUR_BEARER_TOKEN]'")
    print("   COOKIES = {")
    print("       '__Host-s_[USER_ID]': '[VALUE]',")
    print("       '__Secure-f_[USER_ID]': '[VALUE]',")
    print("       'seenlogin': '1'")
    print("   }")
    print()
    print("=" * 60)

def parse_session_data():
    print("\nSession Data Parser")
    print("-" * 20)
    
    print("\nPaste your Authorization header (Bearer token):")
    auth_header = input().strip()
    
    print("\nPaste your Cookie header:")
    cookie_header = input().strip()
    
    print("\nPaste your URL (with u= parameter):")
    url = input().strip()
    
    # Parse the data
    print("\n" + "=" * 50)
    print("GENERATED CONFIG:")
    print("=" * 50)
    
    # Extract user ID from URL
    if "u=" in url:
        user_id = url.split("u=")[1].split("&")[0]
        print(f'JMAP_URL = "https://api.fastmail.com/jmap/api/?u={user_id}"')
    
    # Extract bearer token
    if "Bearer " in auth_header:
        token = auth_header.replace("Bearer ", "").strip()
        print(f'BEARER_TOKEN = "{token}"')
    
    # Parse cookies
    print("COOKIES = {")
    if cookie_header:
        cookies = cookie_header.split(";")
        for cookie in cookies:
            if "=" in cookie:
                name, value = cookie.strip().split("=", 1)
                if name.startswith("__Host-") or name.startswith("__Secure-") or name == "seenlogin":
                    print(f'    "{name}": "{value}",')
    print("}")
    
    print("\nCopy the above values into alias_creation.py!")

if __name__ == "__main__":
    extract_session_guide()
    
    choice = input("\nWould you like to parse session data now? (y/N): ").strip().lower()
    if choice in ['y', 'yes']:
        parse_session_data() 