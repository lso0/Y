#!/usr/bin/env python3
"""
Infisical Token Updater - Streamlined Version
Securely updates encrypted Infisical authentication tokens
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import getpass
from datetime import datetime

class InfisicalTokenUpdater:
    def __init__(self):
        # Simple approach: script is in scripts/infisical/, so project root is 2 levels up
        script_path = Path(__file__).resolve()
        self.project_root = script_path.parent.parent.parent
        self.encrypted_tokens_file = self.project_root / "scripts" / "enc" / "encrypted_tokens.json"
    
    def load_encrypted_tokens(self) -> Dict[str, Any]:
        """Load existing encrypted tokens file"""
        try:
            if not self.encrypted_tokens_file.exists():
                return {}
            
            with open(self.encrypted_tokens_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading encrypted tokens file: {e}")
            return {}
    
    def save_encrypted_tokens(self, tokens_data: Dict[str, Any]) -> bool:
        """Save the encrypted tokens file"""
        try:
            self.encrypted_tokens_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.encrypted_tokens_file, 'w') as f:
                json.dump(tokens_data, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error saving encrypted tokens file: {e}")
            return False
    
    def decrypt_current_token(self, password):
        """Decrypt current Infisical token if it exists"""
        try:
            encrypted_tokens = self.load_encrypted_tokens()
            
            if not encrypted_tokens or "infisical" not in encrypted_tokens:
                print("ℹ️ No existing Infisical token found")
                return None
            
            encrypted_data = encrypted_tokens["infisical"]
            
            # Derive key from password and salt
            salt = base64.b64decode(encrypted_data['salt'].encode())
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Decrypt the token
            f = Fernet(key)
            decrypted_data = f.decrypt(encrypted_data['encrypted_data'].encode())
            token_info = json.loads(decrypted_data.decode())
            
            print("✅ Current token decrypted successfully")
            return token_info
            
        except Exception as e:
            print(f"❌ Failed to decrypt current token: {e}")
            return None
    
    def encrypt_new_token(self, token_data, password):
        """Encrypt new token data"""
        try:
            # Generate new salt
            import os
            salt = os.urandom(16)
            
            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Encrypt the token data
            fernet = Fernet(key)
            token_json = json.dumps(token_data)
            encrypted_token = fernet.encrypt(token_json.encode())
            
            # Create the encrypted file structure
            encrypted_file_data = {
                "encrypted_token": base64.b64encode(encrypted_token).decode(),
                "salt": base64.b64encode(salt).decode(),
                "iv": base64.b64encode(os.urandom(16)).decode(),  # For compatibility
                "created_at": str(self.project_root),
                "hint": "YubiKey + passcode required"
            }
            
            print("✅ New token encrypted successfully")
            return encrypted_file_data
            
        except Exception as e:
            print(f"❌ Failed to encrypt new token: {e}")
            return None
    
    def save_encrypted_token(self, encrypted_data):
        """Save the encrypted token to file"""
        try:
            # Create backup
            if self.encrypted_token_file.exists():
                backup_file = self.encrypted_token_file.with_suffix('.json.backup')
                import shutil
                shutil.copy2(self.encrypted_token_file, backup_file)
                print(f"📋 Created backup: {backup_file}")
            
            # Save new encrypted token
            with open(self.encrypted_token_file, 'w') as f:
                json.dump(encrypted_data, f, indent=2)
            
            print(f"✅ Encrypted token saved to: {self.encrypted_token_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save encrypted token: {e}")
            return False
    
    def show_current_credentials(self, token_data):
        """Show current credentials (masked)"""
        print("\n📋 Current credentials:")
        if 'client_id' in token_data:
            client_id = token_data['client_id']
            masked_id = client_id[:8] + "***" + client_id[-4:] if len(client_id) > 12 else "***"
            print(f"  Client ID: {masked_id}")
        
        if 'client_secret' in token_data:
            secret = token_data['client_secret']
            masked_secret = secret[:8] + "***" + secret[-4:] if len(secret) > 12 else "***"
            print(f"  Client Secret: {masked_secret}")
        
        print()
    
    def get_new_credentials(self):
        """Get new credentials from user input"""
        print("🔑 Enter new Infisical credentials:")
        
        client_id = input("Client ID: ").strip()
        if not client_id:
            print("❌ Client ID cannot be empty")
            return None
        
        client_secret = getpass.getpass("Client Secret: ").strip()
        if not client_secret:
            print("❌ Client Secret cannot be empty")
            return None
        
        return {
            "client_id": client_id,
            "client_secret": client_secret
        }
    
    def update_token(self):
        """Update Infisical credentials in encrypted file"""
        print("🔐 Infisical Token Updater - Streamlined Version")
        print("=" * 50)
        
        # Get password for encryption
        password = getpass.getpass("🔑 Enter encryption password: ")
        if not password:
            print("❌ No password provided")
            return False
        
        # Try to decrypt existing token
        existing_token = self.decrypt_current_token(password)
        if existing_token:
            print("📋 Current credentials found:")
            print(f"  Client ID: {existing_token.get('client_id', 'N/A')[:8]}...")
            print(f"  Workspace ID: {existing_token.get('workspace_id', 'N/A')}")
            
            update_choice = input("\n❓ Update existing credentials? (y/n): ").lower()
            if update_choice != 'y':
                print("ℹ️ Keeping existing credentials")
                return True
        
        # Get new credentials
        print("\n📝 Enter new Infisical credentials:")
        client_id = input("Client ID: ").strip()
        client_secret = getpass.getpass("Client Secret: ").strip()
        workspace_id = input("Workspace ID: ").strip()
        
        if not all([client_id, client_secret, workspace_id]):
            print("❌ All fields are required")
            return False
        
        # Create token data
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "workspace_id": workspace_id,
            "updated_at": datetime.now().isoformat()
        }
        
        # Encrypt the token
        try:
            # Generate salt and derive key
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Encrypt the data
            f = Fernet(key)
            encrypted_data = f.encrypt(json.dumps(token_data).encode())
            
            # Create the encrypted structure for Infisical
            infisical_encrypted = {
                "encrypted_data": encrypted_data.decode(),
                "salt": base64.b64encode(salt).decode(),
                "created_at": datetime.now().isoformat(),
                "description": "Infisical project credentials"
            }
            
            # Load existing tokens and update/add Infisical section
            encrypted_tokens = self.load_encrypted_tokens()
            encrypted_tokens["infisical"] = infisical_encrypted
            
            # Save the updated tokens file
            if self.save_encrypted_tokens(encrypted_tokens):
                print(f"✅ Infisical credentials encrypted and saved to: {self.encrypted_tokens_file}")
                print("🔒 Your credentials are now securely stored")
                return True
            else:
                print("❌ Failed to save encrypted tokens")
                return False
                
        except Exception as e:
            print(f"❌ Encryption failed: {e}")
            return False

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Encrypted Token Updater")
        print("Usage:")
        print("  python3 update-token.py              # Interactive update")
        print("  python3 update-token.py --help       # Show this help")
        return
    
    updater = InfisicalTokenUpdater()
    success = updater.update_token()
    
    if success:
        print("\n✅ Update completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Update failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 