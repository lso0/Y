package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// EmailEvent represents a user action in the email system
type EmailEvent struct {
	ID          string                 `json:"id"`
	Timestamp   time.Time              `json:"timestamp"`
	Action      string                 `json:"action"` // read, delete, reply, archive, mark_spam, switch_mailbox
	MessageID   string                 `json:"message_id,omitempty"`
	Sender      string                 `json:"sender,omitempty"`
	Subject     string                 `json:"subject,omitempty"`
	ToAlias     string                 `json:"to_alias,omitempty"`          // Which email alias received this
	Mailbox     string                 `json:"mailbox,omitempty"`           // inbox, spam, trash
	ReadTime    int                    `json:"read_time_seconds,omitempty"` // How long email was viewed
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
	UserContext EmailContextData       `json:"context"`
}

// EmailContextData captures the user's state during the email action
type EmailContextData struct {
	TimeOfDay      string `json:"time_of_day"`     // morning, afternoon, evening, night
	DayOfWeek      string `json:"day_of_week"`     // monday, tuesday, etc.
	InboxCount     int    `json:"inbox_count"`     // number of emails in inbox
	CurrentMailbox string `json:"current_mailbox"` // which mailbox user is viewing
	SessionLength  int    `json:"session_length"`  // how long user has been in email app (minutes)
}

// EmailAnalytics handles email data collection and insights
type EmailAnalytics struct {
	eventsFile    string
	events        []EmailEvent
	sessionStart  time.Time      // When FastMail session started
	lastActivity  time.Time      // Last user activity
	timeInMailbox map[string]int // Time spent in each mailbox (seconds)
	actionCounts  map[string]int // Count of each action type
	dailyUsage    map[string]int // Usage by day
}

// NewEmailAnalytics creates a new email analytics instance with enhanced tracking
func NewEmailAnalytics() *EmailAnalytics {
	return &EmailAnalytics{
		eventsFile:    "analytics/email_analytics.jsonl", // Store in analytics directory
		events:        make([]EmailEvent, 0),
		sessionStart:  time.Now(),
		lastActivity:  time.Now(),
		timeInMailbox: make(map[string]int),
		actionCounts:  make(map[string]int),
		dailyUsage:    make(map[string]int),
	}
}

// LogEmailEvent records a user email action for AI analysis with enhanced tracking
func (ea *EmailAnalytics) LogEmailEvent(action, messageID, sender, subject, toAlias, mailbox string, metadata map[string]interface{}) error {
	now := time.Now()

	// Update session tracking
	ea.updateSessionTracking(action, mailbox, now)

	event := EmailEvent{
		ID:          fmt.Sprintf("email_%d", now.UnixNano()),
		Timestamp:   now,
		Action:      action,
		MessageID:   messageID,
		Sender:      sender,
		Subject:     subject,
		ToAlias:     toAlias,
		Mailbox:     mailbox,
		Metadata:    metadata,
		UserContext: ea.buildEmailContext(now, mailbox),
	}

	// Append to JSONL file
	return ea.appendEventToFile(event)
}

// updateSessionTracking tracks time spent and usage patterns
func (ea *EmailAnalytics) updateSessionTracking(action, mailbox string, timestamp time.Time) {
	// Track time spent in current mailbox
	if ea.lastActivity.After(ea.sessionStart) {
		timeSpent := int(timestamp.Sub(ea.lastActivity).Seconds())
		ea.timeInMailbox[mailbox] += timeSpent
	}

	// Update activity counters
	ea.actionCounts[action]++
	dayKey := timestamp.Format("2006-01-02")
	ea.dailyUsage[dayKey]++

	// Update last activity time
	ea.lastActivity = timestamp
}

// GetSessionData returns current session analytics for context
func (ea *EmailAnalytics) GetSessionData() map[string]interface{} {
	sessionLength := int(time.Since(ea.sessionStart).Minutes())

	return map[string]interface{}{
		"session_start":   ea.sessionStart,
		"session_length":  sessionLength,
		"time_in_mailbox": ea.timeInMailbox,
		"action_counts":   ea.actionCounts,
		"daily_usage":     ea.dailyUsage,
		"last_activity":   ea.lastActivity,
	}
}

// LogSessionEnd records when user exits FastMail for comprehensive session data
func (ea *EmailAnalytics) LogSessionEnd() error {
	sessionData := ea.GetSessionData()

	return ea.LogEmailEvent("session_end", "", "", "", "", "", map[string]interface{}{
		"session_data":  sessionData,
		"total_actions": ea.getTotalActions(),
	})
}

// getTotalActions returns total number of actions in this session
func (ea *EmailAnalytics) getTotalActions() int {
	total := 0
	for _, count := range ea.actionCounts {
		total += count
	}
	return total
}

// buildEmailContext captures the current email/system state
func (ea *EmailAnalytics) buildEmailContext(timestamp time.Time, currentMailbox string) EmailContextData {
	hour := timestamp.Hour()
	var timeOfDay string
	switch {
	case hour < 6:
		timeOfDay = "night"
	case hour < 12:
		timeOfDay = "morning"
	case hour < 18:
		timeOfDay = "afternoon"
	default:
		timeOfDay = "evening"
	}

	return EmailContextData{
		TimeOfDay:      timeOfDay,
		DayOfWeek:      timestamp.Weekday().String(),
		CurrentMailbox: currentMailbox,
		// Additional context will be filled by the calling function
	}
}

// appendEventToFile saves event to JSONL file for AI processing
func (ea *EmailAnalytics) appendEventToFile(event EmailEvent) error {
	// Create analytics directory if it doesn't exist
	analyticsDir := "analytics"
	if err := os.MkdirAll(analyticsDir, 0755); err != nil {
		return fmt.Errorf("failed to create analytics directory: %w", err)
	}

	filePath := filepath.Join(analyticsDir, ea.eventsFile)

	// Open file for appending (create if doesn't exist)
	file, err := os.OpenFile(filePath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return fmt.Errorf("failed to open analytics file: %w", err)
	}
	defer file.Close()

	// Convert event to JSON and append as a line
	eventJSON, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("failed to marshal event: %w", err)
	}

	// Write JSON line
	if _, err := file.Write(append(eventJSON, '\n')); err != nil {
		return fmt.Errorf("failed to write event: %w", err)
	}

	return nil
}

// GetRecentEmailEvents loads recent email events for AI analysis
func (ea *EmailAnalytics) GetRecentEmailEvents(days int) ([]EmailEvent, error) {
	filePath := filepath.Join("analytics", ea.eventsFile)

	// Check if file exists
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		return []EmailEvent{}, nil // No events yet
	}

	// Read all events (in production, we'd stream/paginate)
	data, err := os.ReadFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read analytics file: %w", err)
	}

	// Parse JSONL format
	var events []EmailEvent
	cutoffTime := time.Now().AddDate(0, 0, -days)

	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		if strings.TrimSpace(line) == "" {
			continue
		}

		var event EmailEvent
		if err := json.Unmarshal([]byte(line), &event); err != nil {
			continue // Skip malformed lines
		}

		// Only include recent events
		if event.Timestamp.After(cutoffTime) {
			events = append(events, event)
		}
	}

	return events, nil
}

// GenerateEmailInsights provides AI-driven email insights
func (ea *EmailAnalytics) GenerateEmailInsights() (*EmailInsights, error) {
	events, err := ea.GetRecentEmailEvents(30) // Last 30 days
	if err != nil {
		return nil, err
	}

	insights := &EmailInsights{
		TotalEvents:     len(events),
		GeneratedAt:     time.Now(),
		Patterns:        ea.analyzeEmailPatterns(events),
		Recommendations: ea.generateEmailRecommendations(events),
	}

	return insights, nil
}

// EmailInsights contains AI-generated email insights
type EmailInsights struct {
	TotalEvents     int                    `json:"total_events"`
	GeneratedAt     time.Time              `json:"generated_at"`
	Patterns        map[string]interface{} `json:"patterns"`
	Recommendations []string               `json:"recommendations"`
}

// analyzeEmailPatterns identifies user email behavior patterns
func (ea *EmailAnalytics) analyzeEmailPatterns(events []EmailEvent) map[string]interface{} {
	patterns := make(map[string]interface{})

	// Analyze timing and action patterns
	timeDistribution := make(map[string]int)
	actionDistribution := make(map[string]int)
	senderFrequency := make(map[string]int)
	aliasDistribution := make(map[string]int)

	for _, event := range events {
		timeDistribution[event.UserContext.TimeOfDay]++
		actionDistribution[event.Action]++
		if event.Sender != "" {
			senderFrequency[event.Sender]++
		}
		if event.ToAlias != "" {
			aliasDistribution[event.ToAlias]++
		}
	}

	patterns["most_active_time"] = ea.findMostFrequent(timeDistribution)
	patterns["most_common_action"] = ea.findMostFrequent(actionDistribution)
	patterns["most_contacted_sender"] = ea.findMostFrequent(senderFrequency)
	patterns["most_used_alias"] = ea.findMostFrequent(aliasDistribution)
	patterns["total_actions"] = len(events)
	patterns["time_distribution"] = timeDistribution
	patterns["action_distribution"] = actionDistribution

	return patterns
}

// generateEmailRecommendations creates AI-driven email suggestions
func (ea *EmailAnalytics) generateEmailRecommendations(events []EmailEvent) []string {
	var recommendations []string

	// Count different types of actions
	readCount := 0
	deleteCount := 0
	replyCount := 0

	for _, event := range events {
		switch event.Action {
		case "read":
			readCount++
		case "delete":
			deleteCount++
		case "reply":
			replyCount++
		}
	}

	// Generate smart recommendations based on email patterns
	if deleteCount > readCount/2 {
		recommendations = append(recommendations,
			"🗑️ You delete many emails. Consider setting up filters to auto-archive newsletters and promotions.")
	}

	if replyCount > 0 && readCount > 0 {
		replyRate := float64(replyCount) / float64(readCount) * 100
		if replyRate > 50 {
			recommendations = append(recommendations,
				fmt.Sprintf("⚡ High reply rate (%.1f%%). Consider templates for common responses.", replyRate))
		}
	}

	if len(events) == 0 {
		recommendations = append(recommendations,
			"📧 Start using your email system to get personalized AI insights and automation suggestions!")
	}

	return recommendations
}

// findMostFrequent finds the most frequent item in a map (helper function)
func (ea *EmailAnalytics) findMostFrequent(distribution map[string]int) string {
	maxCount := 0
	mostFrequent := ""

	for item, count := range distribution {
		if count > maxCount {
			maxCount = count
			mostFrequent = item
		}
	}

	return mostFrequent
}
