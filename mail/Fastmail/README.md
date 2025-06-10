# FastMail Automation

This script provides automation for sending and checking emails using FastMail's SMTP and IMAP servers.

## Prerequisites

1. A FastMail account
2. Python 3.6 or higher
3. App Password from FastMail

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the same directory with your FastMail credentials:
```
FASTMAIL_EMAIL=your.email@fastmail.com
FASTMAIL_APP_PASSWORD=your_app_password
```

To get your App Password:
1. Log in to your FastMail account
2. Go to Settings → Password & Security
3. Under "App Passwords", click "New App Password"
4. Give it a name (e.g., "Python Script")
5. Save the generated password

## Usage

The script provides the following functionality:

1. Sending emails:
```python
fastmail = FastMailAutomation()
fastmail.send_email(
    to_email="recipient@example.com",
    subject="Test Email",
    body="Hello, this is a test email!"
)
```

2. Checking emails:
```python
# Get last 5 unread emails
emails = fastmail.check_emails(limit=5, unread_only=True)

# Get all emails from a specific folder
emails = fastmail.check_emails(folder='Sent', limit=10, unread_only=False)
```

3. Saving emails to JSON:
```python
fastmail.save_emails_to_json(emails)
```

## Features

- Send plain text or HTML emails
- Check emails from any folder
- Filter for unread emails
- Save email data to JSON files
- Detailed logging
- Error handling and cleanup

## Security Notes

- Never commit your `.env` file to version control
- Use App Passwords instead of your main account password
- Keep your credentials secure 