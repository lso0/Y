#!/usr/bin/env python3
import os
import json
import logging
import requests
import sqlite3
from datetime import datetime
from pathlib import Path

# ─── Setup logging ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ─── Load environment variables ─────────────────────────────────────────────
def load_env_file():
    """Load environment variables from ../../.env file"""
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if not env_path.exists():
        raise Exception(f"Environment file not found: {env_path}")
    
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value.strip('\'"')
    return env_vars

# Load environment variables
try:
    env_vars = load_env_file()
    FASTMAIL_EMAIL = env_vars.get('FM_M_0')
    FASTMAIL_PASSWORD = env_vars.get('FM_P_0')
    FASTMAIL_API_TOKEN = env_vars.get('FM_API_0')
    
    if not all([FASTMAIL_EMAIL, FASTMAIL_API_TOKEN]):
        raise Exception("Missing required environment variables: FM_M_0, FM_API_0")
        
    print(f"Email: {FASTMAIL_EMAIL}")
    print(f"API Token: {'*'*len(FASTMAIL_API_TOKEN) if FASTMAIL_API_TOKEN else None}")
except Exception as e:
    print(f"Error loading environment variables: {e}")
    print("Please make sure the .env file exists with FM_M_0 and FM_API_0 variables")
    exit(1)

# ─── Database setup ─────────────────────────────────────────────────────────
class AliasDatabase:
    def __init__(self, db_path: str = "aliases.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with aliases table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aliases (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_alias(self, alias_data: dict):
        """Save or update an alias in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO aliases 
            (id, email, name, description, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            alias_data.get('id'),
            alias_data.get('email'),
            alias_data.get('name', ''),
            alias_data.get('description', ''),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_aliases(self) -> list:
        """Get all aliases from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, email, name, description, created_at, is_active 
            FROM aliases 
            WHERE is_active = 1
            ORDER BY created_at DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'email': row[1], 
                'name': row[2],
                'description': row[3],
                'created_at': row[4],
                'is_active': row[5]
            }
            for row in results
        ]
    
    def delete_alias(self, alias_id: str):
        """Mark an alias as inactive (soft delete)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE aliases 
            SET is_active = 0, updated_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), alias_id))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> dict:
        """Get alias statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM aliases WHERE is_active = 1')
        active_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM aliases WHERE is_active = 0')
        deleted_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'active': active_count,
            'deleted': deleted_count,
            'total': active_count + deleted_count
        }

class FastMailAliasManager:
    def __init__(self, email: str, api_token: str):
        self.session = requests.Session()
        self.email = email
        self.base_url = None          # will be set from /.well-known/jmap
        self.account_id = None        # JMAP mail account ID
        self.session_state = None
        self.db = AliasDatabase()

        # Standard headers; we'll fill in Authorization below
        self.headers = {
            "Content-Type": "application/json",
            "Accept":       "application/json",
            "X-ME-ConnectionId": "fastmail-alias-manager",
            "Origin":  "https://app.fastmail.com",
            "Referer": "https://app.fastmail.com/",
            "User-Agent": "FastMail Alias Manager/1.0",
        }

        # Put the Bearer token into headers now
        self.headers["Authorization"] = f"Bearer {api_token}"

    def login(self) -> bool:
        """
        1) GET https://api.fastmail.com/.well-known/jmap 
           using Authorization: Bearer <api_token>
        2) Extract apiUrl and mail accountId from JSON
        3) POST a Core/echo to fetch sessionState
        """
        try:
            # ─── STEP 1: Discover JMAP endpoint via ".well-known/jmap" ─────────────
            session_url = "https://api.fastmail.com/.well-known/jmap"
            print("Step 1: GET /.well-known/jmap (Bearer token)")
            resp = self.session.get(session_url, headers=self.headers)
            if resp.status_code != 200:
                raise Exception(
                    f"Failed to fetch JMAP session: {resp.status_code} – {resp.text}"
                )

            info = resp.json()
            self.base_url = info.get("apiUrl")
            if not self.base_url:
                raise Exception("No apiUrl in /.well-known/jmap response")

            primary = info.get("primaryAccounts", {})
            mail_acc = primary.get("urn:ietf:params:jmap:mail")
            if not mail_acc:
                raise Exception("No mail accountId in /.well-known/jmap response")
            self.account_id = mail_acc

            print(f"✓ Found JMAP endpoint: {self.base_url}")
            print(f"✓ Found mail accountId: {self.account_id}")

            # ─── STEP 2: Core/echo → fetch a sessionState ─────────────────────────
            echo_payload = {
                "using": ["urn:ietf:params:jmap:core"],
                "methodCalls": [
                    ["Core/echo", {"hello": "world"}, "0"]
                ]
            }
            print("Step 2: POST Core/echo → fetch sessionState")
            echo_resp = self.session.post(
                self.base_url,
                headers=self.headers,
                json=echo_payload
            )
            if echo_resp.status_code != 200:
                raise Exception(
                    f"Core/echo failed: {echo_resp.status_code} – {echo_resp.text}"
                )

            echo_data = echo_resp.json()
            self.session_state = echo_data.get("sessionState")
            if not self.session_state:
                raise Exception("No sessionState in Core/echo response")

            print(f"✓ Received sessionState: {self.session_state}")
            return True

        except Exception as e:
            print(f"Login error: {e}")
            return False

    def list_aliases(self) -> list:
        """
        List all email aliases via Identity/get JMAP call and sync with database.
        Returns a list of Identity objects (each one has "id" and "email").
        """
        try:
            payload = {
                "using": [
                    "urn:ietf:params:jmap:core",
                    "urn:ietf:params:jmap:mail"
                ],
                "methodCalls": [
                    [
                        "Identity/get",
                        { "accountId": self.account_id },
                        "0"
                    ]
                ],
                "sessionState": self.session_state
            }
            resp = self.session.post(
                self.base_url,
                headers=self.headers,
                json=payload
            )
            if resp.status_code != 200:
                raise Exception(f"Failed to list aliases: {resp.status_code} – {resp.text}")

            data = resp.json()
            aliases = []
            for method_resp in data.get("methodResponses", []):
                if method_resp[0] == "Identity/get":
                    aliases = method_resp[1].get("list", [])
                    break
            
            # Sync aliases with database
            for alias in aliases:
                self.db.save_alias(alias)
            
            return aliases

        except Exception as e:
            print(f"Error listing aliases: {e}")
            return []

    def create_alias(self, alias_name: str, description: str = "") -> dict | None:
        """
        Create a new email alias via Identity/set JMAP call and save to database.
        """
        try:
            payload = {
                "using": [
                    "urn:ietf:params:jmap:core",
                    "urn:ietf:params:jmap:mail"
                ],
                "methodCalls": [
                    [
                        "Identity/set",
                        {
                            "accountId": self.account_id,
                            "create": {
                                "newAlias": {
                                    "name": alias_name,
                                    "email": f"{alias_name}@fastmail.com"
                                }
                            }
                        },
                        "0"
                    ]
                ],
                "sessionState": self.session_state
            }
            resp = self.session.post(
                self.base_url,
                headers=self.headers,
                json=payload
            )
            if resp.status_code != 200:
                raise Exception(f"Failed to create alias: {resp.status_code} – {resp.text}")

            data = resp.json()
            for method_resp in data.get("methodResponses", []):
                if method_resp[0] == "Identity/set":
                    # 1) Update our session_state to the returned "newState"
                    new_state = method_resp[1].get("newState")
                    if new_state:
                        self.session_state = new_state

                    # 2) Pull out whatever key the server generated under "created"
                    created_map = method_resp[1].get("created", {})
                    if created_map:
                        # There will be exactly one entry in `created_map`.
                        new_id, new_obj = next(iter(created_map.items()))
                        
                        # Save to database with description
                        new_obj['description'] = description
                        self.db.save_alias(new_obj)
                        
                        return new_obj
                    else:
                        return None

            return None

        except Exception as e:
            print(f"Error creating alias: {e}")
            return None

    def delete_alias(self, alias_id: str) -> list:
        """
        Delete an email alias via Identity/set JMAP call and update database.
        """
        try:
            payload = {
                "using": [
                    "urn:ietf:params:jmap:core",
                    "urn:ietf:params:jmap:mail"
                ],
                "methodCalls": [
                    [
                        "Identity/set",
                        {
                            "accountId": self.account_id,
                            "destroy": [alias_id]
                        },
                        "0"
                    ]
                ],
                "sessionState": self.session_state
            }
            resp = self.session.post(
                self.base_url,
                headers=self.headers,
                json=payload
            )
            if resp.status_code != 200:
                raise Exception(f"Failed to delete alias: {resp.status_code} – {resp.text}")

            data = resp.json()
            for method_resp in data.get("methodResponses", []):
                if method_resp[0] == "Identity/set":
                    # 1) Update our session_state to whatever "newState" the server sent
                    new_state = method_resp[1].get("newState")
                    if new_state:
                        self.session_state = new_state

                    # 2) Update database (soft delete)
                    destroyed = method_resp[1].get("destroyed", [])
                    for del_id in destroyed:
                        self.db.delete_alias(del_id)

                    return destroyed

            return []
        except Exception as e:
            print(f"Error deleting alias: {e}")
            return []

    def get_stats(self) -> dict:
        """Get alias statistics from database"""
        return self.db.get_stats()

def main():
    # Use environment variables
    email = FASTMAIL_EMAIL
    api_token = FASTMAIL_API_TOKEN

    if not all([email, api_token]):
        print("Please set both FM_M_0 and FM_API_0 in .env file, then rerun.")
        return

    manager = FastMailAliasManager(email, api_token)
    if manager.login():
        print("Login successful!\n")

        # List current aliases and sync with database
        aliases = manager.list_aliases()
        print("Current aliases:")
        if not aliases:
            print("  (none)")
        else:
            for alias in aliases:
                print(f"  - {alias.get('email')} (ID: {alias.get('id')})")
        
        # Show statistics
        stats = manager.get_stats()
        print(f"\nAlias Statistics:")
        print(f"  Active: {stats['active']}")
        print(f"  Total: {stats['total']}")

    else:
        print("Login failed!")

if __name__ == "__main__":
    main()
