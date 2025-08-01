# Data Folder Encryption

This system encrypts your sensitive `cli_x/data` folder using YubiKey + passphrase authentication, ensuring that sensitive financial data, email configurations, and other private information are protected.

## Security Method

- **Two-Factor Authentication**: YubiKey challenge-response + user passphrase
- **Encryption**: AES-256-CBC with PBKDF2 key derivation (100,000 iterations)
- **Storage**: Encrypted data stored in `scripts/enc/encrypted_tokens.json`

## Quick Start

### Check Status
```bash
./scripts/encrypt-data-folder.sh --status
```

### Encrypt Data Folder
```bash
./scripts/encrypt-data-folder.sh --encrypt
```

This will:
1. Create a compressed archive of your `cli_x/data` folder
2. Encrypt it using your YubiKey + passphrase
3. Store the encrypted data in `encrypted_tokens.json`
4. Move the original folder to `cli_x/data_unencrypted_backup`
5. Update `.gitignore` to exclude the data folder from version control

### Decrypt Data Folder
```bash
./scripts/encrypt-data-folder.sh --decrypt
```

This will restore the `cli_x/data` folder to its original location.

### Decrypt to Specific Location
```bash
./scripts/encrypt-data-folder.sh --decrypt-to /path/to/location
```

## Security Warnings

⚠️ **IMPORTANT SAFETY NOTES:**

1. **Test Decryption**: Always test decryption before deleting the backup folder
2. **YubiKey Requirement**: You need your YubiKey plugged in for both encryption and decryption
3. **Passphrase**: Remember your passphrase - it cannot be recovered
4. **Backup Safety**: The `*_unencrypted_backup` folder contains your original data - delete it only after verifying decryption works

## What Gets Encrypted

The entire `cli_x/data` folder including:
- `finance.yaml` - Financial service data and bank information
- `fastmail.yaml` - Email configuration
- `emails/` - Email storage (inbox, sent, trash, spam, deleted)
- `settings/` - Application settings
- `aliases/` - Email aliases
- Any other files in the data directory

## Manual Commands

You can also use the Python script directly:

```bash
# Check status
python3 scripts/enc/yubikey_token_manager.py --check-data-status

# Encrypt data folder
python3 scripts/enc/yubikey_token_manager.py --encrypt-data cli_x/data

# Decrypt data folder
python3 scripts/enc/yubikey_token_manager.py --decrypt-data

# Decrypt to specific location
python3 scripts/enc/yubikey_token_manager.py --decrypt-data-to /path/to/location
```

## Troubleshooting

### YubiKey Not Found
- Install yubikey-manager: `pip install yubikey-manager`
- Ensure YubiKey is plugged in and configured for HMAC-SHA1

### Wrong Passphrase
- The script will fail with "Decryption failed - wrong YubiKey or passcode"
- Double-check your passphrase (case-sensitive)

### Missing Data Folder
- If you get "Data folder not found", it's likely already encrypted
- Check status with `--status` command

## Integration with Development Workflow

1. **Before Development**: Decrypt data folder if needed
2. **After Development**: Encrypt data folder before committing
3. **CI/CD**: The encrypted data folder won't interfere with builds since it's in `.gitignore`

## Emergency Recovery

If you lose access to your YubiKey or forget your passphrase:
- Check if the `*_unencrypted_backup` folder still exists
- If not, the encrypted data in `encrypted_tokens.json` cannot be recovered without the YubiKey + passphrase

That's why it's critical to:
1. Keep your YubiKey safe
2. Remember your passphrase
3. Test decryption before deleting backups