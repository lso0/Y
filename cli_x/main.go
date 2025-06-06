package main

import (
	"fmt"
	"log"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type state int

const (
	mainMenu state = iota
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
	emails        []EmailSummary
	selectedEmail *Email
	emailClient   *EmailClient
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

	choices := []string{"📧 Read Emails", "✉️  Compose Email (Coming Soon)", "👤 Account Settings", "❌ Exit"}
	if !config.HasAccount() {
		choices = []string{"👤 Setup Account", "❌ Exit"}
	}

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
			m.state = mainMenu
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
	case "up", "k":
		if m.cursor > 0 {
			m.cursor--
		}
	case "down", "j":
		if m.cursor < len(m.choices)-1 {
			m.cursor++
		}
	case "enter", " ":
		if !m.config.HasAccount() {
			switch m.cursor {
			case 0: // Setup Account
				m.state = inputName
				m.input = ""
				m.tempAccount = FastmailAccount{}
				m.message = ""
			case 1: // Exit
				return m, tea.Quit
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
				m.message = infoStyle.Render("✉️ Email composing feature coming soon!")
			case 2: // Account Settings
				m.state = viewAccount
				m.cursor = 0
				m.message = ""
			case 3: // Exit
				return m, tea.Quit
			}
		}
	}
	return m, nil
}

func (m model) fetchEmails() tea.Cmd {
	return func() tea.Msg {
		client, err := NewEmailClient(m.config.MainAccount.APIKey)
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
	emails []EmailSummary
	client *EmailClient
	err    error
}

func (m model) updateReadEmails(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "esc", "q":
		m.state = mainMenu
		m.cursor = 0
		m.loading = false
	case "up", "k":
		if m.cursor > 0 {
			m.cursor--
		}
	case "down", "j":
		if m.cursor < len(m.emails)-1 {
			m.cursor++
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
	case "esc", "q":
		m.state = readEmails
		m.cursor = 0
	}
	return m, nil
}

func (m model) updateAddAccount(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "esc":
		m.state = mainMenu
		m.cursor = 0
	}
	return m, nil
}

func (m model) updateViewAccount(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "esc", "q":
		m.state = mainMenu
		m.cursor = 0
	case "enter", " ":
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
	case "esc":
		m.state = mainMenu
		m.cursor = 0
		m.input = ""
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
				// Update choices to show full menu now that account is set up
				m.choices = []string{"📧 Read Emails", "✉️  Compose Email (Coming Soon)", "👤 Account Settings", "❌ Exit"}
			}

			m.state = mainMenu
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

	// Title with enhanced styling
	s.WriteString(titleStyle.Render("📨 Fastmail CLI Manager"))
	s.WriteString("\n")

	if m.message != "" {
		s.WriteString(m.message)
		s.WriteString("\n\n")
	}

	switch m.state {
	case mainMenu:
		s.WriteString(headerStyle.Render("🏠 Main Menu"))
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

		if m.config.HasAccount() {
			s.WriteString("\n")
			s.WriteString(successStyle.Render(fmt.Sprintf("👤 Current account: %s (%s)",
				m.config.MainAccount.Name, m.config.MainAccount.Email)))
		} else {
			s.WriteString("\n")
			s.WriteString(errorStyle.Render("⚠️  Please setup your Fastmail account first"))
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
		s.WriteString(infoStyle.Render("Press 'r' to refresh, 'q' to go back"))

	case viewAccount:
		s.WriteString(headerStyle.Render("👤 Account Settings"))
		s.WriteString("\n")

		if m.config.HasAccount() {
			account := m.config.MainAccount
			s.WriteString(fmt.Sprintf("📛 Name: %s\n", account.Name))
			s.WriteString(fmt.Sprintf("📧 Email: %s\n", account.Email))
			s.WriteString(fmt.Sprintf("🔑 API Key: %s...\n", account.APIKey[:8]))
			s.WriteString("\n")
			s.WriteString(infoStyle.Render("Press Enter to edit account details"))
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
	s.WriteString(infoStyle.Render("Press 'Ctrl+C' to quit • Use ↑↓ or j/k to navigate • Enter to select"))
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
