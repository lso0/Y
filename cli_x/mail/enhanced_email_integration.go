package fm

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"time"
)

// EnhancedEmailContent represents the full content from the Python enhanced reader
type EnhancedEmailContent struct {
	ID                string            `json:"id"`
	Subject           string            `json:"subject"`
	From              string            `json:"from"`
	To                string            `json:"to"`
	CC                string            `json:"cc"`
	BCC               string            `json:"bcc"`
	Date              string            `json:"date"`
	MessageID         string            `json:"message_id"`
	ReplyTo           string            `json:"reply_to"`
	TextPlain         string            `json:"text_plain"`
	TextHTML          string            `json:"text_html"`
	TextHTMLConverted string            `json:"text_html_converted"`
	CombinedText      string            `json:"combined_text"`
	Attachments       []AttachmentInfo  `json:"attachments"`
	Images            []ImageInfo       `json:"images"`
	InlineImages      []ImageInfo       `json:"inline_images"`
	HasAttachments    bool              `json:"has_attachments"`
	HasImages         bool              `json:"has_images"`
	ContentParts      []ContentPartInfo `json:"content_parts"`
	SecurityInfo      EmailSecurityInfo `json:"security_info"`
}

// AttachmentInfo represents attachment metadata
type AttachmentInfo struct {
	Filename           string `json:"filename"`
	ContentType        string `json:"content_type"`
	Size               int    `json:"size"`
	PartNumber         int    `json:"part_number"`
	ContentDisposition string `json:"content_disposition"`
	CanSave            bool   `json:"can_save"`
	PreviewAvailable   bool   `json:"preview_available"`
	PreviewContent     string `json:"preview_content,omitempty"`
}

// ImageInfo represents image metadata
type ImageInfo struct {
	Filename    string `json:"filename"`
	Path        string `json:"path"`
	ContentType string `json:"content_type"`
	Size        int64  `json:"size"`
	ContentID   string `json:"content_id"`
	PartNumber  int    `json:"part_number"`
}

// ContentPartInfo represents email part metadata
type ContentPartInfo struct {
	PartNumber  int    `json:"part_number"`
	ContentType string `json:"content_type"`
	Filename    string `json:"filename"`
	Disposition string `json:"disposition"`
	Size        int    `json:"size"`
}

// EmailSecurityInfo represents security analysis
type EmailSecurityInfo struct {
	SPFPass            bool   `json:"spf_pass"`
	DKIMValid          bool   `json:"dkim_valid"`
	DMARCPass          bool   `json:"dmarc_pass"`
	IsEncrypted        bool   `json:"is_encrypted"`
	HasSuspiciousLinks bool   `json:"has_suspicious_links"`
	SenderReputation   string `json:"sender_reputation"`
}

// TTSResult represents the result of TTS generation
type TTSResult struct {
	AudioFile string `json:"audio_file"`
	Success   bool   `json:"success"`
	Error     string `json:"error,omitempty"`
}

// EnhancedEmailReader provides enhanced email reading capabilities
type EnhancedEmailReader struct {
	PythonPath    string
	ScriptPath    string
	TTSScriptPath string
	WorkingDir    string
}

// NewEnhancedEmailReader creates a new enhanced email reader
func NewEnhancedEmailReader() *EnhancedEmailReader {
	// Get the working directory and adjust if we're in cli_x
	workingDir, _ := os.Getwd()

	// Check if we're running from inside cli_x directory
	if filepath.Base(workingDir) == "cli_x" {
		// Go up one directory to the project root
		workingDir = filepath.Dir(workingDir)
	}

	// Use the venv Python if available
	venvPython := filepath.Join(workingDir, "venv", "bin", "python3")
	pythonPath := "python3" // Default fallback
	if _, err := os.Stat(venvPython); err == nil {
		pythonPath = venvPython
	}

	return &EnhancedEmailReader{
		PythonPath:    pythonPath,
		ScriptPath:    filepath.Join(workingDir, "cli_x", "mail", "fm", "enhanced_email_reader.py"),
		TTSScriptPath: filepath.Join(workingDir, "cli_x", "dia_tts_engine.py"),
		WorkingDir:    workingDir,
	}
}

// ReadEmailWithFullContent reads an email with comprehensive content extraction
func (r *EnhancedEmailReader) ReadEmailWithFullContent(emailID, folder string) (*EnhancedEmailContent, error) {
	// Check if enhanced reader script exists
	if _, err := os.Stat(r.ScriptPath); os.IsNotExist(err) {
		return nil, fmt.Errorf("enhanced email reader script not found: %s", r.ScriptPath)
	}

	// Prepare command arguments
	args := []string{
		r.ScriptPath,
		emailID,
		"--folder", folder,
		"--save-json",
	}

	// Execute Python script
	cmd := exec.Command(r.PythonPath, args...)
	cmd.Dir = r.WorkingDir

	// Set environment variables to ensure Python can find dotenv file
	cmd.Env = append(os.Environ(),
		fmt.Sprintf("PYTHONPATH=%s", r.WorkingDir),
	)

	// Capture output
	output, err := cmd.CombinedOutput()
	if err != nil {
		// Log the full output for debugging
		return nil, fmt.Errorf("enhanced email reader failed: %v\nPython output:\n%s", err, string(output))
	}

	// Always log Python output for debugging
	fmt.Printf("DEBUG: Python script output:\n%s\n", string(output))

	// Look for the generated JSON file
	jsonFile, err := r.findGeneratedJSONFile(emailID)
	if err != nil {
		// Also log the directory we're looking in
		enhancedDir := filepath.Join(r.WorkingDir, "cli_x", "mail", "enhanced_emails")
		fmt.Printf("DEBUG: Looking for JSON in directory: %s\n", enhancedDir)
		if files, dirErr := os.ReadDir(enhancedDir); dirErr == nil {
			fmt.Printf("DEBUG: Files in enhanced_emails directory:\n")
			for _, f := range files {
				fmt.Printf("  - %s\n", f.Name())
			}
		}
		return nil, fmt.Errorf("failed to find generated JSON file: %v\nPython output was:\n%s", err, string(output))
	}

	// Read and parse the JSON file
	content, err := r.parseJSONFile(jsonFile)
	if err != nil {
		return nil, fmt.Errorf("failed to parse JSON file: %v", err)
	}

	return content, nil
}

// ConvertEmailToSpeech converts email content to speech using Dia TTS
func (r *EnhancedEmailReader) ConvertEmailToSpeech(content *EnhancedEmailContent, outputFile string, playAudio bool) (*TTSResult, error) {
	// Check if TTS script exists
	if _, err := os.Stat(r.TTSScriptPath); os.IsNotExist(err) {
		return &TTSResult{Success: false, Error: "Dia TTS script not found"}, nil
	}

	// Prepare email content for TTS
	emailText := r.prepareEmailForTTS(content)

	// Prepare command arguments
	args := []string{
		r.TTSScriptPath,
		emailText,
		"--email-mode",
		"--subject", content.Subject,
		"--sender", content.From,
	}

	if outputFile != "" {
		args = append(args, "--output", outputFile)
	}

	if playAudio {
		args = append(args, "--play")
	}

	// Execute TTS script
	cmd := exec.Command(r.PythonPath, args...)
	cmd.Dir = r.WorkingDir

	// Capture output
	output, err := cmd.CombinedOutput()
	if err != nil {
		return &TTSResult{
			Success: false,
			Error:   fmt.Sprintf("TTS generation failed: %v\nOutput: %s", err, string(output)),
		}, nil
	}

	// Parse output to find generated audio file
	audioFile := r.extractAudioFileFromOutput(string(output))

	return &TTSResult{
		AudioFile: audioFile,
		Success:   true,
	}, nil
}

// prepareEmailForTTS prepares email content for TTS conversion
func (r *EnhancedEmailReader) prepareEmailForTTS(content *EnhancedEmailContent) string {
	// Use combined text if available, otherwise use plain text
	text := content.CombinedText
	if text == "" {
		text = content.TextPlain
	}
	if text == "" {
		text = content.TextHTMLConverted
	}

	// Limit text length for reasonable speech duration
	words := splitWords(text)
	if len(words) > 200 {
		text = joinWords(words[:200]) + "... Email content truncated for speech."
	}

	return text
}

// findGeneratedJSONFile finds the most recently generated JSON file for the email
func (r *EnhancedEmailReader) findGeneratedJSONFile(emailID string) (string, error) {
	enhancedDir := filepath.Join(r.WorkingDir, "cli_x", "mail", "enhanced_emails")

	// Look for files matching the pattern
	pattern := filepath.Join(enhancedDir, fmt.Sprintf("enhanced_email_%s_*.json", emailID))
	matches, err := filepath.Glob(pattern)
	if err != nil {
		return "", err
	}

	if len(matches) == 0 {
		return "", fmt.Errorf("no JSON file found for email ID %s", emailID)
	}

	// Return the most recent file
	mostRecent := matches[0]
	var mostRecentTime time.Time

	for _, match := range matches {
		if info, err := os.Stat(match); err == nil {
			if info.ModTime().After(mostRecentTime) {
				mostRecent = match
				mostRecentTime = info.ModTime()
			}
		}
	}

	return mostRecent, nil
}

// parseJSONFile parses the enhanced email JSON file
func (r *EnhancedEmailReader) parseJSONFile(filename string) (*EnhancedEmailContent, error) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	var content EnhancedEmailContent
	if err := json.Unmarshal(data, &content); err != nil {
		return nil, err
	}

	return &content, nil
}

// extractAudioFileFromOutput extracts the generated audio file path from TTS output
func (r *EnhancedEmailReader) extractAudioFileFromOutput(output string) string {
	// Simple parsing - look for "Generated: " line
	lines := splitLines(output)
	for _, line := range lines {
		if contains(line, "Generated:") || contains(line, "✅ Generated:") {
			// Extract file path after "Generated: "
			parts := splitString(line, " ")
			for i, part := range parts {
				if (part == "Generated:" || part == "✅ Generated:") && i+1 < len(parts) {
					return parts[i+1]
				}
			}
		}
	}
	return ""
}

// DisplayEnhancedEmailContent formats and displays enhanced email content
func (r *EnhancedEmailReader) DisplayEnhancedEmailContent(content *EnhancedEmailContent) string {
	var result string

	// Header information
	result += fmt.Sprintf("📧 EMAIL DETAILS\n")
	result += fmt.Sprintf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	result += fmt.Sprintf("Subject: %s\n", content.Subject)
	result += fmt.Sprintf("From: %s\n", content.From)
	result += fmt.Sprintf("To: %s\n", content.To)
	if content.CC != "" {
		result += fmt.Sprintf("CC: %s\n", content.CC)
	}
	result += fmt.Sprintf("Date: %s\n", content.Date)

	// Security indicators
	security := content.SecurityInfo
	securityIcon := "🟢"
	if !(security.SPFPass && security.DKIMValid && security.DMARCPass) {
		securityIcon = "🟡"
	}
	result += fmt.Sprintf("Security: %s SPF:%t DKIM:%t DMARC:%t\n",
		securityIcon, security.SPFPass, security.DKIMValid, security.DMARCPass)

	// Content summary
	result += fmt.Sprintf("\n📊 CONTENT SUMMARY\n")
	result += fmt.Sprintf("Parts: %d | Attachments: %d | Images: %d\n",
		len(content.ContentParts), len(content.Attachments),
		len(content.Images)+len(content.InlineImages))

	// Attachments
	if len(content.Attachments) > 0 {
		result += fmt.Sprintf("\n📎 ATTACHMENTS (%d)\n", len(content.Attachments))
		for _, att := range content.Attachments {
			result += fmt.Sprintf("  • %s (%s, %d bytes)\n",
				att.Filename, att.ContentType, att.Size)
			if att.PreviewContent != "" {
				preview := att.PreviewContent
				if len(preview) > 100 {
					preview = preview[:100] + "..."
				}
				result += fmt.Sprintf("    Preview: %s\n", preview)
			}
		}
	}

	// Images
	totalImages := len(content.Images) + len(content.InlineImages)
	if totalImages > 0 {
		result += fmt.Sprintf("\n🖼️  IMAGES (%d)\n", totalImages)
		for _, img := range content.Images {
			result += fmt.Sprintf("  • %s (%s, %d bytes)\n",
				img.Filename, img.ContentType, img.Size)
		}
		for _, img := range content.InlineImages {
			result += fmt.Sprintf("  • %s [inline] (%s, %d bytes)\n",
				img.Filename, img.ContentType, img.Size)
		}
	}

	// Content
	result += fmt.Sprintf("\n📝 CONTENT\n")
	result += fmt.Sprintf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

	if content.CombinedText != "" {
		// Limit display for readability
		displayText := content.CombinedText
		if len(displayText) > 1500 {
			displayText = displayText[:1500] + "\n\n... [Content truncated for display] ..."
		}
		result += displayText
	} else {
		result += "[No readable content found]"
	}

	return result
}

// Helper functions for string manipulation (Go doesn't have these built-in)
func splitWords(text string) []string {
	return splitString(text, " ")
}

func joinWords(words []string) string {
	result := ""
	for i, word := range words {
		if i > 0 {
			result += " "
		}
		result += word
	}
	return result
}

func splitLines(text string) []string {
	return splitString(text, "\n")
}

func splitString(text, sep string) []string {
	if text == "" {
		return []string{}
	}

	var result []string
	current := ""

	for i := 0; i < len(text); i++ {
		if i+len(sep) <= len(text) && text[i:i+len(sep)] == sep {
			result = append(result, current)
			current = ""
			i += len(sep) - 1
		} else {
			current += string(text[i])
		}
	}

	if current != "" {
		result = append(result, current)
	}

	return result
}

func contains(text, substr string) bool {
	return len(text) >= len(substr) && indexOf(text, substr) >= 0
}

func indexOf(text, substr string) int {
	for i := 0; i <= len(text)-len(substr); i++ {
		if text[i:i+len(substr)] == substr {
			return i
		}
	}
	return -1
}
