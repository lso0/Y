#!/usr/bin/env python3
import os
import json
import logging
import requests
from infisical_client import InfisicalClient, ClientSettings, GetSecretOptions

# ─── Setup logging ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ─── Initialize Infisical client ────────────────────────────────────────────
settings = ClientSettings(
    access_token="st.0bb5c3fd-9c7a-4d4a-ba21-cf52f19fe138.82a484eeef259b2d7b86981beb097f3e.2f6edc5753315a2785e9857975b30c76",
    site_url="http://192.168.1.14:80"  # your Infisical instance
)
client = InfisicalClient(settings)

# Get secrets from Infisical
try:
    # Get each secret individually using the new SDK methods
    email_options = GetSecretOptions(
        environment="prod",
        project_id="Y",  # Your project ID
        secret_name="FASTMAIL_EMAIL"
    )
    token_options = GetSecretOptions(
        environment="prod", 
        project_id="Y",  # Your project ID
        secret_name="FASTMAIL_API_TOKEN"
    )
    
    email_secret = client.getSecret(email_options)
    token_secret = client.getSecret(token_options)
    
    FASTMAIL_EMAIL = email_secret.secret_value
    FASTMAIL_API_TOKEN = token_secret.secret_value
    
    print(f"Email: {FASTMAIL_EMAIL}")
    print(f"API Token: {'*'*len(FASTMAIL_API_TOKEN) if FASTMAIL_API_TOKEN else None}")
except Exception as e:
    print(f"Error getting secrets from Infisical: {e}")
    print("Please make sure:")
    print("1. Your Infisical server is running at http://192.168.1.14:80")
    print("2. You have replaced 'YOUR_PERSONAL_ACCESS_TOKEN' with your actual token")
    print("3. The secrets FASTMAIL_EMAIL and FASTMAIL_API_TOKEN exist in the 'prod' environment")
    print("4. The project ID 'Y' is correct")
    exit(1)

class FastMailAliasManager:
    def __init__(self, email: str, api_token: str):
        self.session = requests.Session()
        self.email = email
        self.base_url = None          # will be set from /.well-known/jmap
        self.account_id = None        # JMAP mail account ID
        self.session_state = None

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
        List all email aliases via Identity/get JMAP call.
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
            for method_resp in data.get("methodResponses", []):
                if method_resp[0] == "Identity/get":
                    return method_resp[1].get("list", [])
            return []

        except Exception as e:
            print(f"Error listing aliases: {e}")
            return []

    def create_alias(self, alias_name: str) -> dict | None:
        """
        Create a new email alias via Identity/set JMAP call:
          {
            "using": [...],
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
        On success, Fastmail returns something like:
        {
          "methodResponses": [
            [
              "Identity/set",
              {
                "accountId":"u2ef64041",
                "oldState":"(old sessionState)",
                "newState":"(updated sessionState)",
                "created": {
                  "<some-UUID>": {
                    "id":"<some-UUID>",
                    "name":"test00",
                    "email":"test00@fastmail.com",
                    …other fields…
                  }
                },
                "destroyed":[]
              },
              "0"
            ]
          ],
          "sessionState":"(updated sessionState)"
        }
        We must pull out that "newState" and store it in self.session_state before returning.
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
                        return new_obj
                    else:
                        return None

            return None

        except Exception as e:
            print(f"Error creating alias: {e}")
            return None


    def delete_alias(self, alias_id: str) -> list:
        """
        Delete an email alias via Identity/set JMAP call:
          {
            "using": [...],
            "methodCalls": [
              [
                "Identity/set",
                {
                  "accountId": self.account_id,
                  "destroy": [ alias_id ]
                },
                "0"
              ]
            ],
            "sessionState": self.session_state
          }
        On success, Fastmail returns something like:
        {
          "methodResponses": [
            [
              "Identity/set",
              {
                "accountId":"u2ef64041",
                "oldState":"(old sessionState)",
                "newState":"(updated sessionState)",
                "created": { … },
                "destroyed":[ "<the-id-we-just-destroyed>" ]
              },
              "0"
            ]
          ],
          "sessionState":"(updated sessionState)"
        }
        We must pull out that "newState" before returning.
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

                    # 2) Return the "destroyed" array (usually [alias_id])
                    return method_resp[1].get("destroyed", [])

            return []
        except Exception as e:
            print(f"Error deleting alias: {e}")
            return []


def main():
    # Use secrets from Infisical
    email = FASTMAIL_EMAIL
    api_token = FASTMAIL_API_TOKEN

    print(f"Email: {email}")
    print(f"API Token: {'*'*len(api_token) if api_token else None}")

    if not all([email, api_token]):
        print("Please set both FASTMAIL_EMAIL and FASTMAIL_API_TOKEN in Infisical, then rerun.")
        return

    manager = FastMailAliasManager(email, api_token)
    if manager.login():
        print("Login successful!\n")

        # ─── Create a new alias "test001" ───────────────────────────────────
        new_alias = manager.create_alias("test001")
        if new_alias:
            print(f"✓ Created new alias: {new_alias['email']} (ID: {new_alias['id']})\n")
        else:
            print("✗ Failed to create a new alias.\n")

        # ─── Now list current aliases ────────────────────────────────────────
        aliases = manager.list_aliases()
        print("Current aliases:")
        if not aliases:
            print("  (none)")
        else:
            for alias in aliases:
                print(f"  - {alias.get('email')} (ID: {alias.get('id')})")

        # ─── (Optional) Delete that same alias again ─────────────────────────
        if aliases:
            to_delete = aliases[0].get("id")
            destroyed = manager.delete_alias(to_delete)
            if destroyed:
                print(f"\n✓ Deleted alias with ID: {destroyed[0]}")
            else:
                print(f"\n✗ Failed to delete alias ID: {to_delete}")
    else:
        print("Login failed!")

if __name__ == "__main__":
    main()
