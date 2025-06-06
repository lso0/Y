package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/joho/godotenv"
)

type FastmailAccount struct {
	Name   string
	Email  string
	Pass   string
	APIKey string
}

type Config struct {
	MainAccount *FastmailAccount
}

const envFileName = ".env"

func getConfigPath() string {
	// First try current directory (project local)
	if _, err := os.Stat(envFileName); err == nil {
		return envFileName
	}

	// Fall back to system config directory
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return envFileName
	}
	return filepath.Join(homeDir, ".config", "cli_x", envFileName)
}

func loadConfig() (*Config, error) {
	configPath := getConfigPath()

	// If using system config path, create directory if it doesn't exist
	if !strings.Contains(configPath, envFileName) || strings.Contains(configPath, ".config") {
		configDir := filepath.Dir(configPath)
		if err := os.MkdirAll(configDir, 0755); err != nil {
			return nil, fmt.Errorf("failed to create config directory: %w", err)
		}
	}

	// If .env file doesn't exist, create a default one
	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		defaultEnv := `# Fastmail CLI Configuration
# Get your API key from: https://app.fastmail.com/settings/security/tokens/new

# Account Configuration
FASTMAIL_NAME=""
FASTMAIL_EMAIL=""
FASTMAIL_PASSWORD=""
FASTMAIL_API_KEY=""
`
		if err := os.WriteFile(configPath, []byte(defaultEnv), 0600); err != nil {
			return nil, fmt.Errorf("failed to create default .env file: %w", err)
		}
		return &Config{}, nil
	}

	// Load .env file
	if err := godotenv.Load(configPath); err != nil {
		return nil, fmt.Errorf("failed to load .env file: %w", err)
	}

	// Read environment variables
	name := os.Getenv("FASTMAIL_NAME")
	email := os.Getenv("FASTMAIL_EMAIL")
	password := os.Getenv("FASTMAIL_PASSWORD")
	apiKey := os.Getenv("FASTMAIL_API_KEY")

	config := &Config{}

	// If all credentials are provided, create the account
	if name != "" && email != "" && password != "" && apiKey != "" {
		config.MainAccount = &FastmailAccount{
			Name:   name,
			Email:  email,
			Pass:   password,
			APIKey: apiKey,
		}
	}

	return config, nil
}

func saveConfig(config *Config) error {
	configPath := getConfigPath()

	var envContent strings.Builder
	envContent.WriteString("# Fastmail CLI Configuration\n")
	envContent.WriteString("# Get your API key from: https://app.fastmail.com/settings/security/tokens/new\n\n")
	envContent.WriteString("# Account Configuration\n")

	if config.MainAccount != nil {
		envContent.WriteString(fmt.Sprintf("FASTMAIL_NAME=\"%s\"\n", config.MainAccount.Name))
		envContent.WriteString(fmt.Sprintf("FASTMAIL_EMAIL=\"%s\"\n", config.MainAccount.Email))
		envContent.WriteString(fmt.Sprintf("FASTMAIL_PASSWORD=\"%s\"\n", config.MainAccount.Pass))
		envContent.WriteString(fmt.Sprintf("FASTMAIL_API_KEY=\"%s\"\n", config.MainAccount.APIKey))
	} else {
		envContent.WriteString("FASTMAIL_NAME=\"\"\n")
		envContent.WriteString("FASTMAIL_EMAIL=\"\"\n")
		envContent.WriteString("FASTMAIL_PASSWORD=\"\"\n")
		envContent.WriteString("FASTMAIL_API_KEY=\"\"\n")
	}

	if err := os.WriteFile(configPath, []byte(envContent.String()), 0600); err != nil {
		return fmt.Errorf("failed to write .env file: %w", err)
	}

	return nil
}

func (c *Config) SetAccount(name, email, password, apiKey string) {
	c.MainAccount = &FastmailAccount{
		Name:   name,
		Email:  email,
		Pass:   password,
		APIKey: apiKey,
	}
}

func (c *Config) GetMainAccount() *FastmailAccount {
	return c.MainAccount
}

func (c *Config) HasAccount() bool {
	return c.MainAccount != nil
}
