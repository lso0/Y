# RevenueCat Automation Script

This script automates the process of logging into RevenueCat and creating new projects using Selenium WebDriver.

## Prerequisites

- Python 3.7 or higher
- Chrome browser installed
- pip (Python package manager)

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root directory with your RevenueCat credentials:
```
REVENUECAT_EMAIL=your.email@example.com
REVENUECAT_PASSWORD=your_password
```

## Usage

Run the script:
```bash
python revenuecat_automation.py
```

The script will:
1. Launch a Chrome browser
2. Log in to RevenueCat using your credentials
3. Navigate to the Projects section
4. Create a new project named "TestProject"

## Features

- Automated login to RevenueCat
- Project creation automation
- Detailed logging
- Error handling
- Environment variable support for credentials

## Notes

- The script uses Chrome WebDriver, which is automatically downloaded and managed by webdriver-manager
- By default, the browser runs in visible mode. To run in headless mode, uncomment the headless option in the script
- The script includes proper wait conditions to handle dynamic loading of elements
- All actions are logged for debugging purposes 

## Usage

python3 rc_a.py -a 1 2 -p "Project1" "Project2" -x c_p

<3>
hello