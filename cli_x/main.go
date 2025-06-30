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
	fmMenu
	devMenu
	financeMenu
	knowledgeMenu
	ytMenu
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
	// Memory system for cursor positions
	mainMenuCursor      int
	fmMenuCursor        int
	devMenuCursor       int
	financeMenuCursor   int
	knowledgeMenuCursor int
	ytMenuCursor        int
}

var (
	// Subtle dark color palette
	primaryColor   = lipgloss.Color("#4A5568") // Gray-600
	secondaryColor = lipgloss.Color("#2D3748") // Gray-700
	accentColor    = lipgloss.Color("#68D391") // Green-300
	warningColor   = lipgloss.Color("#F6AD55") // Orange-300
	errorColor     = lipgloss.Color("#FC8181") // Red-300
	textColor      = lipgloss.Color("#E2E8F0") // Gray-200
	mutedColor     = lipgloss.Color("#A0AEC0") // Gray-400
	backgroundDark = lipgloss.Color("#1A202C") // Gray-900
	borderColor    = lipgloss.Color("#4A5568") // Gray-600

	// Enhanced styles
	titleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(textColor).
			Background(secondaryColor).
			Padding(0, 2).
			Margin(0, 0, 1, 0).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(borderColor).
			Align(lipgloss.Center)

	headerStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(accentColor).
			Padding(0, 1).
			Margin(0, 0, 1, 0)

	menuStyle = lipgloss.NewStyle().
			Foreground(textColor).
			Background(backgroundDark).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(borderColor).
			Padding(0, 2).
			Margin(0, 1, 0, 0).
			Width(28)

	selectedStyle = lipgloss.NewStyle().
			Foreground(textColor).
			Background(secondaryColor).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(accentColor).
			Bold(true).
			Padding(0, 2).
			Margin(0, 1, 0, 0).
			Width(28)

	emailListStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(mutedColor).
			Padding(1).
			Margin(1, 0)

	emailItemStyle = lipgloss.NewStyle().
			Foreground(textColor).
			Background(backgroundDark).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(borderColor).
			Padding(0, 2).
			Margin(0, 0, 1, 0)

	emailSelectedStyle = lipgloss.NewStyle().
				Foreground(textColor).
				Background(secondaryColor).
				Border(lipgloss.RoundedBorder()).
				BorderForeground(accentColor).
				Padding(0, 2).
				Margin(0, 0, 1, 0).
				Bold(true)

	unreadStyle = lipgloss.NewStyle().
			Foreground(warningColor).
			Bold(true)

	errorStyle = lipgloss.NewStyle().
			Foreground(errorColor).
			Bold(true).
			Padding(0, 2).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(errorColor).
			Background(backgroundDark)

	successStyle = lipgloss.NewStyle().
			Foreground(accentColor).
			Bold(true).
			Padding(0, 2).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(accentColor).
			Background(backgroundDark)

	inputStyle = lipgloss.NewStyle().
			Foreground(textColor).
			Background(secondaryColor).
			Padding(0, 2).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(accentColor).
			Width(40)

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

	// Main menu with four categories
	choices := []string{"FM", "dev", "Finance", "Knowledge"}

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
		case fmMenu:
			return m.updateFMMenu(msg)
		case devMenu:
			return m.updateDevMenu(msg)
		case financeMenu:
			return m.updateFinanceMenu(msg)
		case knowledgeMenu:
			return m.updateKnowledgeMenu(msg)
		case ytMenu:
			return m.updateYTMenu(msg)
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
		// Save current main menu position
		m.mainMenuCursor = m.cursor

		switch m.cursor {
		case 0: // FM
			m.state = fmMenu
			// Set FM menu based on account status
			if !m.config.HasAccount() {
				m.choices = []string{"Setup Account"}
			} else {
				m.choices = []string{"Read Emails", "Compose Email (Coming Soon)", "Account Settings"}
			}
			// Ensure cursor is within bounds
			if m.fmMenuCursor >= len(m.choices) {
				m.fmMenuCursor = 0
			}
			m.cursor = m.fmMenuCursor
			m.message = ""
		case 1: // dev
			m.state = devMenu
			m.choices = []string{"Docker Tools", "Deploy Scripts", "System Utils", "Code Gen"}
			// Ensure cursor is within bounds
			if m.devMenuCursor >= len(m.choices) {
				m.devMenuCursor = 0
			}
			m.cursor = m.devMenuCursor
			m.message = ""
		case 2: // Finance
			m.state = financeMenu
			m.choices = []string{"Budget Tracker", "Expense Manager", "Investment Portfolio", "Reports"}
			// Ensure cursor is within bounds
			if m.financeMenuCursor >= len(m.choices) {
				m.financeMenuCursor = 0
			}
			m.cursor = m.financeMenuCursor
			m.message = ""
		case 3: // Knowledge
			m.state = knowledgeMenu
			m.choices = []string{"YT", "Medium"}
			// Ensure cursor is within bounds
			if m.knowledgeMenuCursor >= len(m.choices) {
				m.knowledgeMenuCursor = 0
			}
			m.cursor = m.knowledgeMenuCursor
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
		m.state = knowledgeMenu
		m.cursor = m.knowledgeMenuCursor
		m.choices = []string{"YT", "Medium"}
	case "j": // Move down
		if m.cursor < len(m.choices)-1 {
			m.cursor++
		}
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
	case "l": // Select
		// Save current YT menu position
		m.ytMenuCursor = m.cursor

		switch m.cursor {
		case 0: // Video Manager
			m.message = infoStyle.Render("Video Manager - Coming Soon!")
		case 1: // Analytics
			m.message = infoStyle.Render("Analytics Dashboard - Coming Soon!")
		case 2: // Settings
			m.message = infoStyle.Render("YouTube Settings - Coming Soon!")
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
		m.cursor = m.mainMenuCursor
		m.choices = []string{"FM", "dev", "Finance", "Knowledge"}
	case "j": // Move down
		if m.cursor < len(m.choices)-1 {
			m.cursor++
		}
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
	case "l": // Select
		// Save current FM menu position
		m.fmMenuCursor = m.cursor

		if !m.config.HasAccount() {
			switch m.cursor {
			case 0: // Setup Account
				m.state = inputName
				m.input = ""
				m.tempAccount = FastmailAccount{}
				m.message = ""
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
		m.cursor = m.mainMenuCursor
		m.choices = []string{"FM", "dev", "Finance", "Knowledge"}
	case "j": // Move down
		if m.cursor < len(m.choices)-1 {
			m.cursor++
		}
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
	case "l": // Select
		// Save current dev menu position
		m.devMenuCursor = m.cursor

		switch m.cursor {
		case 0: // Docker Tools
			m.message = infoStyle.Render("Docker Management Tools - Coming Soon!")
		case 1: // Deploy Scripts
			m.message = infoStyle.Render("Deployment Scripts - Coming Soon!")
		case 2: // System Utils
			m.message = infoStyle.Render("System Utilities - Coming Soon!")
		case 3: // Code Gen
			m.message = infoStyle.Render("Code Generation Tools - Coming Soon!")
		}
	}
	return m, nil
}

func (m model) updateFinanceMenu(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = mainMenu
		m.cursor = m.mainMenuCursor
		m.choices = []string{"FM", "dev", "Finance", "Knowledge"}
	case "j": // Move down
		if m.cursor < len(m.choices)-1 {
			m.cursor++
		}
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
	case "l": // Select
		// Save current finance menu position
		m.financeMenuCursor = m.cursor

		switch m.cursor {
		case 0: // Budget Tracker
			m.message = infoStyle.Render("Budget Tracking - Coming Soon!")
		case 1: // Expense Manager
			m.message = infoStyle.Render("Expense Management - Coming Soon!")
		case 2: // Investment Portfolio
			m.message = infoStyle.Render("Investment Portfolio - Coming Soon!")
		case 3: // Reports
			m.message = infoStyle.Render("Financial Reports - Coming Soon!")
		}
	}
	return m, nil
}

func (m model) updateKnowledgeMenu(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = mainMenu
		m.cursor = m.mainMenuCursor
		m.choices = []string{"FM", "dev", "Finance", "Knowledge"}
	case "j": // Move down
		if m.cursor < len(m.choices)-1 {
			m.cursor++
		}
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
	case "l": // Select
		// Save current knowledge menu position
		m.knowledgeMenuCursor = m.cursor

		switch m.cursor {
		case 0: // YT
			m.state = ytMenu
			m.choices = []string{"Video Manager", "Analytics", "Settings"}
			// Ensure cursor is within bounds
			if m.ytMenuCursor >= len(m.choices) {
				m.ytMenuCursor = 0
			}
			m.cursor = m.ytMenuCursor
			m.message = ""
		case 1: // Medium
			m.message = infoStyle.Render("Medium Integration - Coming Soon!")
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
		// Save current email reading position and return to FM menu
		m.state = fmMenu
		m.cursor = m.fmMenuCursor
		m.loading = false
		if !m.config.HasAccount() {
			m.choices = []string{"Setup Account"}
		} else {
			m.choices = []string{"Read Emails", "Compose Email (Coming Soon)", "Account Settings"}
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
		m.cursor = m.mainMenuCursor
	}
	return m, nil
}

func (m model) updateViewAccount(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = fmMenu
		m.cursor = m.mainMenuCursor
		if !m.config.HasAccount() {
			m.choices = []string{"Setup Account"}
		} else {
			m.choices = []string{"Read Emails", "Compose Email (Coming Soon)", "Account Settings"}
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
		m.cursor = m.mainMenuCursor
		m.input = ""
		if !m.config.HasAccount() {
			m.choices = []string{"Setup Account"}
		} else {
			m.choices = []string{"Read Emails", "Compose Email (Coming Soon)", "Account Settings"}
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
				m.choices = []string{"Read Emails", "Compose Email (Coming Soon)", "Account Settings"}
			}

			m.state = fmMenu
			m.cursor = m.mainMenuCursor
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
	case fmMenu:
		title = "📧 FastMail Manager"
	case devMenu:
		title = "💻 Development Tools"
	case financeMenu:
		title = "💰 Finance Manager"
	case knowledgeMenu:
		title = "🧠 Knowledge Base"
	case ytMenu:
		title = "📺 YouTube Manager"
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
	case mainMenu, fmMenu, devMenu, financeMenu, knowledgeMenu, ytMenu:
		var headerText string
		switch m.state {
		case mainMenu:
			headerText = "🏠 Select Category"
		case fmMenu:
			headerText = "📧 FastMail Tools"
		case devMenu:
			headerText = "💻 Development Tools"
		case financeMenu:
			headerText = "💰 Finance Tools"
		case knowledgeMenu:
			headerText = "🧠 Knowledge Base"
		case ytMenu:
			headerText = "📺 YouTube Tools"
		}

		s.WriteString(headerStyle.Render(headerText))
		s.WriteString("\n")

		for i, choice := range m.choices {
			number := fmt.Sprintf("%d. ", i+1)
			content := number + choice

			if m.cursor == i {
				s.WriteString(selectedStyle.Render(content))
			} else {
				s.WriteString(menuStyle.Render(content))
			}
			s.WriteString("\n")
		}

		// Show account status for FM menu (more compact)
		if m.state == fmMenu {
			if m.config.HasAccount() {
				s.WriteString(successStyle.Render(fmt.Sprintf("Account: %s (%s)",
					m.config.MainAccount.Name, m.config.MainAccount.Email)))
			} else {
				s.WriteString(errorStyle.Render("⚠️  Please setup your FastMail account first"))
			}
			s.WriteString("\n")
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

	s.WriteString("\n")
	// Help text removed for cleaner design
	return s.String()
}

func (m model) renderEmailList() string {
	var items []string

	for i, email := range m.emails {
		number := fmt.Sprintf("%d. ", i+1)

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
			number, unreadMarker, timeStr, fromDisplay, subjectDisplay)

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
