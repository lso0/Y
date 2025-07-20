#!/usr/bin/env python3
"""
Secure Token Manager with YubiKey Integration
Encrypts/decrypts Infisical tokens using YubiKey + passcode
"""

import os
import sys
import json
import base64
import getpass
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import subprocess

class SecureTokenManager:
    def __init__(self, config_dir=None):
        self.config_dir = Path(config_dir or Path.home() / ".fastmail_automation")
        self.config_dir.mkdir(exist_ok=True)
        self.token_file = self.config_dir / "encrypted_token.json"
        
    def get_yubikey_challenge(self, challenge="fastmail"):
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

    def encrypt_token(self, token, passcode=None):
        """Encrypt Infisical token using YubiKey + passcode"""
        print("🔐 Encrypting token with YubiKey...")
        print("👆 Please touch your YubiKey when it blinks...")
        
        # Get YubiKey response
        yubikey_response = self.get_yubikey_challenge()
        if not yubikey_response:
            return False
            
        # Get passcode
        if not passcode:
            passcode = getpass.getpass("🔒 Enter your passcode: ")
        
        # Generate salt and IV
        salt = os.urandom(16)
        iv = os.urandom(16)
        
        # Derive key
        key = self.derive_key(yubikey_response, passcode, salt)
        
        # Encrypt token
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Pad token to AES block size
        token_bytes = token.encode()
        padding_length = 16 - (len(token_bytes) % 16)
        padded_token = token_bytes + bytes([padding_length] * padding_length)
        
        encrypted_token = encryptor.update(padded_token) + encryptor.finalize()
        
        # Save encrypted data
        encrypted_data = {
            "encrypted_token": base64.b64encode(encrypted_token).decode(),
            "salt": base64.b64encode(salt).decode(),
            "iv": base64.b64encode(iv).decode(),
            "created_at": str(Path().resolve()),
            "hint": "YubiKey + passcode required"
        }
        
        with open(self.token_file, 'w') as f:
            json.dump(encrypted_data, f, indent=2)
        
        print(f"✅ Token encrypted and saved to: {self.token_file}")
        print("🔐 Token is now secure - YubiKey + passcode required to decrypt")
        return True

    def decrypt_token(self, passcode=None):
        """Decrypt Infisical token using YubiKey + passcode"""
        if not self.token_file.exists():
            print(f"❌ No encrypted token found at: {self.token_file}")
            print("💡 Run with --encrypt first to encrypt your token")
            return None
        
        print("🔓 Decrypting token with YubiKey...")
        print("👆 Please touch your YubiKey when it blinks...")
        
        # Get YubiKey response
        yubikey_response = self.get_yubikey_challenge()
        if not yubikey_response:
            return None
            
        # Get passcode
        if not passcode:
            passcode = getpass.getpass("🔒 Enter your passcode: ")
        
        # Load encrypted data
        try:
            with open(self.token_file, 'r') as f:
                encrypted_data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load encrypted token: {e}")
            return None
        
        # Decode components
        try:
            encrypted_token = base64.b64decode(encrypted_data["encrypted_token"])
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
            
            print("✅ Token decrypted successfully!")
            return token
        except Exception as e:
            print(f"❌ Decryption failed - wrong YubiKey or passcode: {e}")
            return None

    def run_infisical_command(self, command_args, passcode=None):
        """Decrypt token and run infisical command"""
        token = self.decrypt_token(passcode)
        if not token:
            return False
        
        # Build infisical command with decrypted token
        infisical_cmd = [
            '/home/wgus1/.npm-global/bin/infisical', 'run',
            '--projectId=13bce4c5-1ffc-478b-b1ce-76726074f358',
            '--env=dev',
            '--domain=http://100.74.180.50',
            f'--token={token}',
            '--'
        ] + command_args
        
        print(f"🚀 Running secure infisical command...")
        
        # Run command without exposing token
        try:
            result = subprocess.run(infisical_cmd, check=False)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Command failed: {e}")
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Secure Token Manager with YubiKey")
    parser.add_argument('--encrypt', metavar='TOKEN', help='Encrypt an Infisical token')
    parser.add_argument('--decrypt', action='store_true', help='Decrypt and display token')
    parser.add_argument('--run', nargs='+', help='Decrypt token and run command')
    parser.add_argument('--passcode', help='Passcode (will prompt if not provided)')
    
    args = parser.parse_args()
    
    manager = SecureTokenManager()
    
    if args.encrypt:
        manager.encrypt_token(args.encrypt, args.passcode)
    elif args.decrypt:
        token = manager.decrypt_token(args.passcode)
        if token:
            print(f"🔓 Decrypted token: {token[:50]}...")
    elif args.run:
        success = manager.run_infisical_command(args.run, args.passcode)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 