import os
import logging
import requests
import json
import sys
import argparse
import time
import multiprocessing
import fcntl
from datetime import datetime
from dotenv import load_dotenv

# Set up logging with configurable level
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable urllib3 debugging if debug level is set
if LOG_LEVEL == 'DEBUG':
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.DEBUG)
    logger.debug("Debug logging enabled - HTTP requests will be verbose")

# Directory paths - relative to script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, "db")
LOGS_DIR = os.path.join(SCRIPT_DIR, "logs")
MAX_PROJECTS_PER_BATCH = 20  # Maximum number of projects to create in one batch
RATE_LIMIT_DELAY = 1  # Delay between API calls in seconds
MAX_CONCURRENT_ACCOUNTS = 3  # Maximum number of accounts to process concurrently

# Create necessary directories if they don't exist
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

class RevenueCatAutomation:
    def __init__(self, account_id):
        self.session = requests.Session()
        self.base_url = "https://api.revenuecat.com"
        self.headers = {
            'Content-Type': 'application/json',
            'x-requested-with': 'XMLHttpRequest'
        }
        self.account_id = account_id
        self.db_file = os.path.join(DB_DIR, f"{account_id}_db.json")
        self.load_db()
        self.rate_limit_counter = 0

    def rate_limit(self):
        """Implement rate limiting between API calls."""
        self.rate_limit_counter += 1
        if self.rate_limit_counter % 2 == 0:  # Every 2 API calls
            time.sleep(RATE_LIMIT_DELAY)

    def load_db(self):
        """Load the database from account-specific db.json file."""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r') as f:
                    self.db = json.load(f)
            else:
                self.db = {"projects": {}}
                self.save_db()
        except Exception as e:
            logger.error(f"Error loading database: {str(e)}")
            self.db = {"projects": {}}

    def save_db(self):
        """Save the database to account-specific db.json file."""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.db, f, indent=2)
            logger.info(f"Database saved to {self.db_file}")
        except Exception as e:
            logger.error(f"Error saving database: {str(e)}")

    def save_project_data(self, project_data, api_key_data):
        """Save project and API key data to the database."""
        try:
            project_id = project_data.get('id')
            if project_id:
                self.db["projects"][project_id] = {
                    "project": {
                        "name": project_data.get('name'),
                        "id": project_id,
                        "created_at": datetime.now().isoformat()
                    },
                    "api_key": {
                        "key": api_key_data.get('key'),
                        "id": api_key_data.get('id'),
                        "label": api_key_data.get('label'),
                        "created_at": api_key_data.get('created_at')
                    }
                }
                self.save_db()
                logger.info(f"Project data saved to database for account {self.account_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving project data: {str(e)}")
            return False

    def delete_project(self, project_name):
        """Delete a project by name."""
        try:
            # Find project ID by name
            project_id = None
            for pid, data in self.db["projects"].items():
                if data["project"]["name"] == project_name:
                    project_id = pid
                    break

            if not project_id:
                logger.error(f"Project '{project_name}' not found in database for account {self.account_id}")
                return False

            # Delete from RevenueCat
            url = f"{self.base_url}/internal/v1/developers/me/projects/{project_id}"
            headers = self.headers.copy()
            headers.update({
                'Accept': 'application/json',
                'Origin': 'https://app.revenuecat.com',
                'Referer': 'https://app.revenuecat.com/'
            })

            response = self.session.delete(url, headers=headers)
            
            if response.status_code in [200, 204]:
                # Remove from database
                del self.db["projects"][project_id]
                self.save_db()
                logger.info(f"Successfully deleted project: {project_name} from account {self.account_id}")
                return True
            else:
                logger.error(f"Project deletion failed with status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error deleting project: {str(e)}")
            return False

    def get_project_by_name(self, project_name):
        """Get project data by name from the database."""
        for data in self.db["projects"].values():
            if data["project"]["name"] == project_name:
                return data
        return None

    def save_to_json(self, project_data, api_key_data):
        """Save project and API key data to a JSON file."""
        try:
            # Create data structure
            data = {
                "project": {
                    "name": project_data.get('name'),
                    "id": project_data.get('id'),
                    "created_at": datetime.now().isoformat()
                },
                "api_key": {
                    "key": api_key_data.get('key'),
                    "id": api_key_data.get('id'),
                    "label": api_key_data.get('label'),
                    "created_at": api_key_data.get('created_at')
                }
            }
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"revenuecat_data_{timestamp}.json"
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Data saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving data to JSON: {str(e)}")
            return None

    def login(self, email, password):
        """Login to RevenueCat and get session cookies."""
        try:
            # First, get the login page to get any initial cookies
            login_url = "https://app.revenuecat.com/login"
            logger.debug(f"Getting login page: {login_url}")
            page_response = self.session.get(login_url)
            logger.debug(f"Login page response status: {page_response.status_code}")
            
            # Prepare login request
            login_data = {
                "email": email,
                "password": password
            }
            login_api_url = f"{self.base_url}/v1/developers/login"
            
            logger.info(f"Attempting login for account {self.account_id}")
            logger.debug(f"Login URL: {login_api_url}")
            logger.debug(f"Login email: {email}")
            logger.debug(f"Request headers: {self.headers}")
            logger.debug(f"Session cookies before login: {dict(self.session.cookies)}")
            
            # Perform login
            response = self.session.post(
                login_api_url,
                json=login_data,
                headers=self.headers
            )
            
            logger.debug(f"Login response status: {response.status_code}")
            logger.debug(f"Login response headers: {dict(response.headers)}")
            logger.debug(f"Session cookies after login: {dict(self.session.cookies)}")
            
            if response.status_code == 200:
                logger.info(f"Login successful for account {self.account_id}")
                try:
                    response_json = response.json()
                    logger.debug(f"Login response JSON: {response_json}")
                except:
                    logger.debug("Login response is not JSON format")
                return True
            else:
                logger.error(f"Login failed for account {self.account_id} with status code: {response.status_code}")
                
                # Log response content for debugging
                try:
                    response_text = response.text
                    logger.error(f"Response body: {response_text}")
                    
                    # Try to parse as JSON for better formatting
                    try:
                        response_json = response.json()
                        logger.error(f"Response JSON: {json.dumps(response_json, indent=2)}")
                    except:
                        logger.error(f"Response text (non-JSON): {response_text}")
                        
                except Exception as content_error:
                    logger.error(f"Could not read response content: {str(content_error)}")
                
                # Log additional debugging info for 403 errors
                if response.status_code == 403:
                    logger.error("🔒 HTTP 403 Forbidden - Possible causes:")
                    logger.error("   1. Invalid credentials (check RC_E_* and RC_P_* environment variables)")
                    logger.error("   2. Account locked or suspended")
                    logger.error("   3. Rate limiting or IP blocking")
                    logger.error("   4. API endpoint changed or deprecated")
                    logger.error("   5. Required headers or authentication method changed")
                    logger.error(f"   6. Email being used: {email}")
                    
                return False
                
        except Exception as e:
            logger.error(f"Login error for account {self.account_id}: {str(e)}")
            logger.exception("Full login exception details:")
            return False

    def create_project(self, project_name):
        """Create a new project in RevenueCat using direct API call."""
        try:
            self.rate_limit()  # Rate limit before API call
            url = f"{self.base_url}/internal/v1/developers/me/projects"
            data = {"name": project_name}
            
            logger.debug(f"Creating project '{project_name}' for account {self.account_id}")
            logger.debug(f"Project creation URL: {url}")
            logger.debug(f"Project data: {data}")
            logger.debug(f"Request headers: {self.headers}")
            
            response = self.session.post(
                url,
                json=data,
                headers=self.headers
            )
            
            logger.debug(f"Project creation response status: {response.status_code}")
            logger.debug(f"Project creation response headers: {dict(response.headers)}")
            
            if response.status_code in [200, 201]:
                project_data = response.json()
                logger.info(f"Successfully created project: {project_name} for account {self.account_id}")
                logger.debug(f"Project details: {project_data}")
                return project_data
            else:
                logger.error(f"Project creation failed for '{project_name}' (account {self.account_id}) with status code: {response.status_code}")
                
                # Log detailed error response
                try:
                    response_text = response.text
                    logger.error(f"Response body: {response_text}")
                    
                    try:
                        response_json = response.json()
                        logger.error(f"Response JSON: {json.dumps(response_json, indent=2)}")
                    except:
                        logger.error(f"Response text (non-JSON): {response_text}")
                        
                except Exception as content_error:
                    logger.error(f"Could not read response content: {str(content_error)}")
                
                # Additional context for common errors
                if response.status_code == 403:
                    logger.error("🔒 Project creation forbidden - check if session is still valid")
                elif response.status_code == 409:
                    logger.error("🔄 Project name might already exist")
                elif response.status_code == 422:
                    logger.error("📝 Invalid project data - check project name format")
                    
                return None
                
        except Exception as e:
            logger.error(f"Project creation error for '{project_name}' (account {self.account_id}): {str(e)}")
            logger.exception("Full project creation exception details:")
            return None

    def create_api_key(self, project_id, label="APIKEYNAME1"):
        """Create a new API key for the project."""
        try:
            self.rate_limit()  # Rate limit before API call
            url = f"{self.base_url}/internal/v1/developers/me/projects/{project_id}/api_keys"
            data = {
                "label": label,
                "api_version": "2",
                "permissions": [
                    "charts_metrics:overview:read_write",
                    "customer_information:customers:read_write",
                    "customer_information:subscriptions:read_write",
                    "customer_information:purchases:read_write",
                    "customer_information:invoices:read_write",
                    "project_configuration:projects:read_write",
                    "project_configuration:apps:read_write",
                    "project_configuration:entitlements:read_write",
                    "project_configuration:offerings:read_write",
                    "project_configuration:packages:read_write",
                    "project_configuration:products:read_write"
                ]
            }
            
            headers = self.headers.copy()
            headers.update({
                'Accept': 'application/json',
                'Origin': 'https://app.revenuecat.com',
                'Referer': 'https://app.revenuecat.com/'
            })
            
            logger.debug(f"Creating API key '{label}' for project {project_id} (account {self.account_id})")
            logger.debug(f"API key creation URL: {url}")
            logger.debug(f"API key data: {json.dumps(data, indent=2)}")
            logger.debug(f"Request headers: {headers}")
            
            response = self.session.post(
                url,
                json=data,
                headers=headers
            )
            
            logger.debug(f"API key creation response status: {response.status_code}")
            logger.debug(f"API key creation response headers: {dict(response.headers)}")
            
            if response.status_code in [200, 201]:
                api_key_data = response.json()
                logger.info(f"Successfully created API key: {label} for project {project_id} (account {self.account_id})")
                logger.info(f"API Key: {api_key_data.get('key')}")
                logger.debug(f"API Key ID: {api_key_data.get('id')}")
                logger.debug(f"Full API key response: {api_key_data}")
                return api_key_data
            else:
                logger.error(f"API key creation failed for project {project_id} (account {self.account_id}) with status code: {response.status_code}")
                
                # Log detailed error response
                try:
                    response_text = response.text
                    logger.error(f"Response body: {response_text}")
                    
                    try:
                        response_json = response.json()
                        logger.error(f"Response JSON: {json.dumps(response_json, indent=2)}")
                    except:
                        logger.error(f"Response text (non-JSON): {response_text}")
                        
                except Exception as content_error:
                    logger.error(f"Could not read response content: {str(content_error)}")
                
                # Additional context for common errors
                if response.status_code == 403:
                    logger.error("🔒 API key creation forbidden - check if session is still valid")
                elif response.status_code == 404:
                    logger.error("🔍 Project not found - check if project ID is correct")
                elif response.status_code == 422:
                    logger.error("📝 Invalid API key data - check permissions or label format")
                    
                return None
                
        except Exception as e:
            logger.error(f"API key creation error for project {project_id} (account {self.account_id}): {str(e)}")
            logger.exception("Full API key creation exception details:")
            return None

    def close(self):
        """Clean up the session."""
        self.session.close()
        logger.info("Session closed")

def process_account(account_id, action, project_names):
    """Process a single account's operations."""
    try:
        # Set up logging for this process
        process_logger = logging.getLogger(f"Account_{account_id}")
        process_logger.setLevel(logging.INFO)
        
        # Create a file handler for this process in the logs directory
        log_file = os.path.join(LOGS_DIR, f"rc_a_{account_id}.log")
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        process_logger.addHandler(fh)
        
        # Load environment variables from parent directory
        load_dotenv('../.env')
        
        # Get account number from the account argument (e.g., A1 -> 1)
        account_num = account_id.lstrip('A')
        
        # Get credentials from environment variables
        email = os.getenv(f'RC_E_{account_num}')
        password = os.getenv(f'RC_P_{account_num}')
        
        if not email or not password:
            process_logger.error(f"Please set RC_E_{account_num} and RC_P_{account_num} environment variables")
            return
        
        automation = RevenueCatAutomation(account_id)
        try:
            if automation.login(email, password):
                if action == 'c_p':
                    total_projects = len(project_names)
                    success_count = 0
                    failed_projects = []

                    process_logger.info(f"Starting batch creation of {total_projects} projects...")
                    
                    for index, project_name in enumerate(project_names, 1):
                        process_logger.info(f"\nProcessing project {index}/{total_projects}: {project_name}")
                        project_data = automation.create_project(project_name)
                        if project_data:
                            project_id = project_data.get('id')
                            if project_id:
                                api_key_data = automation.create_api_key(project_id)
                                if api_key_data:
                                    process_logger.info(f"Successfully created project and API key for: {project_name}")
                                    automation.save_project_data(project_data, api_key_data)
                                    success_count += 1
                                else:
                                    process_logger.error(f"Failed to create API key for: {project_name}")
                                    failed_projects.append(project_name)
                            else:
                                process_logger.error(f"Could not get project ID for: {project_name}")
                                failed_projects.append(project_name)
                        else:
                            process_logger.error(f"Failed to create project: {project_name}")
                            failed_projects.append(project_name)
                    
                    # Summary report
                    process_logger.info("\n=== Batch Operation Summary ===")
                    process_logger.info(f"Total projects processed: {total_projects}")
                    process_logger.info(f"Successfully created: {success_count}")
                    process_logger.info(f"Failed: {len(failed_projects)}")
                    if failed_projects:
                        process_logger.info("Failed projects:")
                        for project in failed_projects:
                            process_logger.info(f"  - {project}")
                
                elif action == 'd_p':
                    total_projects = len(project_names)
                    success_count = 0
                    failed_projects = []

                    process_logger.info(f"Starting batch deletion of {total_projects} projects...")
                    
                    for index, project_name in enumerate(project_names, 1):
                        process_logger.info(f"\nProcessing project {index}/{total_projects}: {project_name}")
                        if automation.delete_project(project_name):
                            success_count += 1
                        else:
                            failed_projects.append(project_name)
                    
                    # Summary report
                    process_logger.info("\n=== Batch Operation Summary ===")
                    process_logger.info(f"Total projects processed: {total_projects}")
                    process_logger.info(f"Successfully deleted: {success_count}")
                    process_logger.info(f"Failed: {len(failed_projects)}")
                    if failed_projects:
                        process_logger.info("Failed projects:")
                        for project in failed_projects:
                            process_logger.info(f"  - {project}")
                
                elif action == 'l_p':
                    # List all projects for the account
                    projects = automation.db["projects"]
                    if projects:
                        process_logger.info(f"\nProjects for account {account_id}:")
                        for project_id, data in projects.items():
                            project = data["project"]
                            api_key = data["api_key"]
                            process_logger.info(f"\nProject: {project['name']}")
                            process_logger.info(f"  ID: {project['id']}")
                            process_logger.info(f"  Created: {project['created_at']}")
                            process_logger.info(f"  API Key: {api_key['key']}")
                            process_logger.info(f"  API Key ID: {api_key['id']}")
                    else:
                        process_logger.info(f"No projects found for account {account_id}")
        finally:
            automation.close()
            
    except Exception as e:
        process_logger.error(f"Error processing account {account_id}: {str(e)}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='RevenueCat Project Management')
    parser.add_argument('--accounts', '-a', nargs='+', required=True,
                       help='Account identifier(s) (e.g., A1 A2)')
    parser.add_argument('--action', '-x', choices=['c_p', 'd_p', 'l_p'], required=True,
                       help='Action to perform (c_p: create project, d_p: delete project, l_p: list projects)')
    parser.add_argument('--projects', '-p', nargs='+', default=[],
                       help='Name(s) of the project(s)')
    parser.add_argument('--debug', '-d', action='store_true',
                       help='Enable debug logging for verbose HTTP request/response details')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging (same as --debug)')
    args = parser.parse_args()
    
    # Set log level based on arguments or environment variable
    if args.debug or args.verbose or os.getenv('LOG_LEVEL', '').upper() == 'DEBUG':
        logging.getLogger().setLevel(logging.DEBUG)
        # Enable urllib3 debug logging for HTTP details
        logging.getLogger("urllib3.connectionpool").setLevel(logging.DEBUG)
        logging.getLogger("requests.packages.urllib3").setLevel(logging.DEBUG)
        logger.info("🐛 Debug logging enabled - HTTP requests will be verbose")

    # Validate arguments
    if args.action in ['c_p', 'd_p'] and not args.projects:
        logger.error("Project names are required for create and delete operations")
        sys.exit(1)

    # Check for batch size limit
    if args.action == 'c_p' and len(args.projects) > MAX_PROJECTS_PER_BATCH:
        logger.warning(f"Too many projects requested ({len(args.projects)}). Limiting to {MAX_PROJECTS_PER_BATCH} projects.")
        args.projects = args.projects[:MAX_PROJECTS_PER_BATCH]

    # Limit concurrent accounts
    if len(args.accounts) > MAX_CONCURRENT_ACCOUNTS:
        logger.warning(f"Too many accounts requested ({len(args.accounts)}). Limiting to {MAX_CONCURRENT_ACCOUNTS} concurrent accounts.")
        args.accounts = args.accounts[:MAX_CONCURRENT_ACCOUNTS]

    # Create processes for each account
    processes = []
    for account_id in args.accounts:
        p = multiprocessing.Process(
            target=process_account,
            args=(account_id, args.action, args.projects)
        )
        processes.append(p)
        p.start()

    # Wait for all processes to complete
    for p in processes:
        p.join()

    logger.info("All account operations completed")

if __name__ == "__main__":
    main() 