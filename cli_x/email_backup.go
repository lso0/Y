package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	fm "cli_x/mail"
)

// EmailBackup represents a complete email backup with metadata
type EmailBackup struct {
	ID           string                 `json:"id"`
	BackupDate   time.Time              `json:"backup_date"`
	EmailData    *fm.Email              `json:"email_data"`
	Summary      fm.EmailSummary        `json:"summary"`
	Source       string                 `json:"source"`        // "inbox", "sent", "spam", etc.
	BackupReason string                 `json:"backup_reason"` // "deleted", "archived", "routine_backup"
	Metadata     map[string]interface{} `json:"metadata"`
}

// AliasBackup stores FastMail alias configurations
type AliasBackup struct {
	ID          string                 `json:"id"`
	BackupDate  time.Time              `json:"backup_date"`
	AliasEmail  string                 `json:"alias_email"`
	TargetEmail string                 `json:"target_email"`
	Settings    map[string]interface{} `json:"settings"`
	Active      bool                   `json:"active"`
}

// SettingsBackup stores FastMail account settings
type SettingsBackup struct {
	ID         string                 `json:"id"`
	BackupDate time.Time              `json:"backup_date"`
	Settings   map[string]interface{} `json:"settings"`
	Version    string                 `json:"version"`
}

// EmailBackupManager handles all backup operations
type EmailBackupManager struct {
	dataDir     string
	emailsDir   string
	aliasesDir  string
	settingsDir string
	client      *fm.EmailClient
}

// NewEmailBackupManager creates a new backup manager
func NewEmailBackupManager(client *fm.EmailClient) *EmailBackupManager {
	dataDir := "data"

	manager := &EmailBackupManager{
		dataDir:     dataDir,
		emailsDir:   filepath.Join(dataDir, "emails"),
		aliasesDir:  filepath.Join(dataDir, "aliases"),
		settingsDir: filepath.Join(dataDir, "settings"),
		client:      client,
	}

	// Create backup directories
	manager.createDirectories()

	return manager
}

// createDirectories ensures all backup directories exist
func (ebm *EmailBackupManager) createDirectories() error {
	dirs := []string{
		ebm.dataDir,
		ebm.emailsDir,
		filepath.Join(ebm.emailsDir, "inbox"),
		filepath.Join(ebm.emailsDir, "sent"),
		filepath.Join(ebm.emailsDir, "spam"),
		filepath.Join(ebm.emailsDir, "trash"),
		filepath.Join(ebm.emailsDir, "deleted"),
		ebm.aliasesDir,
		ebm.settingsDir,
	}

	for _, dir := range dirs {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}

	return nil
}

// BackupEmail creates a complete backup of an email before deletion/archiving
func (ebm *EmailBackupManager) BackupEmail(emailSummary fm.EmailSummary, reason string) error {
	// Get full email details
	emailDetails, err := ebm.client.GetEmailDetails(emailSummary.ID)
	if err != nil {
		return fmt.Errorf("failed to get email details: %w", err)
	}

	// Create backup record
	backup := EmailBackup{
		ID:           fmt.Sprintf("backup_%s_%d", emailSummary.ID, time.Now().UnixNano()),
		BackupDate:   time.Now(),
		EmailData:    emailDetails,
		Summary:      emailSummary,
		Source:       emailSummary.Mailbox,
		BackupReason: reason,
		Metadata: map[string]interface{}{
			"original_mailbox": emailSummary.Mailbox,
			"backup_version":   "1.0",
			"size_bytes":       len(emailSummary.Preview), // Approximate
		},
	}

	// Determine backup subdirectory
	var subDir string
	if reason == "deleted" {
		subDir = "deleted"
	} else {
		subDir = emailSummary.Mailbox
	}

	// Save to appropriate directory
	backupPath := filepath.Join(ebm.emailsDir, subDir, fmt.Sprintf("%s.json", backup.ID))

	return ebm.saveBackupToFile(backup, backupPath)
}

// BackupAlias saves alias configuration
func (ebm *EmailBackupManager) BackupAlias(aliasEmail, targetEmail string, settings map[string]interface{}) error {
	backup := AliasBackup{
		ID:          fmt.Sprintf("alias_%s_%d", aliasEmail, time.Now().UnixNano()),
		BackupDate:  time.Now(),
		AliasEmail:  aliasEmail,
		TargetEmail: targetEmail,
		Settings:    settings,
		Active:      true,
	}

	backupPath := filepath.Join(ebm.aliasesDir, fmt.Sprintf("%s.json", backup.ID))

	return ebm.saveBackupToFile(backup, backupPath)
}

// BackupSettings saves current FastMail settings
func (ebm *EmailBackupManager) BackupSettings(settings map[string]interface{}) error {
	backup := SettingsBackup{
		ID:         fmt.Sprintf("settings_%d", time.Now().UnixNano()),
		BackupDate: time.Now(),
		Settings:   settings,
		Version:    "1.0",
	}

	backupPath := filepath.Join(ebm.settingsDir, fmt.Sprintf("%s.json", backup.ID))

	return ebm.saveBackupToFile(backup, backupPath)
}

// saveBackupToFile writes backup data to JSON file
func (ebm *EmailBackupManager) saveBackupToFile(data interface{}, filePath string) error {
	file, err := os.Create(filePath)
	if err != nil {
		return fmt.Errorf("failed to create backup file: %w", err)
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ") // Pretty print JSON

	if err := encoder.Encode(data); err != nil {
		return fmt.Errorf("failed to encode backup data: %w", err)
	}

	return nil
}

// GetBackupStats returns statistics about backed up data
func (ebm *EmailBackupManager) GetBackupStats() (map[string]interface{}, error) {
	stats := make(map[string]interface{})

	// Count emails in each directory
	emailDirs := []string{"inbox", "sent", "spam", "trash", "deleted"}
	for _, dir := range emailDirs {
		count, err := ebm.countFilesInDir(filepath.Join(ebm.emailsDir, dir))
		if err != nil {
			continue // Skip on error
		}
		stats[fmt.Sprintf("emails_%s", dir)] = count
	}

	// Count aliases
	aliasCount, _ := ebm.countFilesInDir(ebm.aliasesDir)
	stats["aliases"] = aliasCount

	// Count settings backups
	settingsCount, _ := ebm.countFilesInDir(ebm.settingsDir)
	stats["settings_backups"] = settingsCount

	return stats, nil
}

// countFilesInDir counts JSON files in a directory
func (ebm *EmailBackupManager) countFilesInDir(dirPath string) (int, error) {
	files, err := os.ReadDir(dirPath)
	if err != nil {
		return 0, err
	}

	count := 0
	for _, file := range files {
		if !file.IsDir() && filepath.Ext(file.Name()) == ".json" {
			count++
		}
	}

	return count, nil
}
