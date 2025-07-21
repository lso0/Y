#!/usr/bin/env python3
"""
Infisical Secrets Manager - Streamlined Version
Decrypts token, authenticates with Infisical, and extracts all secrets to .env file
"""

import os
import sys
import json
import subprocess
import base64
import getpass
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class InfisicalSecretsManager:
    def __init__(self):
        self.project_root = Path("/Users/wgm0/Documents/Y")
        self.env_file = self.project_root / ".env"
        self.infisical_config = self.project_root / ".infisical.json"
        self.encrypted_token_file = self.project_root / "scripts" / "enc" / "encrypted_token.json"
        
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
    
    def decrypt_token(self, password=None):
        """Decrypt the Infisical token from encrypted file"""
        try:
            print("🔓 Decrypting Infisical token...")
            
            if not self.encrypted_token_file.exists():
                print(f"❌ Encrypted token file not found: {self.encrypted_token_file}")
                return None
            
            # Load encrypted token file
            with open(self.encrypted_token_file, 'r') as f:
                encrypted_data = json.load(f)
            
            if password is None:
                password = getpass.getpass("🔑 Enter decryption password: ")
            
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
            
            print("✅ Token decrypted successfully")
            return token_data
            
        except Exception as e:
            print(f"❌ Token decryption failed: {e}")
            return None
    
    def authenticate_infisical(self, token_data):
        """Authenticate with Infisical using decrypted credentials"""
        try:
            print("🔐 Authenticating with Infisical...")
            
            client_id = token_data.get('client_id')
            client_secret = token_data.get('client_secret')
            
            if not client_id or not client_secret:
                print("❌ Missing client_id or client_secret in token data")
                return False
            
            # Set environment variables for Infisical CLI
            env = os.environ.copy()
            env['INFISICAL_CLIENT_ID'] = client_id
            env['INFISICAL_CLIENT_SECRET'] = client_secret
            
            # Run Infisical authentication
            result = subprocess.run([
                "infisical", "auth", "universal-auth", 
                "--client-id", client_id,
                "--client-secret", client_secret
            ], capture_output=True, text=True, cwd=str(self.project_root), env=env)
            
            if result.returncode == 0:
                print("✅ Infisical authentication successful")
                return True
            else:
                print(f"❌ Infisical authentication failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def get_all_secrets(self):
        """Get all secrets from Infisical"""
        try:
            print("📦 Fetching all secrets from Infisical...")
            
            # Get secrets in JSON format
            result = subprocess.run([
                "infisical", "secrets", "get", "--format", "json"
            ], capture_output=True, text=True, cwd=str(self.project_root))
            
            if result.returncode == 0:
                secrets_data = json.loads(result.stdout)
                print(f"✅ Retrieved {len(secrets_data)} secrets from Infisical")
                return secrets_data
            else:
                print(f"❌ Failed to get secrets: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching secrets: {e}")
            return None
    
    def load_existing_env(self):
        """Load existing .env file"""
        existing_vars = {}
        if self.env_file.exists():
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            # Remove quotes if present
                            value = value.strip("'\"")
                            existing_vars[key] = value
                print(f"📖 Loaded {len(existing_vars)} existing environment variables")
            except Exception as e:
                print(f"⚠️ Error reading existing .env: {e}")
        return existing_vars
    
    def update_env_file(self, secrets_data):
        """Update .env file with secrets from Infisical"""
        try:
            print("💾 Updating .env file...")
            
            # Load existing variables
            existing_vars = self.load_existing_env()
            
            # Convert Infisical secrets to env format
            infisical_vars = {}
            for secret in secrets_data:
                key = secret.get('secretKey')
                value = secret.get('secretValue')
                if key and value is not None:
                    infisical_vars[key] = value
            
            print(f"🔄 Found {len(infisical_vars)} secrets from Infisical:")
            for key in sorted(infisical_vars.keys()):
                masked_value = infisical_vars[key][:3] + "***" if len(infisical_vars[key]) > 3 else "***"
                print(f"  {key} = {masked_value}")
            
            # Merge with existing variables (Infisical takes precedence)
            all_vars = {**existing_vars, **infisical_vars}
            
            # Create backup of existing .env
            if self.env_file.exists():
                backup_file = self.env_file.with_suffix('.env.backup')
                subprocess.run(['cp', str(self.env_file), str(backup_file)])
                print(f"📋 Created backup: {backup_file}")
            
            # Write updated .env file
            with open(self.env_file, 'w') as f:
                f.write("# Auto-generated .env file with Infisical secrets\n")
                f.write(f"# Generated on: {subprocess.check_output(['date']).decode().strip()}\n")
                f.write("# DO NOT EDIT MANUALLY - Use scripts/infisical/secrets-manager.py\n\n")
                
                # Group variables by prefix for better organization
                grouped_vars = {}
                for key, value in sorted(all_vars.items()):
                    prefix = key.split('_')[0] if '_' in key else 'OTHER'
                    if prefix not in grouped_vars:
                        grouped_vars[prefix] = []
                    grouped_vars[prefix].append((key, value))
                
                # Write grouped variables
                for prefix in sorted(grouped_vars.keys()):
                    f.write(f"# {prefix} Configuration\n")
                    for key, value in grouped_vars[prefix]:
                        # Quote values that contain special characters
                        if any(c in value for c in [' ', '"', "'", '$', '`', '\\']):
                            f.write(f"{key}='{value}'\n")
                        else:
                            f.write(f"{key}={value}\n")
                    f.write("\n")
            
            print(f"✅ Updated .env file with {len(all_vars)} total variables")
            print(f"📍 Location: {self.env_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to update .env file: {e}")
            return False
    
    def show_status(self):
        """Show current system status"""
        print("📊 Current Status:")
        
        # Check .env file
        if self.env_file.exists():
            try:
                with open(self.env_file, 'r') as f:
                    env_count = sum(1 for line in f if line.strip() and not line.startswith('#') and '=' in line)
                env_date = "Unknown"
                try:
                    with open(self.env_file, 'r') as f:
                        for line in f:
                            if "Generated on:" in line:
                                env_date = line.split("Generated on:")[1].strip()
                                break
                except:
                    pass
                print(f"  📁 .env file: ✅ Found ({env_count} variables, generated: {env_date})")
            except:
                print(f"  📁 .env file: ⚠️ Found but unreadable")
        else:
            print(f"  📁 .env file: ❌ Not found")
        
        # Check encrypted token
        if self.encrypted_token_file.exists():
            print(f"  🔐 Encrypted token: ✅ Found at {self.encrypted_token_file}")
        else:
            print(f"  🔐 Encrypted token: ❌ Not found at {self.encrypted_token_file}")
        
        # Check Infisical CLI
        try:
            result = subprocess.run(['infisical', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"  🛠️  Infisical CLI: ✅ Installed ({version})")
            else:
                print(f"  🛠️  Infisical CLI: ❌ Not working")
        except:
            print(f"  🛠️  Infisical CLI: ❌ Not installed")
        
        # Check Python dependencies
        try:
            import cryptography
            print(f"  🐍 Python cryptography: ✅ Available")
        except:
            print(f"  🐍 Python cryptography: ❌ Missing")
    
    def run_full_sync(self, password=None):
        """Run the complete secrets synchronization process"""
        print("🚀 Starting Infisical Secrets Synchronization...")
        print("=" * 50)
        
        # Step 1: Load Infisical config (optional)
        config = self.load_infisical_config()
        # Config is now always returned, so we continue regardless
        
        # Step 2: Decrypt token
        token_data = self.decrypt_token(password)
        if not token_data:
            return False
        
        # Step 3: Authenticate with Infisical
        if not self.authenticate_infisical(token_data):
            return False
        
        # Step 4: Get all secrets
        secrets_data = self.get_all_secrets()
        if secrets_data is None:
            return False
        
        # Step 5: Update .env file
        if not self.update_env_file(secrets_data):
            return False
        
        print("=" * 50)
        print("🎉 Secrets synchronization completed successfully!")
        print(f"📂 Secrets available in: {self.env_file}")
        print("💡 Usage examples:")
        print("   # Load secrets in current shell:")
        print("   source .env")
        print("   # Run YouTube automation:")
        print("   python3 cli_x/dev/auto/services/youtube/scripts/youtube_automation_env.py")
        
        return True

def main():
    """Main function"""
    manager = InfisicalSecretsManager()
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h"]:
            print("Infisical Secrets Manager - Streamlined Version")
            print("Usage:")
            print("  python3 secrets-manager.py              # Interactive sync")
            print("  python3 secrets-manager.py <password>   # Non-interactive sync")
            print("  python3 secrets-manager.py --status     # Show system status")
            print("  python3 secrets-manager.py --help       # Show this help")
            return
        elif sys.argv[1] in ["--status", "-s"]:
            manager.show_status()
            return
        else:
            # Assume it's a password
            password = sys.argv[1]
            success = manager.run_full_sync(password)
    else:
        # Interactive mode
        success = manager.run_full_sync()
    
    if success:
        print("\n🎯 Next steps:")
        print("1. Check the updated .env file: cat .env")
        print("2. Run YouTube automation: python3 cli_x/dev/auto/services/youtube/scripts/youtube_automation_env.py")
        sys.exit(0)
    else:
        print("\n❌ Secrets synchronization failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 