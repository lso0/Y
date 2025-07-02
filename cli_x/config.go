package main

import (
	"fmt"
	"os"
	"path/filepath"

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

func loadConfig() (*Config, error) {
	// Load .env file from parent directory (Y/.env)
	envPath := filepath.Join("..", ".env")

	// Check if .env file exists
	if _, err := os.Stat(envPath); err != nil {
		return nil, fmt.Errorf("could not find .env file at %s: %w", envPath, err)
	}

	// Load .env file
	if err := godotenv.Load(envPath); err != nil {
		return nil, fmt.Errorf("failed to load .env file: %w", err)
	}

	// Read FastMail environment variables
	apiKey := os.Getenv("FM_API_0")
	email := os.Getenv("FM_M_0")
	password := os.Getenv("FM_P_0")

	config := &Config{}

	// If all FastMail credentials are provided, create the account
	if apiKey != "" && email != "" && password != "" {
		config.MainAccount = &FastmailAccount{
			Name:   "FastMail Account", // Default name since it's not in env
			Email:  email,
			Pass:   password,
			APIKey: apiKey,
		}
	}

	return config, nil
}

func saveConfig(config *Config) error {
	// Since we're reading from parent .env file, we don't save config changes
	// The .env file should be managed manually
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
	return c.MainAccount != nil && c.MainAccount.APIKey != ""
}
