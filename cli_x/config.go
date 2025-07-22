package main

import (
	"encoding/json"
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

type AppSettings struct {
	SortMode int `json:"sort_mode"` // 0=unsorted, 1=date, 2=monthly, 3=yearly
}

type Config struct {
	MainAccount *FastmailAccount
	Settings    *AppSettings
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

	config := &Config{
		Settings: &AppSettings{
			SortMode: 0, // Default to unsorted
		},
	}

	// If all FastMail credentials are provided, create the account
	if apiKey != "" && email != "" && password != "" {
		config.MainAccount = &FastmailAccount{
			Name:   "FastMail Account", // Default name since it's not in env
			Email:  email,
			Pass:   password,
			APIKey: apiKey,
		}
	}

	// Load app-specific settings from local config file
	configPath := "cli_x_config.json"
	if _, err := os.Stat(configPath); err == nil {
		// Config file exists, load it
		data, err := os.ReadFile(configPath)
		if err == nil {
			var settings AppSettings
			if json.Unmarshal(data, &settings) == nil {
				config.Settings = &settings
			}
		}
	}

	return config, nil
}

func saveConfig(config *Config) error {
	// Save app-specific settings to local config file
	if config.Settings != nil {
		configPath := "cli_x_config.json"
		data, err := json.MarshalIndent(config.Settings, "", "  ")
		if err != nil {
			return fmt.Errorf("failed to marshal config: %w", err)
		}

		if err := os.WriteFile(configPath, data, 0644); err != nil {
			return fmt.Errorf("failed to save config: %w", err)
		}
	}

	// Note: We don't save .env file changes as that should be managed manually
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
