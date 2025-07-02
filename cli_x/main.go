package main

import (
	"fmt"
	"log"
	"strconv"
	"strings"
	"time"

	fm "cli_x/mail"
	"cli_x/system"

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
	// Finance states
	financeList
	financeView
	financeAdd
	financeEdit
	financeInputName
	financeInputTag
	financeInputMonthly
	financeInputYearly
	financeInputRecurrence
	financeInputRenewalDate
	// GitHub states
	ghMenu
	ghRepos
	ghStarred
	// Alias states
	aliasMenu
	aliasList
	aliasAdd
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
	emailPage     int // Current page (0-based)
	loading       bool
	// Memory system for cursor positions
	mainMenuCursor      int
	fmMenuCursor        int
	devMenuCursor       int
	financeMenuCursor   int
	knowledgeMenuCursor int
	ytMenuCursor        int

	// Finance data
	financeData     *FinanceData
	services        []Service
	selectedService int
	tempService     Service
	editingIndex    int

	// Terminal dimensions for responsive design
	terminalWidth  int
	terminalHeight int

	// Status message for dev menu (shown at bottom)
	devMenuStatus string

	// Status message for YT menu (shown at bottom)
	ytMenuStatus string

	// Battery information for status bar
	battery *system.BatteryInfo

	// VPN information for status bar
	vpn *system.VPNInfo

	// GitHub data
	githubClient *GitHubClient
	githubUser   string
	repositories []Repository
	ghMenuCursor int

	// Finance input tracking
	financeInputField int // 0=name, 1=tag, 2=monthly
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
	orangeColor    = lipgloss.Color("#FF8C00") // Orange for selection

	// Enhanced styles
	titleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(textColor).
			Background(secondaryColor).
			Padding(0, 2).
			Margin(0, 0, 0, 0).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(borderColor).
			Align(lipgloss.Left)

	headerStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(accentColor).
			Padding(0, 2).
			Margin(0, 0, 0, 0).
			Align(lipgloss.Left)

	menuStyle = lipgloss.NewStyle().
			Foreground(textColor).
			Padding(0, 1).
			Margin(0, 0, 0, 0)

	selectedStyle = lipgloss.NewStyle().
			Foreground(orangeColor).
			Bold(true).
			Padding(0, 1).
			Margin(0, 0, 0, 0)

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

	statusBarStyle = lipgloss.NewStyle().
			Foreground(mutedColor).
			Background(backgroundDark).
			Align(lipgloss.Right).
			Padding(0, 1)

	placeholderStyle = lipgloss.NewStyle().
				Foreground(mutedColor).
				Italic(true)
)

func initialModel() model {
	config, err := loadConfig()
	if err != nil {
		log.Fatal(err)
	}

	// Main menu with four categories
	choices := []string{"FM", "Dev", "Finance", "Knowledge"}

	return model{
		config:         config,
		state:          mainMenu,
		selected:       make(map[int]struct{}),
		choices:        choices,
		terminalWidth:  80, // Default fallback
		terminalHeight: 24, // Default fallback
	}
}

func (m model) Init() tea.Cmd {
	// Request initial terminal size and fetch system info
	return tea.Batch(tea.EnterAltScreen, m.fetchBattery(), m.fetchVPN())
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		// Handle terminal resize - make interface responsive
		m.terminalWidth = msg.Width
		m.terminalHeight = msg.Height
		return m, nil
	case tea.KeyMsg:
		// Refresh battery info on any key press (lightweight)
		cmds := []tea.Cmd{}

		switch m.state {
		case mainMenu:
			model, cmd := m.updateMainMenu(msg)
			cmds = append(cmds, cmd)
			cmds = append(cmds, m.fetchBattery(), m.fetchVPN()) // Refresh system info
			return model, tea.Batch(cmds...)
		case fmMenu:
			model, cmd := m.updateFMMenu(msg)
			cmds = append(cmds, cmd)
			cmds = append(cmds, m.fetchBattery(), m.fetchVPN()) // Refresh system info
			return model, tea.Batch(cmds...)
		case devMenu:
			model, cmd := m.updateDevMenu(msg)
			cmds = append(cmds, cmd)
			cmds = append(cmds, m.fetchBattery(), m.fetchVPN()) // Refresh system info
			return model, tea.Batch(cmds...)
		case financeMenu:
			model, cmd := m.updateFinanceMenu(msg)
			cmds = append(cmds, cmd)
			cmds = append(cmds, m.fetchBattery(), m.fetchVPN()) // Refresh system info
			return model, tea.Batch(cmds...)
		case knowledgeMenu:
			model, cmd := m.updateKnowledgeMenu(msg)
			cmds = append(cmds, cmd)
			cmds = append(cmds, m.fetchBattery(), m.fetchVPN()) // Refresh system info
			return model, tea.Batch(cmds...)
		case ytMenu:
			model, cmd := m.updateYTMenu(msg)
			cmds = append(cmds, cmd)
			cmds = append(cmds, m.fetchBattery(), m.fetchVPN()) // Refresh system info
			return model, tea.Batch(cmds...)
		case ghMenu:
			return m.updateGHMenu(msg)
		case ghRepos:
			return m.updateGHRepos(msg)
		case ghStarred:
			return m.updateGHStarred(msg)
		case financeList:
			return m.updateFinanceList(msg)
		case financeView:
			return m.updateFinanceView(msg)
		case financeInputName:
			return m.updateFinanceInput(msg)
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
			m.emailPage = 0 // Reset to first page
			m.cursor = 0    // Reset cursor to first email
			m.message = ""
		}
		return m, nil
	case batteryFetchedMsg:
		m.battery = msg.battery
		return m, nil
	case vpnFetchedMsg:
		m.vpn = msg.vpn
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
				m.choices = []string{"Read Emails", "Compose Email (Coming Soon)", "Aliases"}
			}
			// Ensure cursor is within bounds
			if m.fmMenuCursor >= len(m.choices) {
				m.fmMenuCursor = 0
			}
			m.cursor = m.fmMenuCursor
			m.message = ""
		case 1: // Dev
			m.state = devMenu
			m.choices = []string{"docker", "gh", "gcp", "pxc", "x-automation"}
			// Ensure cursor is within bounds
			if m.devMenuCursor >= len(m.choices) {
				m.devMenuCursor = 0
			}
			m.cursor = m.devMenuCursor
			m.message = ""
			m.devMenuStatus = "" // Clear dev menu status when entering
		case 2: // Finance
			m.state = financeMenu
			m.choices = []string{"View Services", "Add Service"}
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
		m.ytMenuStatus = "" // Clear YT menu status when leaving
	case "j": // Move down
		if m.cursor < len(m.choices)-1 {
			m.cursor++
		}
		m.ytMenuStatus = "" // Clear status when navigating
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
		m.ytMenuStatus = "" // Clear status when navigating
	case "l": // Select
		// Save current YT menu position
		m.ytMenuCursor = m.cursor

		switch m.cursor {
		case 0: // Video Manager
			m.ytMenuStatus = "Video Manager - Coming Soon!"
		case 1: // Analytics
			m.ytMenuStatus = "Analytics Dashboard - Coming Soon!"
		case 2: // Settings
			m.ytMenuStatus = "YouTube Settings - Coming Soon!"
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
		m.choices = []string{"FM", "Dev", "Finance", "Knowledge"}
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
			case 2: // Aliases
				m.state = aliasMenu
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
		m.choices = []string{"FM", "Dev", "Finance", "Knowledge"}
		m.devMenuStatus = "" // Clear dev menu status when leaving
	case "j": // Move down
		if m.cursor < len(m.choices)-1 {
			m.cursor++
		}
		m.devMenuStatus = "" // Clear status when navigating
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
		m.devMenuStatus = "" // Clear status when navigating
	case "l": // Select
		// Save current dev menu position
		m.devMenuCursor = m.cursor

		switch m.cursor {
		case 0: // docker
			m.devMenuStatus = "Docker Management Tools - Coming Soon!"
		case 1: // gh
			// Initialize GitHub client if not already done
			if m.githubClient == nil {
				client, err := NewGitHubClient()
				if err != nil {
					m.devMenuStatus = fmt.Sprintf("Error: %v", err)
				} else {
					m.githubClient = client
					user, err := client.GetAuthenticatedUser()
					if err != nil {
						m.devMenuStatus = fmt.Sprintf("Error getting user: %v", err)
					} else {
						m.githubUser = user
						m.state = ghMenu
						m.choices = []string{"View Starred Repos", "View My Repos", "Account Info"}
						m.cursor = 0
						m.devMenuStatus = ""
					}
				}
			} else {
				m.state = ghMenu
				m.choices = []string{"View Starred Repos", "View My Repos", "Account Info"}
				m.cursor = 0
				m.devMenuStatus = ""
			}
		case 2: // gcp
			m.devMenuStatus = "Google Cloud Platform Tools - Coming Soon!"
		case 3: // pxc
			m.devMenuStatus = "Proxmox Cluster Tools - Coming Soon!"
		case 4: // x-automation
			m.devMenuStatus = "X-Automation Tools (firecrawl, proxy) - Coming Soon!"
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
		m.choices = []string{"FM", "Dev", "Finance", "Knowledge"}
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
		case 0: // View Services
			// Load finance data and switch to list view
			data, err := loadFinanceData()
			if err != nil {
				m.message = errorStyle.Render(fmt.Sprintf("Error loading finance data: %v", err))
				return m, nil
			}
			m.financeData = data
			m.services = data.Services
			m.state = financeList
			m.cursor = 0
			m.message = ""
		case 1: // Add Service
			m.tempService = Service{
				Name:        "",
				Tags:        "general",
				Prices:      Prices{Currency: "PLN", CMonthly: 0.0, CYearly: 0.0},
				Status:      1,
				Recurrence:  "M",
				RenewalDate: time.Now().AddDate(0, 1, 0).Format("2006-01-02"),
				BankService: "ING",
				Card:        "****-****-****-****",
				Account:     "default@example.com",
			}
			m.state = financeInputName
			m.financeInputField = 0
			m.input = ""
			m.message = ""
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
		m.choices = []string{"FM", "Dev", "Finance", "Knowledge"}
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
			m.ytMenuStatus = "" // Clear YT menu status when entering
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

		emails, err := client.GetInboxEmails(120) // Fetch 120 emails (3 pages of 40)
		if err != nil {
			return emailFetchedMsg{err: err}
		}

		return emailFetchedMsg{emails: emails, client: client}
	}
}

func (m model) fetchBattery() tea.Cmd {
	return func() tea.Msg {
		battery, err := system.GetBatteryInfo()
		return batteryFetchedMsg{battery: battery, err: err}
	}
}

func (m model) fetchVPN() tea.Cmd {
	return func() tea.Msg {
		vpn, err := system.GetVPNInfo()
		return vpnFetchedMsg{vpn: vpn, err: err}
	}
}

type emailFetchedMsg struct {
	emails []fm.EmailSummary
	client *fm.EmailClient
	err    error
}

type batteryFetchedMsg struct {
	battery *system.BatteryInfo
	err     error
}

type vpnFetchedMsg struct {
	vpn *system.VPNInfo
	err error
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
			m.choices = []string{"Read Emails", "Compose Email (Coming Soon)", "Aliases"}
		}
	case "j": // Move down
		if m.cursor < len(m.emails)-1 {
			m.cursor++
		}
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
	case "l": // View/Read email
		if m.cursor < len(m.emails) {
			// Switch to viewEmail state (implementation can be enhanced later)
			m.state = viewEmail
		}
	case "r":
		// Refresh emails
		if m.config.HasAccount() {
			m.loading = true
			return m, m.fetchEmails()
		}
	case "shift+1", "!":
		// Go to page 1
		m.emailPage = 0
		m.cursor = 0
	case "shift+2", "@":
		// Go to page 2
		if len(m.emails) > 40 {
			m.emailPage = 1
			m.cursor = 40 // Start of page 2
		}
	case "shift+3", "#":
		// Go to page 3
		if len(m.emails) > 80 {
			m.emailPage = 2
			m.cursor = 80 // Start of page 3
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
		// Keep cursor position when going back
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
			m.choices = []string{"Read Emails", "Compose Email (Coming Soon)", "Aliases"}
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
				m.choices = []string{"Read Emails", "Compose Email (Coming Soon)", "Aliases"}
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

func (m model) updateFinanceList(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = financeMenu
		m.cursor = m.financeMenuCursor
		m.choices = []string{"View Services", "Add Service"}
	case "j": // Move down
		if m.cursor < len(m.services)-1 {
			m.cursor++
		}
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
	case "l": // Select/View service
		if m.cursor < len(m.services) {
			m.selectedService = m.cursor
			m.state = financeView
		}
	case "d": // Delete service
		if m.cursor < len(m.services) {
			err := m.financeData.DeleteService(m.cursor)
			if err != nil {
				m.message = errorStyle.Render(fmt.Sprintf("Error deleting service: %v", err))
			} else {
				err = saveFinanceData(m.financeData)
				if err != nil {
					m.message = errorStyle.Render(fmt.Sprintf("Error saving data: %v", err))
				} else {
					m.services = m.financeData.Services
					if m.cursor >= len(m.services) && len(m.services) > 0 {
						m.cursor = len(m.services) - 1
					} else if len(m.services) == 0 {
						m.cursor = 0
					}
					m.message = successStyle.Render("✓ Service deleted successfully!")
				}
			}
		}
	case "e": // Edit service
		if m.cursor < len(m.services) {
			m.editingIndex = m.cursor
			m.tempService = m.services[m.cursor]
			m.state = financeInputName
			m.financeInputField = 0
			m.input = m.tempService.Name
			m.message = ""
		}
	}
	return m, nil
}

func (m model) updateFinanceView(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = financeList
		m.cursor = m.selectedService
	case "e": // Edit
		m.editingIndex = m.selectedService
		m.tempService = m.services[m.selectedService]
		m.state = financeInputName
		m.financeInputField = 0
		m.input = m.tempService.Name
		m.message = ""
	case "d": // Delete
		err := m.financeData.DeleteService(m.selectedService)
		if err != nil {
			m.message = errorStyle.Render(fmt.Sprintf("Error deleting service: %v", err))
		} else {
			err = saveFinanceData(m.financeData)
			if err != nil {
				m.message = errorStyle.Render(fmt.Sprintf("Error saving data: %v", err))
			} else {
				m.services = m.financeData.Services
				m.state = financeList
				m.cursor = 0
				m.message = successStyle.Render("✓ Service deleted successfully!")
			}
		}
	}
	return m, nil
}

func (m model) updateFinanceInput(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "esc", "h": // Go back
		m.state = financeMenu
		m.cursor = m.financeMenuCursor
		m.choices = []string{"View Services", "Add Service"}
		m.input = ""
		m.tempService = Service{}
		m.financeInputField = 0
	case "tab": // Move to next field
		m.saveCurrentField()
		m.financeInputField++
		if m.financeInputField > 2 { // Only 3 fields now (0, 1, 2)
			m.financeInputField = 0
		}
		m.loadFieldValue()
	case "shift+tab": // Move to previous field
		m.saveCurrentField()
		m.financeInputField--
		if m.financeInputField < 0 { // Loop to last field
			m.financeInputField = 2
		}
		m.loadFieldValue()
	case "enter":
		// Save current field and move to next, or save service if on last field
		m.saveCurrentField()
		if m.financeInputField < 2 {
			m.financeInputField++
			m.loadFieldValue()
		} else {
			// Save the service
			return m.saveFinanceService()
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

// Helper function to save current field value
func (m *model) saveCurrentField() {
	value := strings.TrimSpace(m.input)

	switch m.financeInputField {
	case 0: // Name
		if value != "" {
			m.tempService.Name = value
		}
	case 1: // Tag
		if value != "" {
			m.tempService.Tags = value
		}
	case 2: // Monthly
		if value != "" {
			if val, err := strconv.ParseFloat(value, 64); err == nil {
				m.tempService.Prices.CMonthly = val
			}
		}
	}
}

// Helper function to load field value into input
func (m *model) loadFieldValue() {
	switch m.financeInputField {
	case 0: // Name
		m.input = m.tempService.Name
	case 1: // Tag
		m.input = m.tempService.Tags
	case 2: // Monthly
		if m.tempService.Prices.CMonthly > 0 {
			m.input = fmt.Sprintf("%.2f", m.tempService.Prices.CMonthly)
		} else {
			m.input = ""
		}
	}
}

// Helper function to save the service
func (m model) saveFinanceService() (tea.Model, tea.Cmd) {
	// Validate required fields
	if m.tempService.Name == "" {
		m.message = errorStyle.Render("Service name is required")
		m.financeInputField = 0
		m.loadFieldValue()
		return m, nil
	}

	// Ensure finance data is loaded
	if m.financeData == nil {
		data, loadErr := loadFinanceData()
		if loadErr != nil {
			m.message = errorStyle.Render(fmt.Sprintf("Error loading finance data: %v", loadErr))
			return m, nil
		}
		m.financeData = data
	}

	var err error
	if m.editingIndex >= 0 {
		// Editing existing service
		err = m.financeData.UpdateService(m.editingIndex, m.tempService)
		if err == nil {
			err = saveFinanceData(m.financeData)
		}
		if err != nil {
			m.message = errorStyle.Render(fmt.Sprintf("Error updating service: %v", err))
		} else {
			m.message = successStyle.Render("✓ Service updated successfully!")
		}
	} else {
		// Adding new service
		m.financeData.AddService(m.tempService)
		err = saveFinanceData(m.financeData)
		if err != nil {
			m.message = errorStyle.Render(fmt.Sprintf("Error saving service: %v", err))
		} else {
			m.message = successStyle.Render("✓ Service added successfully!")
		}
	}

	m.state = financeMenu
	m.cursor = m.financeMenuCursor
	m.choices = []string{"View Services", "Add Service"}
	m.input = ""
	m.tempService = Service{}
	m.editingIndex = -1
	m.financeInputField = 0
	return m, nil
}

func (m model) updateGHMenu(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = devMenu
		m.cursor = m.devMenuCursor
		m.choices = []string{"docker", "gh", "gcp", "pxc", "x-automation"}
		m.devMenuStatus = ""
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
		case 0: // View Starred Repos
			if m.githubClient != nil {
				repos, err := m.githubClient.GetStarredRepos(20)
				if err != nil {
					m.message = errorStyle.Render(fmt.Sprintf("Error fetching starred repos: %v", err))
				} else {
					m.repositories = repos
					m.state = ghStarred
					m.cursor = 0
					m.message = ""
				}
			}
		case 1: // View My Repos
			if m.githubClient != nil {
				repos, err := m.githubClient.GetUserRepos(20)
				if err != nil {
					m.message = errorStyle.Render(fmt.Sprintf("Error fetching repos: %v", err))
				} else {
					m.repositories = repos
					m.state = ghRepos
					m.cursor = 0
					m.message = ""
				}
			}
		case 2: // Account Info
			if m.githubUser != "" {
				m.message = successStyle.Render(fmt.Sprintf("Logged in as: %s", m.githubUser))
			}
		}
	}
	return m, nil
}

func (m model) updateGHRepos(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = ghMenu
		m.cursor = 0
		m.choices = []string{"View Starred Repos", "View My Repos", "Account Info"}
	case "j": // Move down
		if m.cursor < len(m.repositories)-1 {
			m.cursor++
		}
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
	}
	return m, nil
}

func (m model) updateGHStarred(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = ghMenu
		m.cursor = 0
		m.choices = []string{"View Starred Repos", "View My Repos", "Account Info"}
	case "j": // Move down
		if m.cursor < len(m.repositories)-1 {
			m.cursor++
		}
	case "k": // Move up
		if m.cursor > 0 {
			m.cursor--
		}
	}
	return m, nil
}

func (m model) View() string {
	var s strings.Builder

	// Status bar with VPN and battery info (minimalistic)
	if m.vpn != nil || m.battery != nil {
		var statusText string

		// VPN status (if available)
		if m.vpn != nil {
			statusText += m.vpn.Icon + " "
		}

		// Battery status (if available)
		if m.battery != nil {
			statusText += fmt.Sprintf("%s%d%%", m.battery.Icon, m.battery.Percentage)
		}

		if statusText != "" {
			statusBar := statusBarStyle.Width(m.terminalWidth - 2).Render(statusText)
			s.WriteString(statusBar)
			s.WriteString("\n")
		}
	}

	if m.message != "" {
		s.WriteString(m.message)
		s.WriteString("\n")
	}

	switch m.state {
	case mainMenu, fmMenu, devMenu, financeMenu, knowledgeMenu, ytMenu, ghMenu:
		return m.renderMenuView(&s)

	case ghRepos, ghStarred:
		return m.renderGitHubRepos(&s)

	case financeList:
		return m.renderFinanceList(&s)

	case financeView:
		return m.renderFinanceView(&s)

	case financeInputName:
		return m.renderFinanceInput(&s)

	case readEmails:
		if m.loading {
			s.WriteString(loadingStyle.Render("⏳ Loading emails..."))
		} else if len(m.emails) == 0 {
			s.WriteString(infoStyle.Render("📭 No emails found"))
			s.WriteString("\n")
			s.WriteString(infoStyle.Render("Press 'r' to refresh, 'h' to go back"))
		} else {
			return m.renderEmailMatrix(&s)
		}

	case viewAccount:
		if m.config.HasAccount() {
			account := m.config.MainAccount
			s.WriteString(fmt.Sprintf("📛 Name: %s\n", account.Name))
			s.WriteString(fmt.Sprintf("📧 Email: %s\n", account.Email))
			s.WriteString(fmt.Sprintf("🔑 API Key: %s...\n", account.APIKey[:8]))
			s.WriteString("\n")
			s.WriteString(infoStyle.Render("Press 'l' to edit account details, 'h' to go back"))
		}

	case inputName:
		s.WriteString("📛 Enter account name: ")
		s.WriteString(inputStyle.Render(m.input + "_"))

	case inputEmail:
		s.WriteString("📧 Enter email address: ")
		s.WriteString(inputStyle.Render(m.input + "_"))

	case inputPassword:
		s.WriteString("🔒 Enter password: ")
		s.WriteString(inputStyle.Render(strings.Repeat("*", len(m.input)) + "_"))

	case inputAPIKey:
		s.WriteString("🔑 Enter API key: ")
		s.WriteString(inputStyle.Render(m.input + "_"))
		s.WriteString("\n")
		s.WriteString(infoStyle.Render("💡 Get your API key from: https://app.fastmail.com/settings/security/tokens/new"))
	}

	return s.String()
}

func (m model) renderMenuView(s *strings.Builder) string {
	// Show finance summary for Finance menu FIRST (before header)
	if m.state == financeMenu {
		// Load finance data to display summary
		data, err := loadFinanceData()
		if err != nil {
			s.WriteString(errorStyle.Render(fmt.Sprintf("Error loading finance data: %v", err)))
		} else {
			monthly := data.GetTotalMonthlyCost()
			yearly := data.GetTotalYearlyCost()
			activeServices := 0
			for _, service := range data.Services {
				if service.Status == 1 {
					activeServices++
				}
			}

			// Create compact styled summary box
			summaryBoxStyle := lipgloss.NewStyle().
				Foreground(textColor).
				Background(backgroundDark).
				Border(lipgloss.RoundedBorder()).
				BorderForeground(accentColor).
				Padding(0, 1).
				Margin(0, 0, 0, 0)

			// Dynamic summary text based on terminal width
			var summaryText string
			if m.terminalWidth > 120 {
				// Very wide terminal - show full details
				summaryText = fmt.Sprintf("💳 %.2f PLN/month  💰 %.2f PLN/year  📊 %d active services",
					monthly, yearly, activeServices)
			} else if m.terminalWidth < 80 {
				// Narrow terminal - minimal info
				summaryText = fmt.Sprintf("%.0f PLN/mo  📊 %d", monthly, activeServices)
			} else {
				// Standard terminal - balanced info
				summaryText = fmt.Sprintf("💳 %.0f PLN/mo  💰 %.0f PLN/yr  📊 %d active",
					monthly, yearly, activeServices)
			}

			summaryBox := summaryBoxStyle.Render(summaryText)
			s.WriteString(summaryBox)
		}
		s.WriteString("\n")
	}

	// Removed header for minimalistic design

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

	// Show dev menu status at the bottom
	if m.state == devMenu && m.devMenuStatus != "" {
		s.WriteString("\n")
		s.WriteString(infoStyle.Render(m.devMenuStatus))
		s.WriteString("\n")
	}

	// Show YT menu status at the bottom
	if m.state == ytMenu && m.ytMenuStatus != "" {
		s.WriteString("\n")
		s.WriteString(infoStyle.Render(m.ytMenuStatus))
		s.WriteString("\n")
	}

	s.WriteString("\n")
	return s.String()
}

func (m model) renderFinanceList(s *strings.Builder) string {
	if len(m.services) == 0 {
		s.WriteString(infoStyle.Render("No services found"))
		s.WriteString("\n")
		s.WriteString(infoStyle.Render("Press 'h' to go back"))
		s.WriteString("\n")
		return s.String()
	}

	// Calculate totals for summary
	totalMonthly := 0.0
	totalYearly := 0.0
	for _, service := range m.services {
		if service.Status == 1 {
			totalMonthly += service.GetMonthlyCost()
			totalYearly += service.GetYearlyCost()
		}
	}

	// Fixed number of services displayed - consistent scrolling experience
	maxVisible := 40
	start := 0
	end := len(m.services)

	if len(m.services) > maxVisible {
		// Smooth scrolling logic - scroll when cursor moves near edges
		// Keep cursor in middle positions when possible (positions 10-30 of 40)

		if m.cursor < 10 {
			// At the beginning - show first 40 services
			start = 0
			end = maxVisible
		} else if m.cursor >= len(m.services)-10 {
			// At the end - show last 40 services
			start = len(m.services) - maxVisible
			end = len(m.services)
		} else {
			// In the middle - keep cursor at position 20 (middle of 40)
			start = m.cursor - 20
			end = start + maxVisible
		}

		// Ensure bounds are valid
		if start < 0 {
			start = 0
			end = maxVisible
		}
		if end > len(m.services) {
			end = len(m.services)
			start = end - maxVisible
			if start < 0 {
				start = 0
			}
		}
	}

	// Show compact scroll indicator at top
	if start > 0 {
		s.WriteString(infoStyle.Render(fmt.Sprintf("↑ %d more above", start)))
		s.WriteString("\n")
	}

	// Display visible services
	for i := start; i < end; i++ {
		service := m.services[i]

		// Text truncation to fit fixed column widths
		var maxNameWidth, maxTagWidth int
		if m.terminalWidth > 120 {
			maxNameWidth = 25
			maxTagWidth = 15
		} else if m.terminalWidth < 80 {
			maxNameWidth = 20
			maxTagWidth = 12
		} else {
			maxNameWidth = 22
			maxTagWidth = 14
		}

		name := service.Name
		if len(name) > maxNameWidth {
			name = name[:maxNameWidth-3] + "..."
		}

		tag := service.Tags
		if len(tag) > maxTagWidth {
			tag = tag[:maxTagWidth-3] + "..."
		}

		monthly := service.GetMonthlyCost()

		// Renewal date truncation for fixed column width
		renewal := service.GetRenewalInfo()
		var maxRenewalWidth int
		if m.terminalWidth > 120 {
			maxRenewalWidth = 20
		} else if m.terminalWidth < 80 {
			// No renewal column in narrow view
			maxRenewalWidth = 0
		} else {
			maxRenewalWidth = 18
		}
		if maxRenewalWidth > 0 && len(renewal) > maxRenewalWidth {
			renewal = renewal[:maxRenewalWidth-3] + "..."
		}

		// Get status indicator (green/orange/red)
		statusIndicator := service.GetStatusIndicator()

		// Create clean matrix/table format with fixed column widths
		var boxContent string
		if m.terminalWidth > 120 {
			// Wide terminal - detailed matrix layout
			boxContent = fmt.Sprintf("%s %3d. %-25s | %-15s | %8.2f PLN/mo | %-20s",
				statusIndicator, i+1, name, tag, monthly, renewal)
		} else if m.terminalWidth < 80 {
			// Narrow terminal - compact matrix layout
			boxContent = fmt.Sprintf("%s %2d. %-20s | %-12s | %6.0f PLN",
				statusIndicator, i+1, name, tag, monthly)
		} else {
			// Standard terminal - balanced matrix layout
			boxContent = fmt.Sprintf("%s %2d. %-22s | %-14s | %7.2f PLN/mo | %-18s",
				statusIndicator, i+1, name, tag, monthly, renewal)
		}

		// Minimalistic service rendering without boxes
		if m.cursor == i {
			// Selected service - highlight with orange color
			s.WriteString(selectedStyle.Render(boxContent))
		} else {
			// Unselected service - normal style
			s.WriteString(menuStyle.Render(boxContent))
		}
		s.WriteString("\n")
	}

	// Show compact scroll indicator at bottom
	if end < len(m.services) {
		s.WriteString(infoStyle.Render(fmt.Sprintf("↓ %d more below", len(m.services)-end)))
		s.WriteString("\n")
	}

	// Dynamic status line based on terminal width
	var statusLine string
	if m.terminalWidth > 100 {
		// Wide terminal - show full status
		statusLine = fmt.Sprintf("Service %d of %d | %.2f PLN/month | j/k:navigate l:view e:edit d:delete h:back",
			m.cursor+1, len(m.services), totalMonthly)
	} else if m.terminalWidth < 80 {
		// Narrow terminal - minimal status
		statusLine = fmt.Sprintf("%d/%d | %.0f PLN | j/k/l/e/d/h",
			m.cursor+1, len(m.services), totalMonthly)
	} else {
		// Standard terminal - balanced status
		statusLine = fmt.Sprintf("Service %d/%d | %.0f PLN/mo | j/k:nav l:view e:edit d:del h:back",
			m.cursor+1, len(m.services), totalMonthly)
	}
	s.WriteString(infoStyle.Render(statusLine))
	return s.String()
}

func (m model) renderFinanceView(s *strings.Builder) string {
	if m.selectedService >= len(m.services) {
		s.WriteString(errorStyle.Render("Service not found"))
		s.WriteString("\n")
		return s.String()
	}

	service := m.services[m.selectedService]

	s.WriteString(fmt.Sprintf("📂 Category: %s\n", service.Tags))
	s.WriteString(fmt.Sprintf("💳 Monthly: %.2f %s\n", service.Prices.CMonthly, service.Prices.Currency))
	s.WriteString(fmt.Sprintf("💰 Yearly: %.2f %s\n", service.Prices.CYearly, service.Prices.Currency))
	s.WriteString(fmt.Sprintf("🔄 Recurrence: %s\n", service.Recurrence))
	s.WriteString(fmt.Sprintf("📅 Renewal: %s\n", service.GetRenewalInfo()))
	s.WriteString(fmt.Sprintf("📊 Status: %s\n", service.GetStatusText()))

	if service.Student {
		s.WriteString("🎓 Student Discount: Yes\n")
	}

	if service.TrialEndDate != "" {
		s.WriteString(fmt.Sprintf("🆓 Trial Ends: %s\n", service.TrialEndDate))
	}

	s.WriteString(fmt.Sprintf("🏦 Bank: %s\n", service.BankService))
	s.WriteString(fmt.Sprintf("💳 Card: %s\n", service.Card))
	s.WriteString(fmt.Sprintf("👤 Account: %s\n", service.Account))

	s.WriteString("\n")
	monthly := service.GetMonthlyCost()
	yearly := service.GetYearlyCost()
	s.WriteString(successStyle.Render(fmt.Sprintf("💡 Effective Cost: %.2f PLN/month (%.2f PLN/year)",
		monthly, yearly)))
	s.WriteString("\n")
	s.WriteString(infoStyle.Render("Press 'e' to edit, 'd' to delete, 'h' to go back"))
	s.WriteString("\n")
	return s.String()
}

func (m model) renderFinanceInput(s *strings.Builder) string {
	// Use Option 4: Terminal Prompt style
	return m.renderTerminalPrompt(s)
}

func (m model) renderHorizontalInput(s *strings.Builder) string {
	fields := []struct {
		name  string
		value string
	}{
		{"Name", m.tempService.Name},
		{"Tag", m.tempService.Tags},
		{"Monthly", fmt.Sprintf("%.2f", m.tempService.Prices.CMonthly)},
	}

	for i, field := range fields {
		s.WriteString(field.name)
		s.WriteString(": ")

		if i == m.financeInputField {
			// Current field being edited
			if m.input != "" {
				s.WriteString(lipgloss.NewStyle().Foreground(textColor).Render(m.input))
			} else if field.value != "" && field.value != "0.00" {
				s.WriteString(lipgloss.NewStyle().Foreground(textColor).Render(field.value))
			} else {
				s.WriteString(lipgloss.NewStyle().Foreground(mutedColor).Render("..."))
			}
			s.WriteString(lipgloss.NewStyle().Foreground(orangeColor).Render("_"))
		} else {
			// Other fields - show current values
			if field.value != "" && field.value != "0.00" {
				s.WriteString(lipgloss.NewStyle().Foreground(textColor).Render(field.value))
			} else {
				s.WriteString(lipgloss.NewStyle().Foreground(mutedColor).Render("..."))
			}
		}

		if i < len(fields)-1 {
			s.WriteString("  ")
		}
	}
	s.WriteString("\n")
	return s.String()
}

func (m model) renderTerminalPrompt(s *strings.Builder) string {
	prompts := []string{
		"Service name?",
		"Category?",
		"Monthly cost?",
	}

	if m.financeInputField < len(prompts) {
		s.WriteString(prompts[m.financeInputField])
		s.WriteString(" ")

		if m.input != "" {
			s.WriteString(lipgloss.NewStyle().Foreground(textColor).Render(m.input))
		}
		s.WriteString(lipgloss.NewStyle().Foreground(orangeColor).Render("_"))
		s.WriteString("\n")
	}
	return s.String()
}

func (m model) renderEmailMatrix(s *strings.Builder) string {
	if len(m.emails) == 0 {
		s.WriteString(infoStyle.Render("No emails found"))
		s.WriteString("\n")
		s.WriteString(infoStyle.Render("Press 'h' to go back"))
		s.WriteString("\n")
		return s.String()
	}

	// Page-based display - 40 emails per page
	emailsPerPage := 40
	totalPages := (len(m.emails) + emailsPerPage - 1) / emailsPerPage // Ceiling division

	// Ensure current page is valid
	if m.emailPage >= totalPages {
		m.emailPage = totalPages - 1
	}
	if m.emailPage < 0 {
		m.emailPage = 0
	}

	// Calculate start and end for current page
	start := m.emailPage * emailsPerPage
	end := start + emailsPerPage
	if end > len(m.emails) {
		end = len(m.emails)
	}

	// Adjust cursor to stay within current page bounds
	pageStart := start
	pageEnd := end - 1
	if m.cursor < pageStart {
		m.cursor = pageStart
	}
	if m.cursor > pageEnd {
		m.cursor = pageEnd
	}

	// Show page indicator at top
	if totalPages > 1 {
		pageInfo := fmt.Sprintf("Page %d of %d | Use Shift+1/2/3 to switch pages", m.emailPage+1, totalPages)
		s.WriteString(infoStyle.Render(pageInfo))
		s.WriteString("\n")
	}

	// Display visible emails in matrix format
	for i := start; i < end; i++ {
		email := m.emails[i]

		// Text truncation to fit fixed column widths
		var maxFromWidth, maxSubjectWidth int
		if m.terminalWidth > 120 {
			maxFromWidth = 25
			maxSubjectWidth = 50
		} else if m.terminalWidth < 80 {
			maxFromWidth = 15
			maxSubjectWidth = 25
		} else {
			maxFromWidth = 20
			maxSubjectWidth = 35
		}

		// From field truncation
		fromDisplay := email.From
		if len(fromDisplay) > maxFromWidth {
			fromDisplay = fromDisplay[:maxFromWidth-3] + "..."
		}

		// Subject field truncation
		subjectDisplay := email.Subject
		if subjectDisplay == "" {
			subjectDisplay = "(no subject)"
		}
		if len(subjectDisplay) > maxSubjectWidth {
			subjectDisplay = subjectDisplay[:maxSubjectWidth-3] + "..."
		}

		// Date formatting
		timeStr := email.Date.Format("15:04")
		if !email.Date.Truncate(24 * time.Hour).Equal(time.Now().Truncate(24 * time.Hour)) {
			timeStr = email.Date.Format("Jan 2")
		}

		// Unread status indicator (minimalistic)
		statusIndicator := "📖" // Read
		if email.IsUnread {
			statusIndicator = "📩" // Unread
		}

		// Create clean matrix/table format with fixed column widths
		var boxContent string
		if m.terminalWidth > 120 {
			// Wide terminal - detailed matrix layout
			boxContent = fmt.Sprintf("%s %3d. %-25s | %-50s | %8s",
				statusIndicator, i+1, fromDisplay, subjectDisplay, timeStr)
		} else if m.terminalWidth < 80 {
			// Narrow terminal - compact matrix layout
			boxContent = fmt.Sprintf("%s %2d. %-15s | %-25s",
				statusIndicator, i+1, fromDisplay, subjectDisplay)
		} else {
			// Standard terminal - balanced matrix layout
			boxContent = fmt.Sprintf("%s %2d. %-20s | %-35s | %8s",
				statusIndicator, i+1, fromDisplay, subjectDisplay, timeStr)
		}

		// Minimalistic email rendering without boxes
		if m.cursor == i {
			// Selected email - highlight with orange color
			s.WriteString(selectedStyle.Render(boxContent))
		} else {
			// Unselected email - normal style
			s.WriteString(menuStyle.Render(boxContent))
		}
		s.WriteString("\n")
	}

	// Dynamic status line based on terminal width
	unreadCount := 0
	for _, email := range m.emails {
		if email.IsUnread {
			unreadCount++
		}
	}

	var statusLine string
	if m.terminalWidth > 100 {
		// Wide terminal - show full status with page info
		statusLine = fmt.Sprintf("Email %d of %d | Page %d/%d | %d unread | j/k:nav l:read Shift+1/2/3:page r:refresh h:back",
			m.cursor+1, len(m.emails), m.emailPage+1, totalPages, unreadCount)
	} else if m.terminalWidth < 80 {
		// Narrow terminal - minimal status
		statusLine = fmt.Sprintf("%d/%d | P%d/%d | %d unread | j/k/l/r/h/Shift+1-3",
			m.cursor+1, len(m.emails), m.emailPage+1, totalPages, unreadCount)
	} else {
		// Standard terminal - balanced status
		statusLine = fmt.Sprintf("Email %d/%d | Page %d/%d | %d unread | j/k:nav l:read Shift+1/2/3:page r:refresh h:back",
			m.cursor+1, len(m.emails), m.emailPage+1, totalPages, unreadCount)
	}
	s.WriteString(infoStyle.Render(statusLine))
	return s.String()
}

func (m model) renderGitHubRepos(s *strings.Builder) string {
	if len(m.repositories) == 0 {
		s.WriteString(infoStyle.Render("No repositories found"))
		s.WriteString("\n")
		s.WriteString(infoStyle.Render("Press 'h' to go back"))
		s.WriteString("\n")
		return s.String()
	}

	// Show current GitHub user
	if m.githubUser != "" {
		s.WriteString(fmt.Sprintf("GitHub: %s\n\n", m.githubUser))
	}

	// Display repositories in minimalistic style
	for i, repo := range m.repositories {
		number := fmt.Sprintf("%d. ", i+1)

		// Truncate long names and descriptions
		name := repo.FullName
		if len(name) > 40 {
			name = name[:37] + "..."
		}

		desc := repo.Description
		if len(desc) > 60 {
			desc = desc[:57] + "..."
		}
		if desc == "" {
			desc = "(no description)"
		}

		content := fmt.Sprintf("%s%s\n   %s | ⭐ %d", number, name, desc, repo.Stars)

		if m.cursor == i {
			s.WriteString(selectedStyle.Render(content))
		} else {
			s.WriteString(menuStyle.Render(content))
		}
		s.WriteString("\n")
	}

	s.WriteString("\n")
	s.WriteString(infoStyle.Render(fmt.Sprintf("Repository %d of %d | j/k:navigate h:back", m.cursor+1, len(m.repositories))))
	return s.String()
}

func main() {
	p := tea.NewProgram(initialModel(), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		log.Fatal(err)
	}
}
