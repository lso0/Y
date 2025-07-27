package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// TTSEngine handles text-to-speech functionality using Coqui TTS
type TTSEngine struct {
	available    bool
	model        string
	outputDir    string
	language     string
	speakingRate float64
}

// NewTTSEngine creates a new TTS engine instance
func NewTTSEngine() *TTSEngine {
	engine := &TTSEngine{
		model:        "tts_models/en/ljspeech/tacotron2-DDC", // Default English model
		outputDir:    "temp_audio",
		language:     "en",
		speakingRate: 1.0,
	}

	// Check if Coqui TTS is available
	engine.available = engine.checkTTSAvailability()

	// Create temp audio directory
	os.MkdirAll(engine.outputDir, 0755)

	return engine
}

// checkTTSAvailability checks if Coqui TTS is installed and available
func (tts *TTSEngine) checkTTSAvailability() bool {
	// Check if tts command is available
	_, err := exec.LookPath("tts")
	if err != nil {
		// Try pip installed version
		_, err = exec.LookPath("python3")
		if err != nil {
			return false
		}

		// Check if TTS Python package is installed
		cmd := exec.Command("python3", "-c", "import TTS; print('TTS available')")
		err = cmd.Run()
		return err == nil
	}
	return true
}

// IsAvailable returns whether TTS functionality is available
func (tts *TTSEngine) IsAvailable() bool {
	return tts.available
}

// InstallInstructions returns instructions for installing Coqui TTS
func (tts *TTSEngine) InstallInstructions() string {
	return `🔊 Text-to-Speech Setup Instructions:

1. Install Coqui TTS:
   pip install TTS

2. Or via conda:
   conda install -c conda-forge TTS

3. Verify installation:
   tts --help

4. Download models (first run will auto-download):
   tts --list_models

For more info: https://github.com/coqui-ai/TTS`
}

// SpeakText converts text to speech and plays it
func (tts *TTSEngine) SpeakText(text string) error {
	if !tts.available {
		return fmt.Errorf("TTS not available - run setup first")
	}

	// Clean and prepare text
	cleanText := tts.cleanTextForTTS(text)
	if cleanText == "" {
		return fmt.Errorf("no readable text content")
	}

	// Generate unique filename
	timestamp := time.Now().UnixNano()
	outputFile := filepath.Join(tts.outputDir, fmt.Sprintf("email_tts_%d.wav", timestamp))

	// Run TTS command
	cmd := exec.Command("tts",
		"--text", cleanText,
		"--model_name", tts.model,
		"--out_path", outputFile)

	if err := cmd.Run(); err != nil {
		return fmt.Errorf("TTS generation failed: %w", err)
	}

	// Play the generated audio
	return tts.playAudio(outputFile)
}

// SpeakEmailContent speaks the email subject and body
func (tts *TTSEngine) SpeakEmailContent(subject, from, content string) error {
	if !tts.available {
		return fmt.Errorf("TTS not available")
	}

	// Create a readable email announcement
	announcement := fmt.Sprintf("Email from %s. Subject: %s. Content: %s",
		from, subject, content)

	return tts.SpeakText(announcement)
}

// cleanTextForTTS prepares text for speech synthesis
func (tts *TTSEngine) cleanTextForTTS(text string) string {
	// Remove HTML tags if present
	text = strings.ReplaceAll(text, "<", " ")
	text = strings.ReplaceAll(text, ">", " ")

	// Replace multiple whitespaces with single space
	text = strings.Join(strings.Fields(text), " ")

	// Limit text length for reasonable speech duration (max 500 words)
	words := strings.Fields(text)
	if len(words) > 500 {
		text = strings.Join(words[:500], " ") + "... Email content truncated for speech."
	}

	// Remove special characters that might cause issues
	text = strings.ReplaceAll(text, "\"", "'")
	text = strings.ReplaceAll(text, "`", "'")

	return strings.TrimSpace(text)
}

// playAudio plays the generated audio file
func (tts *TTSEngine) playAudio(filePath string) error {
	var cmd *exec.Cmd

	// Try different audio players based on OS
	if _, err := exec.LookPath("afplay"); err == nil {
		// macOS
		cmd = exec.Command("afplay", filePath)
	} else if _, err := exec.LookPath("aplay"); err == nil {
		// Linux ALSA
		cmd = exec.Command("aplay", filePath)
	} else if _, err := exec.LookPath("paplay"); err == nil {
		// Linux PulseAudio
		cmd = exec.Command("paplay", filePath)
	} else if _, err := exec.LookPath("mpg123"); err == nil {
		// Generic player
		cmd = exec.Command("mpg123", filePath)
	} else {
		return fmt.Errorf("no audio player found (tried afplay, aplay, paplay, mpg123)")
	}

	// Play audio
	err := cmd.Run()

	// Clean up temporary file
	go func() {
		time.Sleep(1 * time.Second)
		os.Remove(filePath)
	}()

	return err
}

// StopSpeaking stops any current TTS playback
func (tts *TTSEngine) StopSpeaking() error {
	// Kill any running audio processes
	exec.Command("pkill", "afplay").Run()
	exec.Command("pkill", "aplay").Run()
	exec.Command("pkill", "paplay").Run()
	exec.Command("pkill", "mpg123").Run()

	return nil
}

// SetLanguage sets the TTS language
func (tts *TTSEngine) SetLanguage(lang string) {
	tts.language = lang

	// Update model based on language
	switch lang {
	case "en":
		tts.model = "tts_models/en/ljspeech/tacotron2-DDC"
	case "de":
		tts.model = "tts_models/de/thorsten/tacotron2-DDC"
	case "fr":
		tts.model = "tts_models/fr/mai/tacotron2-DDC"
	case "es":
		tts.model = "tts_models/es/mai/tacotron2-DDC"
	default:
		// Use multilingual model for other languages
		tts.model = "tts_models/multilingual/multi-dataset/xtts_v2"
	}
}

// GetAvailableVoices returns list of available TTS voices/models
func (tts *TTSEngine) GetAvailableVoices() ([]string, error) {
	if !tts.available {
		return nil, fmt.Errorf("TTS not available")
	}

	cmd := exec.Command("tts", "--list_models")
	output, err := cmd.Output()
	if err != nil {
		return nil, err
	}

	// Parse the model list
	lines := strings.Split(string(output), "\n")
	var models []string
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.Contains(line, "tts_models/") {
			models = append(models, line)
		}
	}

	return models, nil
}
