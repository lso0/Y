import requests
import json
import os
from typing import Optional, Dict, Any

class FastmailAliasCreator:
    """
    Fastmail alias creator using App Password authentication.
    Much more reliable than browser session extraction.
    """
    
    def __init__(self, app_password: str):
        self.app_password = app_password
        self.account_id = None
        self.user_id = None
        self.base_url = "https://api.fastmail.com/jmap/api/"
        
    def authenticate(self) -> bool:
        """
        Authenticate and get account ID and user ID.
        Returns True if successful, False otherwise.
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.app_password}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "using": ["urn:ietf:params:jmap:core"],
                "methodCalls": [["getSession", {}, "0"]]
            }
            
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Extract account ID
            accounts = data["methodResponses"][0][1]["accounts"]
            self.account_id = list(accounts.keys())[0]
            
            # For user ID, we need to extract from the URL or use the account ID
            # In most cases, the user ID is part of the account structure
            session_data = data["methodResponses"][0][1]
            if "username" in session_data:
                self.user_id = session_data["username"]
            else:
                # Fallback: try to extract from response or use account ID
                self.user_id = self.account_id
            
            # Update base URL with user ID
            self.base_url = f"https://api.fastmail.com/jmap/api/?u={self.user_id}"
            
            print(f"✅ Authentication successful!")
            print(f"Account ID: {self.account_id}")
            print(f"User ID: {self.user_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def create_alias(self, alias_email: str, target_email: str, description: str = "") -> Optional[Dict[Any, Any]]:
        """
        Create a new alias using JMAP API.
        
        Args:
            alias_email: The alias email address to create
            target_email: The target email address to forward to
            description: Optional description for the alias
            
        Returns:
            Response data if successful, None if failed
        """
        if not self.account_id or not self.user_id:
            print("🔄 Not authenticated, attempting authentication...")
            if not self.authenticate():
                return None
        
        headers = {
            "Authorization": f"Bearer {self.app_password}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "using": [
                "urn:ietf:params:jmap:core",
                "https://www.fastmail.com/dev/aliases"
            ],
            "methodCalls": [
                [
                    "Alias/set",
                    {
                        "accountId": self.account_id,
                        "create": {
                            "alias1": {
                                "email": alias_email,
                                "targetEmails": [target_email],
                                "description": description,
                                "restrictSendingTo": "everybody"
                            }
                        }
                    },
                    "0"
                ]
            ]
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Check if the alias was created successfully
            if "methodResponses" in result and len(result["methodResponses"]) > 0:
                method_response = result["methodResponses"][0]
                if method_response[0] == "Alias/set" and "created" in method_response[1]:
                    print(f"🎉 Alias created successfully!")
                    print(f"   {alias_email} -> {target_email}")
                    if description:
                        print(f"   Description: {description}")
                    return result
                else:
                    print(f"❌ Failed to create alias:")
                    print(f"   Response: {json.dumps(result, indent=2)}")
                    return None
            else:
                print(f"❌ Unexpected response format:")
                print(f"   {json.dumps(result, indent=2)}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating alias: {e}")
            return None
    
    def list_aliases(self) -> Optional[Dict[Any, Any]]:
        """
        List all existing aliases.
        
        Returns:
            Response data if successful, None if failed
        """
        if not self.account_id or not self.user_id:
            if not self.authenticate():
                return None
        
        headers = {
            "Authorization": f"Bearer {self.app_password}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "using": [
                "urn:ietf:params:jmap:core",
                "https://www.fastmail.com/dev/aliases"
            ],
            "methodCalls": [
                [
                    "Alias/get",
                    {
                        "accountId": self.account_id,
                        "ids": None  # Get all aliases
                    },
                    "0"
                ]
            ]
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print("📋 Current aliases:")
            if "methodResponses" in result and len(result["methodResponses"]) > 0:
                aliases = result["methodResponses"][0][1]["list"]
                for alias in aliases:
                    print(f"   {alias['email']} -> {', '.join(alias['targetEmails'])}")
                    if alias.get('description'):
                        print(f"      Description: {alias['description']}")
                print(f"\nTotal aliases: {len(aliases)}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error listing aliases: {e}")
            return None


def get_app_password_from_env() -> Optional[str]:
    """Get app password from environment variable."""
    return os.getenv('FASTMAIL_APP_PASSWORD')


def get_app_password_from_input() -> str:
    """Get app password from user input."""
    print("🔑 Enter your Fastmail App Password:")
    print("   (Go to Settings → Password & Security → App Passwords)")
    print("   (Select 'Mail, Contacts & Calendars' scope)")
    return input("App Password: ").strip()


def main():
    """Main function to demonstrate alias creation."""
    print("🚀 Fastmail Alias Creator (App Password Method)")
    print("=" * 50)
    
    # Try to get app password from environment first
    app_password = get_app_password_from_env()
    if not app_password:
        app_password = get_app_password_from_input()
    
    if not app_password:
        print("❌ No app password provided. Exiting.")
        return
    
    # Initialize the creator
    creator = FastmailAliasCreator(app_password)
    
    # Test authentication
    if not creator.authenticate():
        print("❌ Authentication failed. Please check your app password.")
        return
    
    # List existing aliases
    creator.list_aliases()
    
    # Interactive alias creation
    print("\n" + "=" * 50)
    print("📝 Create New Alias")
    
    while True:
        alias_email = input("\nEnter alias email (or 'quit' to exit): ").strip()
        if alias_email.lower() == 'quit':
            break
            
        target_email = input("Enter target email: ").strip()
        description = input("Enter description (optional): ").strip()
        
        if alias_email and target_email:
            result = creator.create_alias(alias_email, target_email, description)
            if result:
                print("✅ Alias created successfully!")
            else:
                print("❌ Failed to create alias.")
        else:
            print("❌ Please provide both alias and target email.")


if __name__ == "__main__":
    # Example usage for automated testing
    test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
    
    if test_mode:
        # Example automated usage
        app_password = get_app_password_from_env()
        if app_password:
            creator = FastmailAliasCreator(app_password)
            
            # Create the nya01 alias as specified in the original script
            result = creator.create_alias(
                alias_email="nya01@fastmail.com",
                target_email="wg0@fastmail.com",
                description="Test alias created via app password"
            )
            
            if result:
                print("🎉 Test alias created successfully!")
            else:
                print("❌ Failed to create test alias.")
        else:
            print("❌ TEST_MODE enabled but no FASTMAIL_APP_PASSWORD environment variable found.")
    else:
        main() 