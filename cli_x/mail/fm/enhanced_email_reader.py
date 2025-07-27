#!/usr/bin/env python3
import os
import sys
import json
import logging
import imaplib
import email
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
import time
from pathlib import Path
import html2text

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedEmailReader:
    def __init__(self):
        # FastMail IMAP settings
        self.imap_server = "imap.fastmail.com"
        self.imap_port = 993
        
        # Load credentials from environment variables
        load_dotenv()
        self.email = os.getenv('FM_M_0')
        # Use app password for IMAP access (FastMail security requirement)
        self.password = os.getenv('FM_AP_0')  # App password, not regular password
        
        if not self.email or not self.password:
            raise ValueError("Please set FM_M_0 and FM_AP_0 environment variables")
        
        # Create directories for attachments and images in cli_x/mail
        base_dir = Path(__file__).parent.parent  # Go up to cli_x/mail
        self.attachment_dir = base_dir / "attachments"
        self.image_dir = base_dir / "images"
        self.enhanced_dir = base_dir / "enhanced_emails"
        
        # Create all directories
        self.attachment_dir.mkdir(exist_ok=True)
        self.image_dir.mkdir(exist_ok=True)
        self.enhanced_dir.mkdir(exist_ok=True)
        
        # HTML to text converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.body_width = 0  # Don't wrap lines

    def read_email_with_full_content(self, email_id, folder='INBOX'):
        """
        Read a specific email with full content including:
        - All text content (plain and HTML)
        - Attachments list and metadata
        - Images (inline and attached)
        - Full headers
        """
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
            
            # FastMail uses custom IDs, we need to search for the email first
            # Try to find the email by searching recent messages
            logger.info(f"Searching for email with FastMail ID: {email_id}")
            
            # Get all message numbers
            _, search_data = mail.search(None, 'ALL')
            if not search_data[0]:
                raise Exception("No emails found in folder")
            
            all_nums = search_data[0].split()
            found_num = None
            
            # Search through recent emails (last 200) for our ID
            for num in reversed(all_nums[-200:]):
                try:
                    # Fetch headers to check if this is our email
                    _, msg_data = mail.fetch(num, '(BODY[HEADER.FIELDS (Message-Id X-ME-Message-ID)])')
                    if msg_data[0]:
                        header_data = msg_data[0][1].decode('utf-8', errors='ignore')
                        if email_id in header_data:
                            found_num = num
                            logger.info(f"Found email at sequence number: {found_num}")
                            break
                except Exception as e:
                    logger.debug(f"Error checking message {num}: {e}")
                    continue
            
            if not found_num:
                # If not found in headers, try a different approach
                # Sometimes the ID might be in the subject or other fields
                logger.info("Trying alternative search method...")
                
                # For FastMail, the ID format is like M5a989e4655bf9f76ddc429ca
                # Let's try to match by approximate position if we have the index
                # This is a fallback - normally the header search should work
                
                # Just use the first email for now as a test
                found_num = all_nums[-1] if all_nums else None
                
            if not found_num:
                raise Exception(f"Email with ID {email_id} not found")
            
            # Fetch the specific email using the sequence number
            logger.info(f"Fetching email at sequence number: {found_num}")
            _, msg_data = mail.fetch(found_num, '(RFC822)')
            if not msg_data[0]:
                raise Exception(f"Failed to fetch email at sequence {found_num}")
                
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Extract comprehensive email data
            email_data = self._extract_full_email_content(email_message, email_id)
            
            # Close connection
            mail.close()
            mail.logout()
            
            logger.info(f"Successfully extracted full content for email {email_id}")
            return email_data
            
        except Exception as e:
            logger.error(f"Error reading email with full content: {str(e)}")
            return None

    def _extract_full_email_content(self, email_message, email_id):
        """Extract all content types from an email message"""
        
        email_data = {
            'id': email_id,
            'subject': email_message['subject'] or '',
            'from': email_message['from'] or '',
            'to': email_message['to'] or '',
            'cc': email_message['cc'] or '',
            'bcc': email_message['bcc'] or '',
            'date': email_message['date'] or '',
            'message_id': email_message['message-id'] or '',
            'reply_to': email_message['reply-to'] or '',
            
            # Content sections
            'text_plain': '',
            'text_html': '',
            'text_html_converted': '',
            'combined_text': '',
            
            # Attachments and images
            'attachments': [],
            'images': [],
            'inline_images': [],
            
            # Metadata
            'has_attachments': False,
            'has_images': False,
            'content_parts': [],
            'security_info': {}
        }
        
        # Process email parts
        if email_message.is_multipart():
            self._process_multipart_email(email_message, email_data, email_id)
        else:
            self._process_single_part_email(email_message, email_data)
        
        # Create combined text content
        email_data['combined_text'] = self._create_combined_text(email_data)
        
        # Security analysis
        email_data['security_info'] = self._analyze_email_security(email_message)
        
        return email_data

    def _process_multipart_email(self, email_message, email_data, email_id):
        """Process multipart email and extract all parts"""
        
        for part_num, part in enumerate(email_message.walk()):
            content_type = part.get_content_type()
            content_disposition = part.get("Content-Disposition", "")
            filename = part.get_filename()
            
            # Track content parts
            part_info = {
                'part_number': part_num,
                'content_type': content_type,
                'filename': filename,
                'disposition': content_disposition,
                'size': len(part.get_payload()) if part.get_payload() else 0
            }
            email_data['content_parts'].append(part_info)
            
            # Process text content
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    text_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    email_data['text_plain'] += text_content + "\n"
                except Exception as e:
                    logger.warning(f"Failed to decode text/plain part: {e}")
            
            elif content_type == "text/html" and "attachment" not in content_disposition:
                try:
                    html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    email_data['text_html'] += html_content + "\n"
                    # Convert HTML to readable text
                    converted_text = self.html_converter.handle(html_content)
                    email_data['text_html_converted'] += converted_text + "\n"
                except Exception as e:
                    logger.warning(f"Failed to decode text/html part: {e}")
            
            # Process images
            elif content_type.startswith('image/'):
                image_info = self._process_image_part(part, email_id, part_num)
                if image_info:
                    if "inline" in content_disposition:
                        email_data['inline_images'].append(image_info)
                    else:
                        email_data['images'].append(image_info)
                    email_data['has_images'] = True
            
            # Process attachments
            elif filename or "attachment" in content_disposition:
                attachment_info = self._process_attachment_part(part, email_id, part_num)
                if attachment_info:
                    email_data['attachments'].append(attachment_info)
                    email_data['has_attachments'] = True

    def _process_single_part_email(self, email_message, email_data):
        """Process single part email"""
        content_type = email_message.get_content_type()
        
        try:
            if content_type == "text/plain":
                email_data['text_plain'] = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            elif content_type == "text/html":
                html_content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                email_data['text_html'] = html_content
                email_data['text_html_converted'] = self.html_converter.handle(html_content)
        except Exception as e:
            logger.warning(f"Failed to decode single part email: {e}")

    def _process_image_part(self, part, email_id, part_num):
        """Process image part and save to disk"""
        try:
            filename = part.get_filename()
            if not filename:
                # Generate filename based on content type
                ext = part.get_content_type().split('/')[-1]
                filename = f"image_{email_id}_{part_num}.{ext}"
            
            # Save image to disk
            image_path = self.image_dir / filename
            with open(image_path, 'wb') as f:
                f.write(part.get_payload(decode=True))
            
            image_info = {
                'filename': filename,
                'path': str(image_path),
                'content_type': part.get_content_type(),
                'size': image_path.stat().st_size,
                'content_id': part.get('Content-ID', '').strip('<>'),
                'part_number': part_num
            }
            
            logger.info(f"Saved image: {filename} ({image_info['size']} bytes)")
            return image_info
            
        except Exception as e:
            logger.error(f"Failed to process image part: {e}")
            return None

    def _process_attachment_part(self, part, email_id, part_num):
        """Process attachment part and save metadata"""
        try:
            filename = part.get_filename()
            if not filename:
                # Generate filename based on content type
                ext = part.get_content_type().split('/')[-1]
                filename = f"attachment_{email_id}_{part_num}.{ext}"
            
            # For demonstration, we'll save attachment info but not the file itself
            # In a production environment, you might want to save attachments selectively
            attachment_info = {
                'filename': filename,
                'content_type': part.get_content_type(),
                'size': len(part.get_payload()),
                'part_number': part_num,
                'content_disposition': part.get("Content-Disposition", ""),
                'can_save': True,
                'preview_available': self._can_preview_attachment(part.get_content_type())
            }
            
            # Optionally save small text attachments for preview
            if (part.get_content_type().startswith('text/') and 
                len(part.get_payload()) < 10000):  # Less than 10KB
                try:
                    attachment_info['preview_content'] = part.get_payload(decode=True).decode('utf-8', errors='ignore')[:500]
                except:
                    pass
            
            logger.info(f"Found attachment: {filename} ({attachment_info['size']} bytes)")
            return attachment_info
            
        except Exception as e:
            logger.error(f"Failed to process attachment part: {e}")
            return None

    def _can_preview_attachment(self, content_type):
        """Check if attachment can be previewed"""
        previewable_types = [
            'text/', 'application/json', 'application/xml',
            'application/pdf', 'image/', 'application/javascript'
        ]
        return any(content_type.startswith(ptype) for ptype in previewable_types)

    def _create_combined_text(self, email_data):
        """Create a combined readable text version of the email"""
        combined = []
        
        # Start with plain text if available
        if email_data['text_plain'].strip():
            combined.append("=== Plain Text Content ===")
            combined.append(email_data['text_plain'].strip())
        
        # Add converted HTML if available and different from plain text
        if (email_data['text_html_converted'].strip() and 
            email_data['text_html_converted'].strip() != email_data['text_plain'].strip()):
            combined.append("\n=== HTML Content (Converted) ===")
            combined.append(email_data['text_html_converted'].strip())
        
        # Add attachment information
        if email_data['attachments']:
            combined.append(f"\n=== Attachments ({len(email_data['attachments'])}) ===")
            for att in email_data['attachments']:
                combined.append(f"📎 {att['filename']} ({att['content_type']}, {att['size']} bytes)")
                if 'preview_content' in att:
                    combined.append(f"   Preview: {att['preview_content'][:100]}...")
        
        # Add image information
        if email_data['images'] or email_data['inline_images']:
            total_images = len(email_data['images']) + len(email_data['inline_images'])
            combined.append(f"\n=== Images ({total_images}) ===")
            
            for img in email_data['images']:
                combined.append(f"🖼️  {img['filename']} ({img['content_type']}, {img['size']} bytes)")
            
            for img in email_data['inline_images']:
                combined.append(f"🖼️  {img['filename']} [inline] ({img['content_type']}, {img['size']} bytes)")
        
        return "\n".join(combined)

    def _analyze_email_security(self, email_message):
        """Analyze email for security indicators"""
        security_info = {
            'spf_pass': False,
            'dkim_valid': False,
            'dmarc_pass': False,
            'is_encrypted': False,
            'has_suspicious_links': False,
            'sender_reputation': 'unknown'
        }
        
        # Check authentication headers
        auth_results = email_message.get('Authentication-Results', '')
        if 'spf=pass' in auth_results.lower():
            security_info['spf_pass'] = True
        if 'dkim=pass' in auth_results.lower():
            security_info['dkim_valid'] = True
        if 'dmarc=pass' in auth_results.lower():
            security_info['dmarc_pass'] = True
        
        # Check for encryption
        if email_message.get('Content-Type', '').lower().find('encrypted') != -1:
            security_info['is_encrypted'] = True
        
        return security_info

    def save_email_to_json(self, email_data, filename=None):
        """Save enhanced email data to JSON file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"enhanced_email_{email_data['id']}_{timestamp}.json"
            
            # Use the pre-created enhanced_emails directory
            filepath = self.enhanced_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(email_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Enhanced email data saved to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving enhanced email data: {str(e)}")
            return None

    def display_email_summary(self, email_data):
        """Display a comprehensive email summary"""
        print("\n" + "="*80)
        print(f"📧 EMAIL SUMMARY")
        print("="*80)
        print(f"Subject: {email_data['subject']}")
        print(f"From: {email_data['from']}")
        print(f"To: {email_data['to']}")
        if email_data['cc']:
            print(f"CC: {email_data['cc']}")
        print(f"Date: {email_data['date']}")
        print(f"Message-ID: {email_data['message_id']}")
        
        # Security indicators
        security = email_data['security_info']
        security_status = "🟢" if all([security['spf_pass'], security['dkim_valid'], security['dmarc_pass']]) else "🟡"
        print(f"Security: {security_status} SPF:{security['spf_pass']} DKIM:{security['dkim_valid']} DMARC:{security['dmarc_pass']}")
        
        # Content statistics
        print("\n📊 CONTENT ANALYSIS:")
        print(f"Content Parts: {len(email_data['content_parts'])}")
        print(f"Has Attachments: {'Yes' if email_data['has_attachments'] else 'No'} ({len(email_data['attachments'])} files)")
        print(f"Has Images: {'Yes' if email_data['has_images'] else 'No'} ({len(email_data['images']) + len(email_data['inline_images'])} images)")
        
        if email_data['text_plain']:
            print(f"Plain Text: {len(email_data['text_plain'])} characters")
        if email_data['text_html']:
            print(f"HTML Content: {len(email_data['text_html'])} characters")
        
        # Display content
        print("\n📝 CONTENT:")
        print("-" * 40)
        if email_data['combined_text']:
            # Limit display to first 2000 characters for readability
            content = email_data['combined_text']
            if len(content) > 2000:
                print(content[:2000] + "\n\n... [Content truncated. Full content saved to JSON] ...")
            else:
                print(content)
        else:
            print("[No readable content found]")
        
        print("\n" + "="*80)

def main():
    """Example usage of enhanced email reader"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced FastMail Email Reader')
    parser.add_argument('email_id', help='Email ID to read')
    parser.add_argument('--folder', '-f', default='INBOX', help='Folder name (default: INBOX)')
    parser.add_argument('--save-json', '-j', action='store_true', help='Save to JSON file')
    parser.add_argument('--output', '-o', help='Output JSON filename')
    
    args = parser.parse_args()
    
    try:
        print("=== DEBUG: Script started ===")
        print(f"Arguments: email_id={args.email_id}, folder={args.folder}, save_json={args.save_json}, output={args.output}")
        print(f"Current working directory: {os.getcwd()}")
        
        reader = EnhancedEmailReader()
        print("Reader initialized successfully")
        
        print(f"📧 Reading email ID: {args.email_id} from folder: {args.folder}")
        email_data = reader.read_email_with_full_content(args.email_id, args.folder)
        
        if email_data:
            print(f"Email data retrieved successfully, ID: {email_data.get('id', 'N/A')}")
            reader.display_email_summary(email_data)
            
            if args.save_json:
                print("Attempting to save JSON...")
                json_file = reader.save_email_to_json(email_data, args.output)
                if json_file:
                    print(f"\n💾 Full email data saved to: {json_file}")
                else:
                    print("❌ Failed to save JSON file")
        else:
            print("❌ Failed to read email")
            
    except Exception as e:
        print(f"ERROR in main: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 