#!/usr/bin/env python3
"""
YubiKey Token Manager with Multi-Service Support
Encrypts/decrypts Infisical and other service tokens using YubiKey + passphrase
Supports the new encrypted_tokens.json multi-service structure
"""

import os
import sys
import json
import base64
import getpass
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import subprocess

class YubiKeyTokenManager:
    def __init__(self):
        # Dynamic path detection: script is in scripts/enc/, so project root is 2 levels up
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
        
    def get_yubikey_challenge(self, challenge="infisical"):
        """Get response from YubiKey using challenge-response"""
        try:
            # Convert challenge to hex for YubiKey
            import binascii
            hex_challenge = binascii.hexlify(challenge.encode()).decode()
            
            # Use ykman to get challenge-response (requires YubiKey with HMAC-SHA1)
            result = subprocess.run([
                'ykman', 'otp', 'calculate', '2', hex_challenge
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"❌ YubiKey error: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            print("❌ YubiKey timeout - please touch your YubiKey")
            return None
        except FileNotFoundError:
            print("❌ ykman not found. Install with: pip install yubikey-manager")
            return None
        except Exception as e:
            print(f"❌ YubiKey error: {e}")
            return None

    def derive_key(self, yubikey_response, passcode, salt):
        """Derive encryption key from YubiKey response + passcode"""
        # Combine YubiKey response with user passcode
        combined_secret = f"{yubikey_response}:{passcode}".encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(combined_secret)

    def encrypt_service_token(self, service_name: str, token_data: str, passcode: Optional[str] = None) -> bool:
        """Encrypt a service token using YubiKey + passcode"""
        print(f"🔐 Encrypting {service_name} token with YubiKey...")
        print("👆 Please touch your YubiKey when it blinks...")
        
        # Get YubiKey response
        yubikey_response = self.get_yubikey_challenge(service_name)
        if not yubikey_response:
            return False
            
        # Get passcode with confirmation
        if not passcode:
            while True:
                passcode1 = getpass.getpass("🔒 Enter your passcode: ")
                if not passcode1:
                    print("❌ No passcode provided")
                    return False
                    
                passcode2 = getpass.getpass("🔒 Confirm your passcode: ")
                if passcode1 == passcode2:
                    passcode = passcode1
                    break
                else:
                    print("❌ Passphrases don't match. Please try again.")
        
        # Generate salt and IV
        salt = os.urandom(16)
        iv = os.urandom(16)
        
        # Derive key
        key = self.derive_key(yubikey_response, passcode, salt)
        
        # Encrypt token
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Pad token to AES block size
        token_bytes = token_data.encode()
        padding_length = 16 - (len(token_bytes) % 16)
        padded_token = token_bytes + bytes([padding_length] * padding_length)
        
        encrypted_token = encryptor.update(padded_token) + encryptor.finalize()
        
        # Create encrypted structure for this service
        service_encrypted = {
            "encrypted_data": base64.b64encode(encrypted_token).decode(),
            "salt": base64.b64encode(salt).decode(),
            "iv": base64.b64encode(iv).decode(),
            "created_at": datetime.now().isoformat(),
            "description": f"{service_name.title()} credentials encrypted with YubiKey",
            "encryption_method": "YubiKey_AES256_CBC"
        }
        
        # Load existing tokens and update/add this service
        encrypted_tokens = self.load_encrypted_tokens()
        encrypted_tokens[service_name] = service_encrypted
        
        # Save the updated tokens file
        if self.save_encrypted_tokens(encrypted_tokens):
            print(f"✅ {service_name.title()} token encrypted and saved to: {self.encrypted_tokens_file}")
            print("🔐 Token is now secure - YubiKey + passcode required to decrypt")
            return True
        else:
            print("❌ Failed to save encrypted tokens")
            return False

    def decrypt_service_token(self, service_name: str, passcode: Optional[str] = None, quiet: bool = False) -> Optional[str]:
        """Decrypt a service token using YubiKey + passcode"""
        encrypted_tokens = self.load_encrypted_tokens()
        
        if not encrypted_tokens or service_name not in encrypted_tokens:
            if not quiet:
                print(f"❌ No {service_name} token found in encrypted tokens file")
                available_services = list(encrypted_tokens.keys())
                if available_services:
                    print(f"Available services: {available_services}")
            return None
        
        encrypted_data = encrypted_tokens[service_name]
        
        if not quiet:
            print(f"🔓 Decrypting {service_name} token with YubiKey...")
            print("👆 Please touch your YubiKey when it blinks...")
        
        # Get YubiKey response
        yubikey_response = self.get_yubikey_challenge(service_name)
        if not yubikey_response:
            return None
            
        # Get passcode
        if not passcode:
            passcode = getpass.getpass("🔒 Enter your passcode: ")
        
        # Decode components
        try:
            encrypted_token = base64.b64decode(encrypted_data["encrypted_data"])
            salt = base64.b64decode(encrypted_data["salt"])
            iv = base64.b64decode(encrypted_data["iv"])
        except Exception as e:
            print(f"❌ Invalid encrypted token format: {e}")
            return None
        
        # Derive key
        try:
            key = self.derive_key(yubikey_response, passcode, salt)
        except Exception as e:
            print(f"❌ Failed to derive key: {e}")
            return None
        
        # Decrypt token
        try:
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_token = decryptor.update(encrypted_token) + decryptor.finalize()
            
            # Remove padding
            padding_length = padded_token[-1]
            token = padded_token[:-padding_length].decode()
            
            if not quiet:
                print(f"✅ {service_name.title()} token decrypted successfully!")
            return token
        except Exception as e:
            if not quiet:
                print(f"❌ Decryption failed - wrong YubiKey or passcode: {e}")
            return None

    def list_services(self):
        """List all available encrypted services"""
        encrypted_tokens = self.load_encrypted_tokens()
        
        if not encrypted_tokens:
            print("❌ No encrypted tokens found")
            return
        
        print("🔐 Available encrypted services:")
        for service_name, service_data in encrypted_tokens.items():
            created_at = service_data.get("created_at", "Unknown")
            description = service_data.get("description", "No description")
            encryption_method = service_data.get("encryption_method", "Unknown")
            print(f"  📦 {service_name}")
            print(f"     📅 Created: {created_at}")
            print(f"     📝 Description: {description}")
            print(f"     🔒 Encryption: {encryption_method}")
            print()

    def encrypt_infisical_token(self, token: str, passcode: Optional[str] = None) -> bool:
        """Encrypt Infisical token specifically"""
        return self.encrypt_service_token("infisical", token, passcode)

    def decrypt_infisical_token(self, passcode: Optional[str] = None, quiet: bool = False) -> Optional[str]:
        """Decrypt Infisical token specifically"""
        return self.decrypt_service_token("infisical", passcode, quiet)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="YubiKey Token Manager with Multi-Service Support")
    parser.add_argument('--encrypt', nargs='?', const='', help='Encrypt a token for the specified service (will prompt if no token provided)')
    parser.add_argument('--service', default='infisical', help='Service name (default: infisical)')
    parser.add_argument('--decrypt', action='store_true', help='Decrypt and display token for service')
    parser.add_argument('--token-only', action='store_true', help='Decrypt and output only the token (for scripting)')
    parser.add_argument('--list', action='store_true', help='List all encrypted services')
    parser.add_argument('--passcode', help='Passcode (will prompt if not provided)')
    
    args = parser.parse_args()
    
    manager = YubiKeyTokenManager()
    
    if args.list:
        manager.list_services()
    elif args.encrypt is not None:
        # Handle interactive token input
        if args.encrypt == '':
            print(f"🔐 Encrypting {args.service} token with YubiKey + passphrase")
            print("=" * 60)
            token = getpass.getpass(f"🔑 Enter your {args.service} token: ")
            if not token:
                print("❌ No token provided")
                sys.exit(1)
        else:
            token = args.encrypt
            
        success = manager.encrypt_service_token(args.service, token, args.passcode)
        sys.exit(0 if success else 1)
    elif args.decrypt:
        token = manager.decrypt_service_token(args.service, args.passcode)
        if token:
            print(f"🔓 Decrypted {args.service} token: {token[:50]}...")
        else:
            sys.exit(1)
    elif args.token_only:
        token = manager.decrypt_service_token(args.service, args.passcode, quiet=True)
        if token:
            print(token)
        else:
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 