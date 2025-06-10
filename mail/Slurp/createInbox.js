const axios = require('axios');
require('dotenv').config();

// MailSlurp API configuration
const API_KEY = process.env.API_KEY;
const BASE_URL = 'https://api.mailslurp.com';

if (!API_KEY || API_KEY === 'your_mailslurp_api_key_here') {
    console.error('❌ Please set your MailSlurp API key in the .env file');
    console.error('Get your API key from: https://app.mailslurp.com/');
    process.exit(1);
}

// Axios instance with default configuration
const mailslurp = axios.create({
    baseURL: BASE_URL,
    headers: {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
});

/**
 * Create a new MailSlurp inbox
 * @param {Object} options - Inbox creation options
 * @param {string} options.name - Name for the inbox
 * @param {string} options.description - Description for the inbox
 * @param {boolean} options.useShortAddress - Use shorter email address
 * @param {number} options.expiresIn - Expiry time in milliseconds
 * @param {string} options.inboxType - Type of inbox ('HTTP_INBOX' or 'SMTP_INBOX')
 * @param {boolean} options.virtual - Create virtual inbox (won't send emails)
 * @returns {Object} Created inbox details
 */
async function createInbox(options = {}) {
    try {
        const inboxData = {
            name: options.name || `Inbox-${Date.now()}`,
            description: options.description || 'Created with MailSlurp API',
            useShortAddress: options.useShortAddress || false,
            inboxType: options.inboxType || 'HTTP_INBOX',
            virtual: options.virtual || false,
            allowTeamAccess: options.allowTeamAccess || false,
            ...options
        };

        // Remove undefined values
        Object.keys(inboxData).forEach(key => 
            inboxData[key] === undefined && delete inboxData[key]
        );

        console.log('🔄 Creating new inbox...');
        
        const response = await mailslurp.post('/inboxes', inboxData);
        const inbox = response.data;

        console.log('✅ Inbox created successfully!');
        console.log('📧 Email Address:', inbox.emailAddress);
        console.log('🆔 Inbox ID:', inbox.id);
        console.log('📝 Name:', inbox.name);
        console.log('📋 Description:', inbox.description);
        console.log('🔗 Type:', inbox.inboxType);
        
        if (inbox.expiresAt) {
            console.log('⏰ Expires At:', new Date(inbox.expiresAt).toLocaleString());
        }

        return inbox;
    } catch (error) {
        console.error('❌ Error creating inbox:', error.response?.data || error.message);
        throw error;
    }
}

/**
 * List all inboxes in the account
 */
async function listInboxes() {
    try {
        console.log('📋 Fetching all inboxes...');
        
        const response = await mailslurp.get('/inboxes');
        const inboxes = response.data.content;

        if (inboxes.length === 0) {
            console.log('📭 No inboxes found');
            return [];
        }

        console.log(`📬 Found ${inboxes.length} inbox(es):`);
        inboxes.forEach((inbox, index) => {
            console.log(`${index + 1}. ${inbox.emailAddress} (${inbox.name})`);
        });

        return inboxes;
    } catch (error) {
        console.error('❌ Error listing inboxes:', error.response?.data || error.message);
        throw error;
    }
}

/**
 * Create multiple inboxes
 * @param {number} count - Number of inboxes to create
 * @param {Object} baseOptions - Base options for all inboxes
 */
async function createMultipleInboxes(count = 1, baseOptions = {}) {
    const inboxes = [];
    
    console.log(`🔄 Creating ${count} inbox(es)...`);
    
    for (let i = 0; i < count; i++) {
        try {
            const options = {
                ...baseOptions,
                name: `${baseOptions.name || 'Inbox'}-${i + 1}-${Date.now()}`
            };
            
            const inbox = await createInbox(options);
            inboxes.push(inbox);
            
            // Small delay between creations
            if (i < count - 1) {
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        } catch (error) {
            console.error(`❌ Failed to create inbox ${i + 1}:`, error.message);
        }
    }
    
    return inboxes;
}

/**
 * Create inbox with custom domain (requires domain verification)
 * @param {string} localPart - Local part of email (before @)
 * @param {string} domain - Custom domain
 */
async function createCustomDomainInbox(localPart, domain) {
    try {
        const response = await mailslurp.post('/inboxes', {
            name: `Custom-${localPart}@${domain}`,
            description: `Custom domain inbox for ${localPart}@${domain}`,
            domainName: domain,
            localPart: localPart
        });

        return response.data;
    } catch (error) {
        console.error('❌ Error creating custom domain inbox:', error.response?.data || error.message);
        console.log('💡 Note: Custom domains need to be verified first in your MailSlurp dashboard');
        throw error;
    }
}

/**
 * Get inbox details by ID
 * @param {string} inboxId - Inbox ID to fetch
 */
async function getInboxDetails(inboxId) {
    try {
        const response = await mailslurp.get(`/inboxes/${inboxId}`);
        return response.data;
    } catch (error) {
        console.error('❌ Error fetching inbox details:', error.response?.data || error.message);
        throw error;
    }
}

/**
 * Delete inbox by ID
 * @param {string} inboxId - Inbox ID to delete
 */
async function deleteInbox(inboxId) {
    try {
        await mailslurp.delete(`/inboxes/${inboxId}`);
        console.log('✅ Inbox deleted successfully');
    } catch (error) {
        console.error('❌ Error deleting inbox:', error.response?.data || error.message);
        throw error;
    }
}

// Command line interface
async function main() {
    const args = process.argv.slice(2);
    const command = args[0];

    try {
        switch (command) {
            case 'create':
                const name = args[1] || `Inbox-${Date.now()}`;
                const description = args[2] || 'Created via CLI';
                await createInbox({ name, description });
                break;

            case 'create-multiple':
                const count = parseInt(args[1]) || 1;
                const baseName = args[2] || 'Batch-Inbox';
                await createMultipleInboxes(count, { name: baseName });
                break;

            case 'create-temp':
                // Create temporary inbox that expires in 1 hour
                await createInbox({
                    name: 'Temporary-Inbox',
                    description: 'Temporary inbox - expires in 1 hour',
                    expiresIn: 60 * 60 * 1000 // 1 hour in milliseconds
                });
                break;

            case 'create-virtual':
                // Create virtual inbox (doesn't send emails)
                await createInbox({
                    name: 'Virtual-Inbox',
                    description: 'Virtual inbox for testing',
                    virtual: true
                });
                break;

            case 'list':
                await listInboxes();
                break;

            case 'details':
                const inboxId = args[1];
                if (!inboxId) {
                    console.error('❌ Please provide inbox ID');
                    break;
                }
                const details = await getInboxDetails(inboxId);
                console.log('📧 Inbox Details:', JSON.stringify(details, null, 2));
                break;

            case 'delete':
                const deleteId = args[1];
                if (!deleteId) {
                    console.error('❌ Please provide inbox ID to delete');
                    break;
                }
                await deleteInbox(deleteId);
                break;

            default:
                console.log(`
🔧 MailSlurp Inbox Creator

Usage:
  node createInbox.js create [name] [description]          - Create a new inbox
  node createInbox.js create-multiple [count] [basename]   - Create multiple inboxes
  node createInbox.js create-temp                          - Create temporary inbox (1 hour)
  node createInbox.js create-virtual                       - Create virtual inbox
  node createInbox.js list                                 - List all inboxes
  node createInbox.js details [inboxId]                    - Get inbox details
  node createInbox.js delete [inboxId]                     - Delete an inbox

Examples:
  node createInbox.js create "My Test Inbox" "For testing emails"
  node createInbox.js create-multiple 5 "Batch-Test"
  node createInbox.js list
                `);
        }
    } catch (error) {
        console.error('💥 Script failed:', error.message);
        process.exit(1);
    }
}

// Export functions for use as a module
module.exports = {
    createInbox,
    listInboxes,
    createMultipleInboxes,
    createCustomDomainInbox,
    getInboxDetails,
    deleteInbox
};

// Run main function if script is executed directly
if (require.main === module) {
    main();
} 