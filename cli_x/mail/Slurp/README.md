# MailSlurp Inbox Creator

A JavaScript script to create and manage MailSlurp email inboxes using the MailSlurp API.

## 🚀 Quick Start

### 1. Set up your API Key

1. Get your MailSlurp API key from [https://app.mailslurp.com/](https://app.mailslurp.com/)
2. Edit the `.env` file and replace `your_mailslurp_api_key_here` with your actual API key:

```env
API_KEY=sk_your_actual_api_key_here
```

### 2. Install Dependencies

The dependencies should already be installed, but if needed:

```bash
npm install
```

### 3. Create Your First Inbox

```bash
node createInbox.js create "My First Inbox" "Description for my inbox"
```

## 📋 Available Commands

### Create a Basic Inbox
```bash
node createInbox.js create [name] [description]
```

**Examples:**
```bash
node createInbox.js create "Test Inbox" "For testing purposes"
node createInbox.js create "Marketing Emails"
```

### Create Multiple Inboxes
```bash
node createInbox.js create-multiple [count] [basename]
```

**Examples:**
```bash
node createInbox.js create-multiple 5 "Batch-Test"
node createInbox.js create-multiple 3 "Load-Test"
```

### Create Temporary Inbox (expires in 1 hour)
```bash
node createInbox.js create-temp
```

### Create Virtual Inbox (for testing - doesn't send emails)
```bash
node createInbox.js create-virtual
```

### List All Inboxes
```bash
node createInbox.js list
```

### Get Inbox Details
```bash
node createInbox.js details [inboxId]
```

**Example:**
```bash
node createInbox.js details 12345678-1234-1234-1234-123456789012
```

### Delete an Inbox
```bash
node createInbox.js delete [inboxId]
```

**Example:**
```bash
node createInbox.js delete 12345678-1234-1234-1234-123456789012
```

### Show Help
```bash
node createInbox.js
```

## 📦 NPM Scripts

You can also use the predefined npm scripts:

```bash
npm run create          # Create a basic inbox
npm run list           # List all inboxes
npm run create-temp    # Create temporary inbox
npm run create-virtual # Create virtual inbox
npm run help           # Show help
```

## 🔧 Advanced Usage

### Using as a Module

You can also import and use the functions in your own JavaScript code:

```javascript
const { createInbox, listInboxes, createMultipleInboxes } = require('./createInbox');

async function myFunction() {
    // Create a custom inbox
    const inbox = await createInbox({
        name: 'My Custom Inbox',
        description: 'Created programmatically',
        useShortAddress: true,
        virtual: false
    });
    
    console.log('Created inbox:', inbox.emailAddress);
    
    // List all inboxes
    const allInboxes = await listInboxes();
    
    // Create multiple inboxes
    const batchInboxes = await createMultipleInboxes(3, {
        name: 'Batch',
        description: 'Batch created inboxes'
    });
}
```

### Inbox Creation Options

When creating inboxes, you can use these options:

```javascript
const options = {
    name: 'My Inbox',                    // Name for the inbox
    description: 'Inbox description',    // Description
    useShortAddress: true,               // Use shorter email address
    inboxType: 'HTTP_INBOX',            // 'HTTP_INBOX' or 'SMTP_INBOX'
    virtual: false,                      // Create virtual inbox (testing)
    expiresIn: 3600000,                 // Expire in 1 hour (milliseconds)
    allowTeamAccess: false              // Allow team access
};
```

## 📧 What You Get

When you create an inbox, you'll receive:

- **Email Address**: A real email address (e.g., `abc123@mailslurp.com`)
- **Inbox ID**: Unique identifier for the inbox
- **Name & Description**: Custom metadata
- **Type**: HTTP or SMTP inbox
- **Expiry**: If set, when the inbox will be deleted

## 🔐 Security Notes

- Keep your API key secure and never commit it to version control
- The `.env` file is included in `.gitignore` (if you create one)
- MailSlurp inboxes are temporary by nature - perfect for testing

## 🆘 Troubleshooting

### Common Issues

1. **API Key Error**: Make sure your API key is correctly set in the `.env` file
2. **Network Error**: Check your internet connection
3. **Rate Limits**: MailSlurp has rate limits - the script includes delays between batch operations

### Error Messages

- `❌ Please set your MailSlurp API key`: Update your `.env` file with the correct API key
- `❌ Error creating inbox: Unauthorized`: Check your API key is valid
- `💡 Note: Custom domains need to be verified first`: For custom domains, verify them in MailSlurp dashboard first

## 📚 MailSlurp Resources

- [MailSlurp Dashboard](https://app.mailslurp.com/)
- [MailSlurp Documentation](https://docs.mailslurp.com/)
- [MailSlurp API Reference](https://docs.mailslurp.com/api/)

## 🎯 Use Cases

Perfect for:
- **Email Testing**: Test email functionality in your applications
- **Temporary Emails**: Create disposable email addresses
- **Load Testing**: Create multiple inboxes for testing
- **Development**: Avoid using real email addresses during development
- **Automation**: Integrate with CI/CD pipelines for email testing

## 📝 Example Output

```
🔄 Creating new inbox...
✅ Inbox created successfully!
📧 Email Address: 1a2b3c4d@mailslurp.com
🆔 Inbox ID: 12345678-1234-1234-1234-123456789012
📝 Name: My Test Inbox
📋 Description: For testing emails
🔗 Type: HTTP_INBOX
```

Happy email testing! 🎉 