#!/usr/bin/env python3
import os
import sys
import json
import logging
import smtplib
import imaplib
import email
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
JSON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "json")

class FastMailAutomation:
    def __init__(self):
        # FastMail SMTP settings
        self.smtp_server = "smtp.fastmail.com"
        self.smtp_port = 465
        
        # FastMail IMAP settings
        self.imap_server = "imap.fastmail.com"
        self.imap_port = 993
        
        # Load credentials from environment variables
        load_dotenv()
        self.email = os.getenv('FASTMAIL_EMAIL')
        self.password = os.getenv('FASTMAIL_APP_PASSWORD')
        
        if not self.email or not self.password:
            raise ValueError("Please set FASTMAIL_EMAIL and FASTMAIL_APP_PASSWORD environment variables")
        
        # Create JSON directory if it doesn't exist
        os.makedirs(JSON_DIR, exist_ok=True)

    def send_email(self, to_email, subject, body, is_html=False):
        """Send an email using FastMail SMTP and save to Sent folder via IMAP."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Date'] = email.utils.formatdate(localtime=True)
            msg['Message-ID'] = email.utils.make_msgid()
            
            # Attach body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            logger.info(f"Connecting to SMTP server: {self.smtp_server}")
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            # Login
            logger.info("Logging in to SMTP server...")
            server.login(self.email, self.password)
            
            # Send email
            logger.info(f"Sending email to: {to_email}")
            server.send_message(msg)
            server.quit()
            logger.info("Email sent via SMTP!")

            # Save to Sent folder via IMAP
            logger.info("Appending sent message to Sent folder via IMAP...")
            raw_msg = msg.as_bytes()
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email, self.password)
            mail.select('Sent')
            result = mail.append('Sent', '\Seen', imaplib.Time2Internaldate(time.time()), raw_msg)
            if result[0] == 'OK':
                logger.info("Email successfully appended to Sent folder!")
            else:
                logger.warning(f"Failed to append email to Sent folder: {result}")
            mail.close()
            mail.logout()

            return True
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    def check_emails(self, folder='INBOX', limit=10, unread_only=False):
        """Check emails using FastMail IMAP."""
        try:
            # Connect to IMAP server
            logger.info(f"Connecting to IMAP server: {self.imap_server}")
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            
            # Login
            logger.info("Logging in to IMAP server...")
            mail.login(self.email, self.password)
            
            # Select mailbox
            logger.info(f"Selecting mailbox: {folder}")
            mail.select(folder)
            
            # Search criteria
            search_criteria = '(UNSEEN)' if unread_only else 'ALL'
            logger.info(f"Searching with criteria: {search_criteria}")
            
            # Search for emails
            _, message_numbers = mail.search(None, search_criteria)
            
            # Get the latest emails
            email_list = []
            for num in message_numbers[0].split()[-limit:]:
                # Fetch email
                _, msg_data = mail.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Extract email details
                email_data = {
                    'subject': email_message['subject'],
                    'from': email_message['from'],
                    'date': email_message['date'],
                    'body': ''
                }
                
                # Get email body
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            email_data['body'] = part.get_payload(decode=True).decode()
                            break
                else:
                    email_data['body'] = email_message.get_payload(decode=True).decode()
                
                email_list.append(email_data)
            
            # Close connection
            mail.close()
            mail.logout()
            
            logger.info(f"Found {len(email_list)} emails")
            return email_list
            
        except Exception as e:
            logger.error(f"Error checking emails: {str(e)}")
            return None

    def save_emails_to_json(self, emails, filename=None):
        """Save emails to a JSON file in the json directory."""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"fastmail_emails_{timestamp}.json"
            
            # Ensure filename is in the json directory
            filepath = os.path.join(JSON_DIR, filename)
            
            with open(filepath, 'w') as f:
                json.dump(emails, f, indent=2)
            
            logger.info(f"Emails saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving emails to JSON: {str(e)}")
            return None

    def check_sent_emails(self, limit=10):
        """Check emails in the Sent folder."""
        return self.check_emails(folder='Sent', limit=limit, unread_only=False)

    def list_folders(self):
        """List all available folders."""
        try:
            # Connect to IMAP server
            logger.info(f"Connecting to IMAP server: {self.imap_server}")
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            
            # Login
            logger.info("Logging in to IMAP server...")
            mail.login(self.email, self.password)
            
            # List all folders
            logger.info("Listing all folders...")
            _, folders = mail.list()
            
            # Close connection
            mail.logout()
            
            # Print folders
            logger.info("\nAvailable folders:")
            for folder in folders:
                logger.info(folder.decode())
            
            return folders
            
        except Exception as e:
            logger.error(f"Error listing folders: {str(e)}")
            return None

    def read_emails(self, folder='INBOX', sender=None, subject=None, date_range=None, limit=10):
        """Read emails from a specified folder with optional filtering."""
        try:
            # Connect to IMAP server
            logger.info(f"Connecting to IMAP server: {self.imap_server}")
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            
            # Login
            logger.info("Logging in to IMAP server...")
            mail.login(self.email, self.password)
            
            # Select mailbox
            logger.info(f"Selecting mailbox: {folder}")
            mail.select(folder)
            
            # Build search criteria
            search_criteria = []
            if sender:
                search_criteria.append(f'(FROM "{sender}")')
            if subject:
                search_criteria.append(f'(SUBJECT "{subject}")')
            if date_range:
                start_date, end_date = date_range
                search_criteria.append(f'(SINCE "{start_date}" BEFORE "{end_date}")')
            if not search_criteria:
                search_criteria.append('ALL')
            
            search_string = ' '.join(search_criteria)
            logger.info(f"Searching with criteria: {search_string}")
            
            # Search for emails
            _, message_numbers = mail.search(None, search_string)
            
            # Get the latest emails
            email_list = []
            for num in message_numbers[0].split()[-limit:]:
                # Fetch email
                _, msg_data = mail.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Extract email details
                email_data = {
                    'subject': email_message['subject'],
                    'from': email_message['from'],
                    'date': email_message['date'],
                    'body': ''
                }
                
                # Get email body
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            email_data['body'] = part.get_payload(decode=True).decode()
                            break
                else:
                    email_data['body'] = email_message.get_payload(decode=True).decode()
                
                email_list.append(email_data)
            
            # Close connection
            mail.close()
            mail.logout()
            
            logger.info(f"Found {len(email_list)} emails")
            return email_list
            
        except Exception as e:
            logger.error(f"Error reading emails: {str(e)}")
            return None

def main():
    parser = argparse.ArgumentParser(description='FastMail Automation Tool')
    parser.add_argument('--action', '-a', choices=['send', 'read', 'list', 'check'], required=True,
                      help='Action to perform: send, read, list, or check emails')
    parser.add_argument('--to', '-t', help='Recipient email address (for send action)')
    parser.add_argument('--subject', '-s', help='Email subject (for send action)')
    parser.add_argument('--body', '-b', help='Email body (for send action)')
    parser.add_argument('--folder', '-f', default='INBOX',
                      help='Folder to read/check (default: INBOX)')
    parser.add_argument('--limit', '-l', type=int, default=10,
                      help='Number of emails to retrieve (default: 10)')
    parser.add_argument('--unread', '-u', action='store_true',
                      help='Only show unread emails')
    parser.add_argument('--sender', help='Filter by sender email')
    parser.add_argument('--date-range', nargs=2, help='Filter by date range (format: "DD-MMM-YYYY")')
    
    args = parser.parse_args()
    
    try:
        # Initialize FastMail automation
        fastmail = FastMailAutomation()
        
        if args.action == 'list':
            fastmail.list_folders()
            
        elif args.action == 'send':
            if not all([args.to, args.subject, args.body]):
                logger.error("--to, --subject, and --body are required for send action")
                sys.exit(1)
            if fastmail.send_email(args.to, args.subject, args.body):
                logger.info("Email sent successfully!")
                
        elif args.action == 'read':
            date_range = tuple(args.date_range) if args.date_range else None
            emails = fastmail.read_emails(
                folder=args.folder,
                sender=args.sender,
                subject=None,
                date_range=date_range,
                limit=args.limit
            )
            if emails:
                logger.info(f"Found {len(emails)} emails")
                fastmail.save_emails_to_json(emails, f"read_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            else:
                logger.info("No emails found")
                
        elif args.action == 'check':
            emails = fastmail.check_emails(
                folder=args.folder,
                limit=args.limit,
                unread_only=args.unread
            )
            if emails:
                logger.info(f"Found {len(emails)} emails")
                fastmail.save_emails_to_json(emails, f"check_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            else:
                logger.info("No emails found")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 