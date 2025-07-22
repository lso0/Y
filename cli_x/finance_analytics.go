package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// FinanceEvent represents a user action in the finance system
type FinanceEvent struct {
	ID          string                 `json:"id"`
	Timestamp   time.Time              `json:"timestamp"`
	Action      string                 `json:"action"` // add, delete, cancel, renew, edit, sort
	ServiceName string                 `json:"service_name,omitempty"`
	Category    string                 `json:"category,omitempty"`
	Amount      float64                `json:"amount,omitempty"`
	Recurrence  string                 `json:"recurrence,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
	UserContext ContextData            `json:"context"`
}

// ContextData captures the user's state during the action
type ContextData struct {
	TimeOfDay     string  `json:"time_of_day"`    // morning, afternoon, evening, night
	DayOfWeek     string  `json:"day_of_week"`    // monday, tuesday, etc.
	TotalServices int     `json:"total_services"` // number of services at time of action
	TotalMonthly  float64 `json:"total_monthly"`  // total monthly spend at time
	SessionLength int     `json:"session_length"` // how long user has been in app (minutes)
}

// FinanceAnalytics handles data collection and basic AI insights
type FinanceAnalytics struct {
	eventsFile string
	events     []FinanceEvent
}

// NewFinanceAnalytics creates a new analytics instance
func NewFinanceAnalytics() *FinanceAnalytics {
	return &FinanceAnalytics{
		eventsFile: "finance_analytics.jsonl", // JSON Lines format for easy streaming
		events:     make([]FinanceEvent, 0),
	}
}

// LogEvent records a user action for AI analysis
func (fa *FinanceAnalytics) LogEvent(action, serviceName string, amount float64, metadata map[string]interface{}) error {
	now := time.Now()

	event := FinanceEvent{
		ID:          fmt.Sprintf("%d", now.UnixNano()),
		Timestamp:   now,
		Action:      action,
		ServiceName: serviceName,
		Amount:      amount,
		Metadata:    metadata,
		UserContext: fa.buildContext(now),
	}

	// Append to JSONL file (each line is a JSON object)
	return fa.appendEventToFile(event)
}

// buildContext captures the current user/system state
func (fa *FinanceAnalytics) buildContext(timestamp time.Time) ContextData {
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

	return ContextData{
		TimeOfDay: timeOfDay,
		DayOfWeek: timestamp.Weekday().String(),
		// Additional context will be filled by the calling function
	}
}

// appendEventToFile saves event to JSONL file for AI processing
func (fa *FinanceAnalytics) appendEventToFile(event FinanceEvent) error {
	// Create analytics directory if it doesn't exist
	analyticsDir := "analytics"
	if err := os.MkdirAll(analyticsDir, 0755); err != nil {
		return fmt.Errorf("failed to create analytics directory: %w", err)
	}

	filePath := filepath.Join(analyticsDir, fa.eventsFile)

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

// GetRecentEvents loads recent events for AI analysis
func (fa *FinanceAnalytics) GetRecentEvents(days int) ([]FinanceEvent, error) {
	filePath := filepath.Join("analytics", fa.eventsFile)

	// Check if file exists
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		return []FinanceEvent{}, nil // No events yet
	}

	// Read all events (in production, we'd stream/paginate)
	data, err := os.ReadFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read analytics file: %w", err)
	}

	// Parse JSONL format
	var events []FinanceEvent
	cutoffTime := time.Now().AddDate(0, 0, -days)

	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		if strings.TrimSpace(line) == "" {
			continue
		}

		var event FinanceEvent
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

// GenerateInsights provides basic AI-driven insights
func (fa *FinanceAnalytics) GenerateInsights() (*FinanceInsights, error) {
	events, err := fa.GetRecentEvents(30) // Last 30 days
	if err != nil {
		return nil, err
	}

	insights := &FinanceInsights{
		TotalEvents:     len(events),
		GeneratedAt:     time.Now(),
		Patterns:        fa.analyzePatterns(events),
		Recommendations: fa.generateRecommendations(events),
	}

	return insights, nil
}

// FinanceInsights contains AI-generated insights
type FinanceInsights struct {
	TotalEvents     int                    `json:"total_events"`
	GeneratedAt     time.Time              `json:"generated_at"`
	Patterns        map[string]interface{} `json:"patterns"`
	Recommendations []string               `json:"recommendations"`
}

// analyzePatterns identifies user behavior patterns
func (fa *FinanceAnalytics) analyzePatterns(events []FinanceEvent) map[string]interface{} {
	patterns := make(map[string]interface{})

	// Analyze timing patterns
	timeDistribution := make(map[string]int)
	actionDistribution := make(map[string]int)

	for _, event := range events {
		timeDistribution[event.UserContext.TimeOfDay]++
		actionDistribution[event.Action]++
	}

	patterns["most_active_time"] = fa.findMostFrequent(timeDistribution)
	patterns["most_common_action"] = fa.findMostFrequent(actionDistribution)
	patterns["total_actions"] = len(events)
	patterns["time_distribution"] = timeDistribution
	patterns["action_distribution"] = actionDistribution

	return patterns
}

// generateRecommendations creates AI-driven suggestions
func (fa *FinanceAnalytics) generateRecommendations(events []FinanceEvent) []string {
	var recommendations []string

	// Count recent additions vs deletions
	addCount := 0
	deleteCount := 0
	cancelCount := 0

	for _, event := range events {
		switch event.Action {
		case "add":
			addCount++
		case "delete":
			deleteCount++
		case "cancel":
			cancelCount++
		}
	}

	// Generate smart recommendations based on patterns
	if addCount > deleteCount*2 {
		recommendations = append(recommendations,
			"📈 You've been adding many services lately. Consider reviewing your subscriptions to avoid overspending.")
	}

	if cancelCount > addCount {
		recommendations = append(recommendations,
			"✂️ Great job managing subscriptions! You're actively canceling unused services.")
	}

	if len(events) == 0 {
		recommendations = append(recommendations,
			"🚀 Start tracking your subscription management patterns to get personalized insights!")
	}

	return recommendations
}

// findMostFrequent finds the most frequent item in a map
func (fa *FinanceAnalytics) findMostFrequent(distribution map[string]int) string {
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
