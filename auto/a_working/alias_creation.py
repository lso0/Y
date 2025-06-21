import requests
import json

# JMAP API endpoint (replace with your user ID)
JMAP_URL = "https://api.fastmail.com/jmap/api/?u=2ef64041"

# Authentication details (you need to extract these from your browser session)
BEARER_TOKEN = "fma1-2ef64041-f0fe715e03eb23ecfb1f99685bb6e6e1-0-b81dcc290c0e4f36d9ee9da2015efa77"
ACCOUNT_ID = "c75164099"

# Session cookies (extract from browser)
COOKIES = {
    "__Host-s_2ef64041": "3.phl.phl.299605f91e4057bcde0deac2efb90c66.1748888660.602dee9772334933490d5f262469a2e5f91e32837fb6893d30d63e27e61ae03",
    "__Secure-f_2ef64041": "2.1748888660.0.d4846db7fbd19242e1a41bd7e3d2238bff5355ac907dc8b21a48c95f52063d5c",
    "seenlogin": "1"
}

def create_alias(alias_email, target_email, description=""):
    """Create an alias using Fastmail's JMAP API"""
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Origin": "https://app.fastmail.com",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }
    
    # JMAP request payload
    payload = {
        "using": [
            "urn:ietf:params:jmap:principals",
            "https://www.fastmail.com/dev/contacts",
            "https://www.fastmail.com/dev/backup",
            "https://www.fastmail.com/dev/auth",
            "https://www.fastmail.com/dev/calendars",
            "https://www.fastmail.com/dev/rules",
            "urn:ietf:params:jmap:mail",
            "urn:ietf:params:jmap:submission",
            "https://www.fastmail.com/dev/customer",
            "https://www.fastmail.com/dev/mail",
            "urn:ietf:params:jmap:vacationresponse",
            "urn:ietf:params:jmap:core",
            "https://www.fastmail.com/dev/files",
            "https://www.fastmail.com/dev/blob",
            "https://www.fastmail.com/dev/user",
            "urn:ietf:params:jmap:contacts",
            "https://www.fastmail.com/dev/performance",
            "https://www.fastmail.com/dev/compress",
            "https://www.fastmail.com/dev/notes",
            "urn:ietf:params:jmap:calendars"
        ],
        "methodCalls": [
            [
                "Alias/set",
                {
                    "accountId": ACCOUNT_ID,
                    "create": {
                        "k45": {
                            "email": alias_email,
                            "targetEmails": [target_email],
                            "targetGroupRef": None,
                            "restrictSendingTo": "everybody",
                            "description": description
                        }
                    },
                    "onSuccessUpdateIdentities": True
                },
                "0"
            ]
        ],
        "lastActivity": 0,
        "clientVersion": "b457b8b325-5000d76b8ac6ae6b"
    }
    
    try:
        response = requests.post(JMAP_URL, json=payload, headers=headers, cookies=COOKIES)
        if response.status_code == 200:
            result = response.json()
            print("Alias created successfully!")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"Failed to create alias. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error creating alias: {e}")
        return False

def get_session_info():
    """Helper function to show what session info you need to extract"""
    print("To use this script, you need to extract the following from your browser:")
    print("1. Bearer token from Authorization header")
    print("2. Account ID from the requests")
    print("3. Session cookies (__Host-s_*, __Secure-f_*)")
    print("\nYou can find these in your browser's Developer Tools > Network tab")
    print("Look for requests to api.fastmail.com/jmap/api/")

if __name__ == "__main__":
    # Create the nya01 alias as specified
    alias_email = "nya01@fastmail.com"
    target_email = "wg0@fastmail.com"
    description = ""
    
    print(f"Creating alias: {alias_email} -> {target_email}")
    success = create_alias(alias_email, target_email, description)
    
    if not success:
        print("\n" + "="*50)
        get_session_info() 