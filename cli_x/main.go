package main

import (
	"fmt"
	"log"
	"strconv"
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

	// Finance data
	financeData     *FinanceData
	services        []Service
	selectedService int
	tempService     Service
	editingIndex    int
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
		case financeList:
			return m.updateFinanceList(msg)
		case financeView:
			return m.updateFinanceView(msg)
		case financeInputName, financeInputTag, financeInputMonthly, financeInputYearly, financeInputRecurrence, financeInputRenewalDate:
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
			m.choices = []string{"View Services", "Add Service", "Categories"}
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
			m.state = financeAdd
			m.tempService = Service{
				Prices:      Prices{Currency: "PLN"},
				Status:      1,
				BankService: "ING",
				Card:        "5123 4567 8901 2345",
				Account:     "wiktor11gal@gmail.com",
			}
			m.state = financeInputName
			m.input = ""
			m.message = ""
		case 2: // Categories
			data, err := loadFinanceData()
			if err != nil {
				m.message = errorStyle.Render(fmt.Sprintf("Error loading finance data: %v", err))
				return m, nil
			}
			categories := data.GetCategories()
			m.message = infoStyle.Render(fmt.Sprintf("📂 Categories: %s", strings.Join(categories, ", ")))
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

func (m model) updateFinanceList(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		return m, tea.Quit
	case "h": // Go back
		m.state = financeMenu
		m.cursor = m.financeMenuCursor
		m.choices = []string{"View Services", "Add Service", "Summary Report", "Categories"}
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
	case "h": // Go back
		m.state = financeMenu
		m.cursor = m.financeMenuCursor
		m.choices = []string{"View Services", "Add Service", "Categories"}
		m.input = ""
		m.tempService = Service{}
	case "enter":
		switch m.state {
		case financeInputName:
			if strings.TrimSpace(m.input) == "" {
				m.message = errorStyle.Render("Name cannot be empty")
				return m, nil
			}
			m.tempService.Name = strings.TrimSpace(m.input)
			m.state = financeInputTag
			m.input = m.tempService.Tags
		case financeInputTag:
			if strings.TrimSpace(m.input) == "" {
				m.message = errorStyle.Render("Tag/Category cannot be empty")
				return m, nil
			}
			m.tempService.Tags = strings.TrimSpace(m.input)
			m.state = financeInputMonthly
			m.input = fmt.Sprintf("%.2f", m.tempService.Prices.CMonthly)
		case financeInputMonthly:
			if val, err := strconv.ParseFloat(strings.TrimSpace(m.input), 64); err == nil {
				m.tempService.Prices.CMonthly = val
			}
			m.state = financeInputYearly
			m.input = fmt.Sprintf("%.2f", m.tempService.Prices.CYearly)
		case financeInputYearly:
			if val, err := strconv.ParseFloat(strings.TrimSpace(m.input), 64); err == nil {
				m.tempService.Prices.CYearly = val
			}
			m.state = financeInputRecurrence
			m.input = m.tempService.Recurrence
		case financeInputRecurrence:
			recurrence := strings.TrimSpace(m.input)
			if recurrence == "" {
				recurrence = "Y"
			}
			m.tempService.Recurrence = recurrence
			m.state = financeInputRenewalDate
			m.input = m.tempService.RenewalDate
		case financeInputRenewalDate:
			if strings.TrimSpace(m.input) != "" {
				if _, err := time.Parse("2006-01-02", strings.TrimSpace(m.input)); err != nil {
					m.message = errorStyle.Render("Date format should be YYYY-MM-DD")
					return m, nil
				}
			}
			m.tempService.RenewalDate = strings.TrimSpace(m.input)

			// Save the service
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
				if m.financeData == nil {
					data, loadErr := loadFinanceData()
					if loadErr != nil {
						m.message = errorStyle.Render(fmt.Sprintf("Error loading finance data: %v", loadErr))
						return m, nil
					}
					m.financeData = data
				}
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
			m.choices = []string{"View Services", "Add Service", "Categories"}
			m.input = ""
			m.tempService = Service{}
			m.editingIndex = -1
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
		return m.renderMenuView(&s)

	case financeList:
		return m.renderFinanceList(&s)

	case financeView:
		return m.renderFinanceView(&s)

	case financeInputName, financeInputTag, financeInputMonthly, financeInputYearly, financeInputRecurrence, financeInputRenewalDate:
		return m.renderFinanceInput(&s)

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

func (m model) renderMenuView(s *strings.Builder) string {
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

	// Show finance summary for Finance menu
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

			// Create horizontal layout with boxes
			managerBox := headerStyle.Render("💰 Finance Manager")
			summaryBox := successStyle.Render(fmt.Sprintf("💳 %.2f PLN/month  💰 %.2f PLN/year  📊 %d active services",
				monthly, yearly, activeServices))

			// Display them horizontally
			s.WriteString(managerBox + "  " + summaryBox)
		}
		s.WriteString("\n")
	}

	s.WriteString("\n")
	return s.String()
}

func (m model) renderFinanceList(s *strings.Builder) string {
	s.WriteString(headerStyle.Render("💰 Finance Services"))
	s.WriteString("\n")

	if len(m.services) == 0 {
		s.WriteString(infoStyle.Render("📭 No services found"))
		s.WriteString("\n")
		s.WriteString(infoStyle.Render("Press 'h' to go back"))
		s.WriteString("\n")
		return s.String()
	}

	totalMonthly := 0.0
	totalYearly := 0.0

	for i, service := range m.services {
		if service.Status == 1 {
			totalMonthly += service.GetMonthlyCost()
			totalYearly += service.GetYearlyCost()
		}

		number := fmt.Sprintf("%d. ", i+1)
		name := service.Name
		if len(name) > 20 {
			name = name[:17] + "..."
		}

		tag := service.Tags
		if len(tag) > 12 {
			tag = tag[:9] + "..."
		}

		monthly := service.GetMonthlyCost()
		status := ""
		if service.Status == 1 {
			status = "🟢"
		} else {
			status = "🔴"
		}

		renewal := service.GetRenewalInfo()
		if len(renewal) > 15 {
			renewal = renewal[:12] + "..."
		}

		line := fmt.Sprintf("%s%s %-20s %-12s %7.2f PLN/mo %s %s",
			number, status, name, tag, monthly, renewal,
			func() string {
				if service.Student {
					return "🎓"
				}
				return ""
			}())

		if m.cursor == i {
			s.WriteString(selectedStyle.Render(line))
		} else {
			s.WriteString(menuStyle.Render(line))
		}
		s.WriteString("\n")
	}

	s.WriteString("\n")
	s.WriteString(successStyle.Render(fmt.Sprintf("💰 Total: %.2f PLN/month (%.2f PLN/year)",
		totalMonthly, totalYearly)))
	s.WriteString("\n")
	s.WriteString(infoStyle.Render("Press 'l' to view, 'e' to edit, 'd' to delete, 'h' to go back"))
	s.WriteString("\n")
	return s.String()
}

func (m model) renderFinanceView(s *strings.Builder) string {
	if m.selectedService >= len(m.services) {
		s.WriteString(errorStyle.Render("Service not found"))
		s.WriteString("\n")
		return s.String()
	}

	service := m.services[m.selectedService]

	s.WriteString(headerStyle.Render(fmt.Sprintf("💰 %s", service.Name)))
	s.WriteString("\n")

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
	var title, prompt string

	if m.editingIndex >= 0 {
		title = "✏️ Edit Service"
	} else {
		title = "➕ Add Service"
	}

	switch m.state {
	case financeInputName:
		prompt = "📝 Service Name"
	case financeInputTag:
		prompt = "📂 Category/Tag"
	case financeInputMonthly:
		prompt = "💳 Monthly Cost (PLN)"
	case financeInputYearly:
		prompt = "💰 Yearly Cost (PLN)"
	case financeInputRecurrence:
		prompt = "🔄 Recurrence (Y/M/2Y)"
	case financeInputRenewalDate:
		prompt = "📅 Renewal Date (YYYY-MM-DD)"
	}

	s.WriteString(headerStyle.Render(title))
	s.WriteString("\n")
	s.WriteString(fmt.Sprintf("%s: ", prompt))
	s.WriteString(inputStyle.Render(m.input + "_"))
	s.WriteString("\n")

	// Show helpful hints
	switch m.state {
	case financeInputRecurrence:
		s.WriteString(infoStyle.Render("💡 Y = Yearly, M = Monthly, 2Y = Every 2 years"))
	case financeInputRenewalDate:
		s.WriteString(infoStyle.Render("💡 Format: 2025-12-31"))
	}

	s.WriteString("\n")
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
