#!/usr/bin/env python3
"""
Encrypted Token Updater
Safely update Infisical credentials in the encrypted token file
"""

import os
import sys
import json
import base64
import getpass
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class TokenUpdater:
    def __init__(self):
        self.project_root = Path("/Users/wgm0/Documents/Y")
        self.encrypted_token_file = self.project_root / "scripts" / "enc" / "encrypted_token.json"
        
    def decrypt_current_token(self, password):
        """Decrypt the current token file"""
        try:
            if not self.encrypted_token_file.exists():
                print(f"❌ Encrypted token file not found: {self.encrypted_token_file}")
                return None
            
            with open(self.encrypted_token_file, 'r') as f:
                encrypted_data = json.load(f)
            
            # Derive key from password
            salt = base64.b64decode(encrypted_data['salt'])
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Decrypt the token
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(base64.b64decode(encrypted_data['encrypted_token']))
            token_data = json.loads(decrypted_data.decode())
            
            print("✅ Current token decrypted successfully")
            return token_data
            
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
        """Main update process"""
        print("🔄 Encrypted Token Updater")
        print("=" * 30)
        
        # Get current password
        current_password = getpass.getpass("🔑 Enter current decryption password: ")
        
        # Decrypt current token
        current_token = self.decrypt_current_token(current_password)
        if not current_token:
            return False
        
        # Show current credentials
        self.show_current_credentials(current_token)
        
        # Ask what to update
        print("What would you like to update?")
        print("1. Update credentials (keep same password)")
        print("2. Update credentials and change password")
        print("3. Change password only")
        print("4. Cancel")
        
        choice = input("Choose option (1-4): ").strip()
        
        if choice == "4":
            print("❌ Update cancelled")
            return False
        
        new_token_data = current_token.copy()
        new_password = current_password
        
        # Update credentials if requested
        if choice in ["1", "2"]:
            new_credentials = self.get_new_credentials()
            if not new_credentials:
                return False
            new_token_data.update(new_credentials)
            print("✅ Credentials updated")
        
        # Update password if requested
        if choice in ["2", "3"]:
            new_password = getpass.getpass("🔐 Enter new decryption password: ")
            confirm_password = getpass.getpass("🔐 Confirm new password: ")
            
            if new_password != confirm_password:
                print("❌ Passwords do not match")
                return False
            
            print("✅ Password updated")
        
        # Encrypt with new data/password
        encrypted_data = self.encrypt_new_token(new_token_data, new_password)
        if not encrypted_data:
            return False
        
        # Save the updated token
        if not self.save_encrypted_token(encrypted_data):
            return False
        
        print("\n🎉 Token update completed successfully!")
        print("💡 You can now use the updated credentials with:")
        print("   scripts/infisical/setup-infisical.sh sync")
        
        return True

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Encrypted Token Updater")
        print("Usage:")
        print("  python3 update-token.py              # Interactive update")
        print("  python3 update-token.py --help       # Show this help")
        return
    
    updater = TokenUpdater()
    success = updater.update_token()
    
    if success:
        print("\n✅ Update completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Update failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 