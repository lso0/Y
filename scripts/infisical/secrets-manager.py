#!/usr/bin/env python3
"""
Infisical Secrets Manager - Streamlined Version
Handles decryption of encrypted tokens and secret management with Infisical
"""

import sys
import os
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

class InfisicalSecretsManager:
    def __init__(self):
        # Simple approach: script is in scripts/infisical/, so project root is 2 levels up
        script_path = Path(__file__).resolve()
        self.project_root = script_path.parent.parent.parent
        self.env_file = self.project_root / ".env"
        self.infisical_config = self.project_root / ".infisical.json"
        self.encrypted_tokens_file = self.project_root / "scripts" / "enc" / "encrypted_tokens.json"
    
    def load_infisical_config(self):
        """Load Infisical workspace configuration (optional)"""
        try:
            if not self.infisical_config.exists():
                print("ℹ️ No .infisical.json config file found (optional)")
                return {"workspaceId": "default"}
                
            with open(self.infisical_config, 'r') as f:
                config = json.load(f)
            print(f"✅ Loaded Infisical config - Workspace: {config.get('workspaceId', 'N/A')}")
            return config
        except Exception as e:
            print(f"⚠️ Could not load Infisical config (continuing anyway): {e}")
            return {"workspaceId": "default"}
    
    def load_encrypted_tokens(self) -> Dict[str, Any]:
        """Load the encrypted tokens file"""
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
    
    def decrypt_token(self, password=None):
        """Decrypt the Infisical token from encrypted file"""
        try:
            print("🔓 Decrypting Infisical token...")
            
            # Load encrypted tokens
            encrypted_tokens = self.load_encrypted_tokens()
            
            if not encrypted_tokens:
                print(f"❌ No encrypted tokens found in {self.encrypted_tokens_file}")
                return None
            
            # Look for Infisical token specifically
            if "infisical" not in encrypted_tokens:
                print("❌ No Infisical token found in encrypted tokens file")
                available_keys = list(encrypted_tokens.keys())
                print(f"Available services: {available_keys}")
                return None
                
            encrypted_data = encrypted_tokens["infisical"]
            
            # Check if this is a YubiKey-encrypted token
            if encrypted_data.get("encryption_method") == "YubiKey_AES256_CBC":
                print("🔐 Detected YubiKey-encrypted token")
                return self._decrypt_yubikey_token(encrypted_data, password)
            else:
                print("🔓 Using standard decryption method")
                return self._decrypt_standard_token(encrypted_data, password)
            
        except Exception as e:
            print(f"❌ Token decryption failed: {e}")
            return None
    
    def _decrypt_yubikey_token(self, encrypted_data, passcode=None):
        """Decrypt YubiKey-encrypted token"""
        try:
            # Import YubiKey manager
            import sys
            sys.path.append(str(self.project_root / "scripts" / "enc"))
            from yubikey_token_manager import YubiKeyTokenManager
            
            manager = YubiKeyTokenManager()
            token = manager.decrypt_infisical_token(passcode, quiet=False)
            
            if not token:
                return None
            
            # YubiKey manager returns raw token string, so we need to create the token structure
            # Try to parse as JSON first (in case it's a complex token), otherwise treat as raw token
            try:
                return json.loads(token)
            except json.JSONDecodeError:
                # Raw token string - return as simple token structure
                return {"token": token}
            
        except ImportError:
            print("❌ YubiKey manager not available")
            return None
        except Exception as e:
            print(f"❌ YubiKey decryption failed: {e}")
            return None
    
    def _decrypt_standard_token(self, encrypted_data, password=None):
        """Decrypt standard encrypted token"""
        try:
            if password is None:
                password = getpass.getpass("🔑 Enter decryption password: ")
            
            if not password:
                print("❌ No password provided")
                return None
            
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
            
            print("✅ Token decrypted successfully")
            return token_info
            
        except Exception as e:
            print(f"❌ Standard decryption failed: {e}")
            return None
    
    def show_environment_status(self):
        """Show current environment and system status"""
        print("🔍 Environment Status Check")
        print("=" * 30)
        
        # Check .env file
        if self.env_file.exists():
            print(f"  📄 .env file: ✅ Found at {self.env_file}")
            try:
                with open(self.env_file, 'r') as f:
                    line_count = len([line for line in f if line.strip() and not line.startswith('#')])
                print(f"  📊 Variables: {line_count} environment variables")
            except Exception:
                print("  📊 Variables: Unable to count")
        else:
            print(f"  📄 .env file: ❌ Not found at {self.env_file}")
        
        # Check encrypted token
        if self.encrypted_tokens_file.exists():
            print(f"  🔐 Encrypted token: ✅ Found at {self.encrypted_tokens_file}")
        else:
            print(f"  🔐 Encrypted token: ❌ Not found at {self.encrypted_tokens_file}")
        
        # Check Infisical CLI
        try:
            result = subprocess.run(['infisical', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"  🔧 Infisical CLI: ✅ {version}")
            else:
                print(f"  🔧 Infisical CLI: ❌ Error: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("  🔧 Infisical CLI: ❌ Timeout")
        except FileNotFoundError:
            print("  🔧 Infisical CLI: ❌ Not installed")
        except Exception as e:
            print(f"  🔧 Infisical CLI: ❌ Error: {e}")
        
        # Check Python dependencies
        try:
            from cryptography.fernet import Fernet
            print(f"  🐍 Python cryptography: ✅ Available")
        except ImportError:
            print(f"  🐍 Python cryptography: ❌ Missing")
    
    def sync_secrets(self):
        """Main method to sync secrets from Infisical"""
        print("🚀 Starting Infisical Secrets Synchronization...")
        print("=" * 50)
        
        # Step 1: Load Infisical config (optional)
        config = self.load_infisical_config()
        if config.get("workspaceId"):
            print("✅ .infisical.json config loaded")
        else:
            print("ℹ️ No .infisical.json config file found (optional)")
        
        # Step 2: Decrypt token
        token_data = self.decrypt_token()
        if not token_data:
            return False
        
        # Step 3: Export secrets directly using token
        if not self.export_secrets_with_token(token_data):
            return False
        
        print("🎉 Secrets synchronization completed successfully!")
        print(f"📄 Environment file created: {self.env_file}")
        return True
    
    def export_secrets_with_token(self, token_data):
        """Export secrets directly using token (no login required)"""
        try:
            print("🔄 Exporting secrets from Infisical...")
            
            # Handle different token formats - extract the actual token
            if isinstance(token_data, dict):
                if "token" in token_data:
                    # Simple token structure from YubiKey
                    token = token_data["token"]
                elif "client_secret" in token_data:
                    # If it's client credentials, use client_secret as token
                    token = token_data["client_secret"]
                else:
                    print("❌ Unknown token data format")
                    return False
            else:
                # Raw token string
                token = str(token_data)
            
            # Build infisical secrets command with direct token usage
            infisical_cmd = [
                'infisical', 'secrets',
                '--projectId=13bce4c5-1ffc-478b-b1ce-76726074f358',
                '--env=dev',
                '--recursive',
                '--domain=http://100.74.180.50',
                f'--token={token}'
            ]
            
            print("🚀 Running Infisical secrets export...")
            
            # Run command and capture output
            result = subprocess.run(infisical_cmd, capture_output=True, text=True, cwd=str(self.project_root))
            
            if result.returncode == 0:
                print("✅ Secrets exported successfully")
                return self.parse_and_save_secrets(result.stdout)
            else:
                print(f"❌ Infisical secrets export failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Secrets export error: {e}")
            return False
    
    def parse_and_save_secrets(self, secrets_output):
        """Parse Infisical secrets output and save to .env file"""
        try:
            print("📝 Processing secrets...")
            
            # Parse the table output to extract key-value pairs
            env_vars = {}
            lines = secrets_output.strip().split('\n')
            
            # Find the table content (skip headers and separators)
            in_table = False
            for line in lines:
                line = line.strip()
                if '│ SECRET NAME │' in line:
                    in_table = True
                    continue
                elif line.startswith('├─') or line.startswith('└─'):
                    continue
                elif in_table and line.startswith('│') and line.endswith('│'):
                    # Parse table row: │ KEY │ VALUE │ TYPE │
                    parts = [part.strip() for part in line.split('│') if part.strip()]
                    if len(parts) >= 2:
                        key = parts[0]
                        value = parts[1]
                        if key and value and key != 'SECRET NAME':
                            env_vars[key] = value
            
            if not env_vars:
                print("❌ No secrets found in output")
                return False
            
            # Write to .env file
            with open(self.env_file, 'w') as f:
                f.write("# Infisical Environment Variables\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
                
                for key, value in env_vars.items():
                    # Escape quotes in values
                    escaped_value = value.replace('"', '\\"')
                    f.write(f'{key}="{escaped_value}"\n')
            
            print(f"✅ {len(env_vars)} secrets saved to {self.env_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error processing secrets: {e}")
            return False

def main():
    """Main entry point for the secrets manager"""
    manager = InfisicalSecretsManager()
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h"]:
            print("🔐 Infisical Secrets Manager")
            print("Usage:")
            print("  python secrets-manager.py               # Interactive mode")
            print("  python secrets-manager.py --status      # Show status")
            print("  python secrets-manager.py --help        # Show help")
            return
        elif sys.argv[1] in ["--status", "-s"]:
            manager.show_environment_status()
            return
        else:
            print("❌ Unknown argument. Use --help for usage information.")
            return
    else:
        # Interactive mode
        success = manager.sync_secrets()
    
    if success:
        print("\n🎉 Success!")
        sys.exit(0)
    else:
        print("\n❌ Failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 