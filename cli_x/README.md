# 📨 Fastmail CLI Manager

A beautiful, modern Terminal User Interface (TUI) application for managing Fastmail accounts and reading emails written in Go.

## ✨ Features

### 🎨 Beautiful Interface
- **Modern Design**: Clean, colorful interface with intuitive navigation
- **Enhanced Colors**: Beautiful color palette with indigo, purple, emerald, and amber accents
- **Visual Elements**: Emoji icons, rounded borders, and stylish highlighting
- **Responsive Layout**: Professional spacing and typography

### 📧 Email Features ✅
- **Email Reading**: Browse your inbox with a beautiful email list
- **Real-time Loading**: Live email fetching with loading indicators
- **Unread Indicators**: Visual markers for unread emails
- **Email Preview**: See subject, sender, date, and preview text
- **Refresh Function**: Press 'r' to refresh your inbox

### 🔧 Account Management
- **Secure Storage**: Credentials stored in .env files (much safer than JSON!)
- **Easy Setup**: Step-by-step account configuration wizard
- **Account Editing**: Modify your account details anytime
- **API Integration**: Direct connection to Fastmail's JMAP API

### 🎮 Navigation
- **Intuitive Controls**: Use arrow keys or vim-style j/k navigation
- **Quick Actions**: Enter/Space to select, Esc to go back
- **Keyboard Shortcuts**: Efficient navigation throughout the app

## 🚀 Installation

1. **Prerequisites**: Ensure you have Go 1.21 or later installed
2. **Clone/Download**: Get the project files
3. **Install Dependencies**:
   ```bash
   go mod tidy
   ```

## 🎯 Usage

### Quick Start
```bash
# Run directly with Go
go run .

# Or build and run the executable
go build -o fastmail-cli
./fastmail-cli
```

### 🗝️ Getting Your API Key

1. Visit: https://app.fastmail.com/settings/security/tokens/new
2. Name your token (e.g., "CLI Manager")
3. Select required scopes:
   - ✅ **Mail** (for reading emails)
   - ✅ **Email Submission** (for sending - coming soon)
4. Copy the generated API key

### 🔧 Configuration

The app uses a secure `.env` file for credential storage:

**Location**: `~/.config/cli_x/.env`

### 📝 Setting Up Your Account

1. Run the application for the first time
2. Select **"👤 Setup Account"** 
3. Enter your account details step by step
4. Your credentials will be securely saved

### 📧 Reading Your Emails

1. Select **"📧 Read Emails"** from the main menu
2. Wait for emails to load
3. Navigate with arrow keys or j/k
4. Press **'r'** to refresh
5. Press **'q'** to go back

## 🎮 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑`/`↓` or `j`/`k` | Navigate |
| `Enter` or `Space` | Select |
| `Esc` or `q` | Go back |
| `r` | Refresh emails |
| `Ctrl+C` | Quit |

## 🔒 Security

**✅ Secure Storage**: Credentials stored in .env files with proper permissions

**✅ No Plain Text JSON**: Industry-standard environment variable approach

## 🚧 Roadmap

### Current Features ✅
- [x] Beautiful TUI interface
- [x] Secure .env configuration
- [x] Real email reading via JMAP
- [x] Inbox browsing with visual indicators

### Coming Soon
- [ ] Email composition and sending
- [ ] Individual email viewing
- [ ] Multiple mailbox support
- [ ] Search and filtering

---

**Made with ❤️ for terminal lovers and email power users**

*Now with real email reading functionality!* 📧✨ 