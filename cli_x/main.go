package main

import (
	"fmt"
	"log"
	"strings"
	"time"

	"cli_x/fm"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type state int

const (
	mainMenu state = iota
	ytMenu
	fmMenu
	devMenu
	addAccount
	viewAccount
	readEmails
	viewEmail
	inputName
	inputEmail
	inputPassword
	inputAPIKey
)

type model struct {
	config        *Config
	state         state
	cursor        int
	choices       []string
	selected      map[int]struct{}
	input         string
	tempAccount   FastmailAccount
	message       string
	err           error
	emails        []fm.EmailSummary
	selectedEmail *fm.Email
	emailClient   *fm.EmailClient
	loading       bool
}

var (
	// Enhanced color palette
	primaryColor   = lipgloss.Color("#6366F1") // Indigo
	secondaryColor = lipgloss.Color("#8B5CF6") // Purple
	accentColor    = lipgloss.Color("#10B981") // Emerald
	warningColor   = lipgloss.Color("#F59E0B") // Amber
	errorColor     = lipgloss.Color("#EF4444") // Red
	textColor      = lipgloss.Color("#F8FAFC") // Slate-50
	mutedColor     = lipgloss.Color("#94A3B8") // Slate-400
	backgroundDark = lipgloss.Color("#1E293B") // Slate-800

	// Enhanced styles
	titleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(textColor).
			Background(primaryColor).
			Padding(1, 2).
			Margin(0, 0, 1, 0).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(primaryColor)

	headerStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(primaryColor).
			Padding(0, 1).
			Margin(1, 0, 1, 0)

	menuStyle = lipgloss.NewStyle().
			Foreground(accentColor).
			Padding(0, 2)

	selectedStyle = lipgloss.NewStyle().
			Foreground(textColor).
			Background(primaryColor).
			Bold(true).
			Padding(0, 2).
			Margin(0, 0, 0, 1)

	emailListStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(mutedColor).
			Padding(1).
			Margin(1, 0)

	emailItemStyle = lipgloss.NewStyle().
			Foreground(textColor).
			Padding(0, 1).
			Margin(0, 0, 1, 0)

	emailSelectedStyle = lipgloss.NewStyle().
				Foreground(textColor).
				Background(secondaryColor).
				Padding(0, 1).
				Margin(0, 0, 1, 0).
				Bold(true)

	unreadStyle = lipgloss.NewStyle().
			Foreground(warningColor).
			Bold(true)

	errorStyle = lipgloss.NewStyle().
			Foreground(errorColor).
			Bold(true).
			Padding(0, 1).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(errorColor)

	successStyle = lipgloss.NewStyle().
			Foreground(accentColor).
			Bold(true).
			Padding(0, 1).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(accentColor)

	inputStyle = lipgloss.NewStyle().
			Foreground(textColor).
			Background(backgroundDark).
			Padding(0, 1).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(primaryColor)

	infoStyle = lipgloss.NewStyle().
			Foreground(mutedColor).
			Italic(true)

	loadingStyle = lipgloss.NewStyle().
			Foreground(warningColor).
			Bold(true)
)

func initialModel() model {
	config, err := loadConfig()
	if err != nil {
		log.Fatal(err)
	}

	// Main menu with three categories
	choices := []string{"YT (YouTube)", "FM (FastMail)", "dev (Development)"}

	return model{
		config:   config,
		state:    mainMenu,
		selected: make(map[int]struct{}),
		choices:  choices,
	}
}

func (m model) Init() tea.Cmd {
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch m.state {
		case mainMenu:
			return m.updateMainMenu(msg)
		case ytMenu:
			return m.updateYTMenu(msg)
		case fmMenu:
			return m.updateFMMenu(msg)
		case devMenu:
			return m.updateDevMenu(msg)
		case addAccount:
			return m.updateAddAccount(msg)
		case viewAccount:
			return m.updateViewAccount(msg)
		case readEmails:
			return m.updateReadEmails(msg)
		case viewEmail:
			return m.updateViewEmail(msg)
		case inputName, inputEmail, inputPassword, inputAPIKey:
			return m.updateInput(msg)
		}
	case emailFetchedMsg:
		m.loading = false
		if msg.err != nil {
			m.message = errorStyle.Render(fmt.Sprintf("Error fetching emails: %v", msg.err))
			m.state = fmMenu
		} else {
			m.emails = msg.emails
			m.emailClient = msg.client
			m.message = ""
		}
		return m, nil
	}
	return m, nil
}

func (m model) updateMainMenu(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c", "q":
		return m, tea.Quit
	case "j": // Move down
		if m.cursor < len(m.choices)-1 {
			m.cursor++
		}
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
	case "l": // Select/Enter
		switch m.cursor {
		case 0: // YT
			m.state = ytMenu
			m.cursor = 0
			m.choices = []string{"Video Manager", "Analytics", "Settings", "Back"}
			m.message = ""
		case 1: // FM
			m.state = fmMenu
			m.cursor = 0
			// Set FM menu based on account status
			if !m.config.HasAccount() {
				m.choices = []string{"Setup Account", "Back"}
			} else {
				m.choices = []string{"Read Emails", "Compose Email (Coming Soon)", "Account Settings", "Back"}
			}
			m.message = ""
		case 2: // dev
			m.state = devMenu
			m.cursor = 0
			m.choices = []string{"Docker Tools", "Deploy Scripts", "System Utils", "Code Gen", "Back"}
			m.message = ""
		}
	}
	return m, nil
}

func (m model) updateYTMenu(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = mainMenu
		m.cursor = 0
		m.choices = []string{"YT (YouTube)", "FM (FastMail)", "dev (Development)"}
	case "j": // Move down
		if m.cursor < len(m.choices)-1 {
			m.cursor++
		}
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
	case "l": // Select
		switch m.cursor {
		case 0: // Video Manager
			m.message = infoStyle.Render("Video Manager - Coming Soon!")
		case 1: // Analytics
			m.message = infoStyle.Render("Analytics Dashboard - Coming Soon!")
		case 2: // Settings
			m.message = infoStyle.Render("YouTube Settings - Coming Soon!")
		case 3: // Back
			m.state = mainMenu
			m.cursor = 0
			m.choices = []string{"YT (YouTube)", "FM (FastMail)", "dev (Development)"}
		}
	}
	return m, nil
}

func (m model) updateFMMenu(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = mainMenu
		m.cursor = 0
		m.choices = []string{"YT (YouTube)", "FM (FastMail)", "dev (Development)"}
	case "j": // Move down
		if m.cursor < len(m.choices)-1 {
			m.cursor++
		}
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
	case "l": // Select
		if !m.config.HasAccount() {
			switch m.cursor {
			case 0: // Setup Account
				m.state = inputName
				m.input = ""
				m.tempAccount = FastmailAccount{}
				m.message = ""
			case 1: // Back
				m.state = mainMenu
				m.cursor = 0
				m.choices = []string{"YT (YouTube)", "FM (FastMail)", "dev (Development)"}
			}
		} else {
			switch m.cursor {
			case 0: // Read Emails
				m.loading = true
				m.state = readEmails
				m.cursor = 0
				m.message = ""
				return m, m.fetchEmails()
			case 1: // Compose Email
				m.message = infoStyle.Render("Email composing feature coming soon!")
			case 2: // Account Settings
				m.state = viewAccount
				m.cursor = 0
				m.message = ""
			case 3: // Back
				m.state = mainMenu
				m.cursor = 0
				m.choices = []string{"YT (YouTube)", "FM (FastMail)", "dev (Development)"}
			}
		}
	}
	return m, nil
}

func (m model) updateDevMenu(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = mainMenu
		m.cursor = 0
		m.choices = []string{"YT (YouTube)", "FM (FastMail)", "dev (Development)"}
	case "j": // Move down
		if m.cursor < len(m.choices)-1 {
			m.cursor++
		}
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
	case "l": // Select
		switch m.cursor {
		case 0: // Docker Tools
			m.message = infoStyle.Render("Docker Management Tools - Coming Soon!")
		case 1: // Deploy Scripts
			m.message = infoStyle.Render("Deployment Scripts - Coming Soon!")
		case 2: // System Utils
			m.message = infoStyle.Render("System Utilities - Coming Soon!")
		case 3: // Code Gen
			m.message = infoStyle.Render("Code Generation Tools - Coming Soon!")
		case 4: // Back
			m.state = mainMenu
			m.cursor = 0
			m.choices = []string{"YT (YouTube)", "FM (FastMail)", "dev (Development)"}
		}
	}
	return m, nil
}

func (m model) fetchEmails() tea.Cmd {
	return func() tea.Msg {
		client, err := fm.NewEmailClient(m.config.MainAccount.APIKey)
		if err != nil {
			return emailFetchedMsg{err: err}
		}

		emails, err := client.GetInboxEmails(20)
		if err != nil {
			return emailFetchedMsg{err: err}
		}

		return emailFetchedMsg{emails: emails, client: client}
	}
}

type emailFetchedMsg struct {
	emails []fm.EmailSummary
	client *fm.EmailClient
	err    error
}

func (m model) updateReadEmails(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = fmMenu
		m.cursor = 0
		m.loading = false
		if !m.config.HasAccount() {
			m.choices = []string{"Setup Account", "Back"}
		} else {
			m.choices = []string{"Read Emails", "Compose Email (Coming Soon)", "Account Settings", "Back"}
		}
	case "j": // Move down
		if m.cursor < len(m.emails)-1 {
			m.cursor++
		}
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
	case "r":
		// Refresh emails
		if m.config.HasAccount() {
			m.loading = true
			return m, m.fetchEmails()
		}
	}
	return m, nil
}

func (m model) updateViewEmail(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = readEmails
		m.cursor = 0
	}
	return m, nil
}

func (m model) updateAddAccount(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = fmMenu
		m.cursor = 0
	}
	return m, nil
}

func (m model) updateViewAccount(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = fmMenu
		m.cursor = 0
		if !m.config.HasAccount() {
			m.choices = []string{"Setup Account", "Back"}
		} else {
			m.choices = []string{"Read Emails", "Compose Email (Coming Soon)", "Account Settings", "Back"}
		}
	case "l": // Select/Edit
		// Start editing account
		if m.config.HasAccount() {
			m.tempAccount = *m.config.MainAccount
			m.state = inputName
			m.input = m.tempAccount.Name
			m.message = ""
		}
	}
	return m, nil
}

func (m model) updateInput(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back instead of esc
		m.state = fmMenu
		m.cursor = 0
		m.input = ""
		if !m.config.HasAccount() {
			m.choices = []string{"Setup Account", "Back"}
		} else {
			m.choices = []string{"Read Emails", "Compose Email (Coming Soon)", "Account Settings", "Back"}
		}
	case "enter":
		switch m.state {
		case inputName:
			if strings.TrimSpace(m.input) == "" {
				m.message = errorStyle.Render("Name cannot be empty")
				return m, nil
			}
			m.tempAccount.Name = strings.TrimSpace(m.input)
			m.state = inputEmail
			m.input = m.tempAccount.Email
		case inputEmail:
			if strings.TrimSpace(m.input) == "" {
				m.message = errorStyle.Render("Email cannot be empty")
				return m, nil
			}
			m.tempAccount.Email = strings.TrimSpace(m.input)
			m.state = inputPassword
			m.input = ""
		case inputPassword:
			if strings.TrimSpace(m.input) == "" {
				m.message = errorStyle.Render("Password cannot be empty")
				return m, nil
			}
			m.tempAccount.Pass = strings.TrimSpace(m.input)
			m.state = inputAPIKey
			m.input = m.tempAccount.APIKey
		case inputAPIKey:
			if strings.TrimSpace(m.input) == "" {
				m.message = errorStyle.Render("API Key cannot be empty")
				return m, nil
			}
			m.tempAccount.APIKey = strings.TrimSpace(m.input)

			// Save the account
			m.config.SetAccount(m.tempAccount.Name, m.tempAccount.Email, m.tempAccount.Pass, m.tempAccount.APIKey)
			if err := saveConfig(m.config); err != nil {
				m.message = errorStyle.Render(fmt.Sprintf("Error saving account: %v", err))
			} else {
				m.message = successStyle.Render("✓ Account saved successfully!")
				// Update choices to show full FM menu now that account is set up
				m.choices = []string{"Read Emails", "Compose Email (Coming Soon)", "Account Settings", "Back"}
			}

			m.state = fmMenu
			m.cursor = 0
			m.input = ""
			m.tempAccount = FastmailAccount{}
		}
	case "backspace":
		if len(m.input) > 0 {
			m.input = m.input[:len(m.input)-1]
		}
	default:
		if len(msg.String()) == 1 {
			m.input += msg.String()
		}
	}
	return m, nil
}

func (m model) View() string {
	var s strings.Builder

	// Dynamic title based on current state
	var title string
	switch m.state {
	case mainMenu:
		title = "🚀 CLI-X Main Menu"
	case ytMenu:
		title = "📺 YouTube Manager"
	case fmMenu:
		title = "📧 FastMail Manager"
	case devMenu:
		title = "💻 Development Tools"
	default:
		title = "📧 FastMail Manager"
	}

	s.WriteString(titleStyle.Render(title))
	s.WriteString("\n")

	if m.message != "" {
		s.WriteString(m.message)
		s.WriteString("\n\n")
	}

	switch m.state {
	case mainMenu, ytMenu, fmMenu, devMenu:
		var headerText string
		switch m.state {
		case mainMenu:
			headerText = "🏠 Select Category"
		case ytMenu:
			headerText = "📺 YouTube Tools"
		case fmMenu:
			headerText = "📧 FastMail Tools"
		case devMenu:
			headerText = "💻 Development Tools"
		}

		s.WriteString(headerStyle.Render(headerText))
		s.WriteString("\n")

		for i, choice := range m.choices {
			cursor := "  "
			if m.cursor == i {
				cursor = "▶ "
			}

			if m.cursor == i {
				s.WriteString(selectedStyle.Render(cursor + choice))
			} else {
				s.WriteString(menuStyle.Render(cursor + choice))
			}
			s.WriteString("\n")
		}

		// Show account status for FM menu
		if m.state == fmMenu {
			s.WriteString("\n")
			if m.config.HasAccount() {
				s.WriteString(successStyle.Render(fmt.Sprintf("👤 Current account: %s (%s)",
					m.config.MainAccount.Name, m.config.MainAccount.Email)))
			} else {
				s.WriteString(errorStyle.Render("⚠️  Please setup your FastMail account first"))
			}
		}

	case readEmails:
		s.WriteString(headerStyle.Render("📧 Inbox"))
		s.WriteString("\n")

		if m.loading {
			s.WriteString(loadingStyle.Render("⏳ Loading emails..."))
		} else if len(m.emails) == 0 {
			s.WriteString(infoStyle.Render("📭 No emails found"))
		} else {
			emailList := emailListStyle.Render(m.renderEmailList())
			s.WriteString(emailList)
		}

		s.WriteString("\n")
		s.WriteString(infoStyle.Render("Press 'r' to refresh, 'h' to go back"))

	case viewAccount:
		s.WriteString(headerStyle.Render("Account Settings"))
		s.WriteString("\n")

		if m.config.HasAccount() {
			account := m.config.MainAccount
			s.WriteString(fmt.Sprintf("📛 Name: %s\n", account.Name))
			s.WriteString(fmt.Sprintf("📧 Email: %s\n", account.Email))
			s.WriteString(fmt.Sprintf("🔑 API Key: %s...\n", account.APIKey[:8]))
			s.WriteString("\n")
			s.WriteString(infoStyle.Render("Press 'l' to edit account details, 'h' to go back"))
		}

	case inputName:
		s.WriteString(headerStyle.Render("👤 Account Setup"))
		s.WriteString("\n")
		s.WriteString("📛 Enter account name: ")
		s.WriteString(inputStyle.Render(m.input + "_"))

	case inputEmail:
		s.WriteString(headerStyle.Render("👤 Account Setup"))
		s.WriteString("\n")
		s.WriteString("📧 Enter email address: ")
		s.WriteString(inputStyle.Render(m.input + "_"))

	case inputPassword:
		s.WriteString(headerStyle.Render("👤 Account Setup"))
		s.WriteString("\n")
		s.WriteString("🔒 Enter password: ")
		s.WriteString(inputStyle.Render(strings.Repeat("*", len(m.input)) + "_"))

	case inputAPIKey:
		s.WriteString(headerStyle.Render("👤 Account Setup"))
		s.WriteString("\n")
		s.WriteString("🔑 Enter API key: ")
		s.WriteString(inputStyle.Render(m.input + "_"))
		s.WriteString("\n")
		s.WriteString(infoStyle.Render("💡 Get your API key from: https://app.fastmail.com/settings/security/tokens/new"))
	}

	s.WriteString("\n\n")
	// Help text removed for cleaner design
	return s.String()
}

func (m model) renderEmailList() string {
	var items []string

	for i, email := range m.emails {
		cursor := "  "
		if m.cursor == i {
			cursor = "▶ "
		}

		unreadMarker := " "
		if email.IsUnread {
			unreadMarker = unreadStyle.Render("●")
		}

		timeStr := email.Date.Format("15:04")
		if !email.Date.Truncate(24 * time.Hour).Equal(time.Now().Truncate(24 * time.Hour)) {
			timeStr = email.Date.Format("Jan 2")
		}

		subjectDisplay := email.Subject
		if len(subjectDisplay) > 50 {
			subjectDisplay = subjectDisplay[:47] + "..."
		}
		if subjectDisplay == "" {
			subjectDisplay = "(no subject)"
		}

		fromDisplay := email.From
		if len(fromDisplay) > 20 {
			fromDisplay = fromDisplay[:17] + "..."
		}

		line := fmt.Sprintf("%s%s %s  %-20s  %s",
			cursor, unreadMarker, timeStr, fromDisplay, subjectDisplay)

		if m.cursor == i {
			items = append(items, emailSelectedStyle.Render(line))
		} else {
			items = append(items, emailItemStyle.Render(line))
		}
	}

	return strings.Join(items, "\n")
}

func main() {
	p := tea.NewProgram(initialModel(), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		log.Fatal(err)
	}
}
