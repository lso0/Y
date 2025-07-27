package fm

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

type EmailSummary struct {
	ID       string
	Subject  string
	From     string
	To       string
	Date     time.Time
	Preview  string
	IsUnread bool
	// Enhanced fields for alias detection and mailbox management
	ToAlias    string   // The specific alias that received this email
	Recipients []string // All recipients
	Mailbox    string   // Which mailbox this email is in (inbox, spam, etc.)
}

type EmailClient struct {
	apiKey     string
	sessionURL string
	apiURL     string
	accountID  string
}

type JMAPSession struct {
	APIUrl          string                 `json:"apiUrl"`
	Accounts        map[string]JMAPAccount `json:"accounts"`
	PrimaryAccounts map[string]string      `json:"primaryAccounts"`
}

type JMAPAccount struct {
	Name string `json:"name"`
}

type JMAPRequest struct {
	Using       []string        `json:"using"`
	MethodCalls [][]interface{} `json:"methodCalls"`
}

type JMAPResponse struct {
	MethodResponses [][]interface{} `json:"methodResponses"`
}

type Mailbox struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	Role string `json:"role,omitempty"`
}

type MailboxGetResponse struct {
	List []Mailbox `json:"list"`
}

type EmailQueryResponse struct {
	IDs []string `json:"ids"`
}

type Email struct {
	ID         string          `json:"id"`
	Subject    string          `json:"subject"`
	From       []Address       `json:"from"`
	To         []Address       `json:"to"`
	ReceivedAt string          `json:"receivedAt"`
	Preview    string          `json:"preview"`
	Keywords   map[string]bool `json:"keywords"`
	BodyValues []interface{}   `json:"bodyValues"`
}

type Address struct {
	Name  string `json:"name"`
	Email string `json:"email"`
}

type EmailGetResponse struct {
	List []Email `json:"list"`
}

func NewEmailClient(apiKey string) (*EmailClient, error) {
	client := &EmailClient{
		apiKey:     apiKey,
		sessionURL: "https://api.fastmail.com/jmap/session",
	}

	if err := client.authenticate(); err != nil {
		return nil, err
	}

	return client, nil
}

func (c *EmailClient) authenticate() error {
	req, err := http.NewRequest("GET", c.sessionURL, nil)
	if err != nil {
		return err
	}

	req.Header.Set("Authorization", "Bearer "+c.apiKey)

	httpClient := &http.Client{}
	resp, err := httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return fmt.Errorf("authentication failed: %d", resp.StatusCode)
	}

	var session JMAPSession
	if err := json.NewDecoder(resp.Body).Decode(&session); err != nil {
		return err
	}

	c.apiURL = session.APIUrl
	c.accountID = session.PrimaryAccounts["urn:ietf:params:jmap:mail"]

	return nil
}

func (c *EmailClient) GetInboxEmails(limit int) ([]EmailSummary, error) {
	// First, get the inbox mailbox
	inboxID, err := c.getInboxID()
	if err != nil {
		return nil, err
	}

	// Query emails in inbox
	emailIDs, err := c.queryEmails(inboxID, limit)
	if err != nil {
		return nil, err
	}

	if len(emailIDs) == 0 {
		return []EmailSummary{}, nil
	}

	// Get email details
	emails, err := c.getEmails(emailIDs)
	if err != nil {
		return nil, err
	}

	// Convert to EmailSummary
	var summaries []EmailSummary
	for _, email := range emails {
		receivedAt, _ := time.Parse("2006-01-02T15:04:05Z", email.ReceivedAt)

		summary := EmailSummary{
			ID:       email.ID,
			Subject:  email.Subject,
			Preview:  email.Preview,
			Date:     receivedAt,
			IsUnread: !email.Keywords["$seen"],
			Mailbox:  "inbox", // Default mailbox - can be enhanced later
		}

		// Enhanced From field processing
		if len(email.From) > 0 {
			if email.From[0].Name != "" {
				summary.From = email.From[0].Name
			} else {
				summary.From = email.From[0].Email
			}
		}

		// Enhanced To field processing with alias detection
		var recipients []string
		var primaryRecipient string
		var detectedAlias string

		for _, addr := range email.To {
			recipients = append(recipients, addr.Email)

			// Detect FastMail aliases (typically contain the main domain)
			if addr.Email != "" {
				if primaryRecipient == "" {
					primaryRecipient = addr.Email
					detectedAlias = addr.Email
				}

				// Check if this looks like a FastMail alias
				if containsFastMailDomain(addr.Email) {
					detectedAlias = addr.Email
				}
			}
		}

		// Populate enhanced fields
		summary.Recipients = recipients
		summary.To = primaryRecipient
		summary.ToAlias = detectedAlias

		summaries = append(summaries, summary)
	}

	return summaries, nil
}

// Generic function to get emails from any mailbox
func (c *EmailClient) GetMailboxEmails(mailboxRole string, limit int) ([]EmailSummary, error) {
	// Get the specified mailbox
	mailboxID, err := c.getMailboxID(mailboxRole)
	if err != nil {
		return nil, err
	}

	// Query emails in the specified mailbox
	emailIDs, err := c.queryEmails(mailboxID, limit)
	if err != nil {
		return nil, err
	}

	if len(emailIDs) == 0 {
		return []EmailSummary{}, nil
	}

	// Get email details
	emails, err := c.getEmails(emailIDs)
	if err != nil {
		return nil, err
	}

	// Convert to EmailSummary with mailbox information
	var summaries []EmailSummary
	for _, email := range emails {
		receivedAt, _ := time.Parse("2006-01-02T15:04:05Z", email.ReceivedAt)

		summary := EmailSummary{
			ID:       email.ID,
			Subject:  email.Subject,
			Preview:  email.Preview,
			Date:     receivedAt,
			IsUnread: !email.Keywords["$seen"],
			Mailbox:  mailboxRole, // Set the specific mailbox
		}

		// Enhanced From field processing
		if len(email.From) > 0 {
			if email.From[0].Name != "" {
				summary.From = email.From[0].Name
			} else {
				summary.From = email.From[0].Email
			}
		}

		// Enhanced To field processing with alias detection
		var recipients []string
		var primaryRecipient string
		var detectedAlias string

		for _, addr := range email.To {
			recipients = append(recipients, addr.Email)

			// Detect FastMail aliases (typically contain the main domain)
			if addr.Email != "" {
				if primaryRecipient == "" {
					primaryRecipient = addr.Email
					detectedAlias = addr.Email
				}

				// Check if this looks like a FastMail alias
				if containsFastMailDomain(addr.Email) {
					detectedAlias = addr.Email
				}
			}
		}

		// Populate enhanced fields
		summary.Recipients = recipients
		summary.To = primaryRecipient
		summary.ToAlias = detectedAlias

		summaries = append(summaries, summary)
	}

	return summaries, nil
}

// DeleteEmail actually deletes an email from FastMail using JMAP API
func (c *EmailClient) DeleteEmail(emailID string) error {
	request := JMAPRequest{
		Using: []string{"urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"},
		MethodCalls: [][]interface{}{
			{"Email/set", map[string]interface{}{
				"accountId": c.accountID,
				"destroy":   []string{emailID},
			}, "0"},
		},
	}

	resp, err := c.makeRequest(request)
	if err != nil {
		return fmt.Errorf("failed to delete email: %w", err)
	}

	if len(resp.MethodResponses) == 0 {
		return fmt.Errorf("no response from server")
	}

	responseData := resp.MethodResponses[0][1].(map[string]interface{})

	// Check if deletion was successful
	if destroyed, ok := responseData["destroyed"].([]interface{}); ok {
		for _, destroyedID := range destroyed {
			if destroyedID.(string) == emailID {
				return nil // Successfully deleted
			}
		}
	}

	// Check for errors
	if notDestroyed, ok := responseData["notDestroyed"].(map[string]interface{}); ok {
		if errorInfo, exists := notDestroyed[emailID]; exists {
			return fmt.Errorf("failed to delete email: %v", errorInfo)
		}
	}

	return fmt.Errorf("email deletion status unknown")
}

// GetEmailDetails retrieves full email content for backup purposes
func (c *EmailClient) GetEmailDetails(emailID string) (*Email, error) {
	request := JMAPRequest{
		Using: []string{"urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"},
		MethodCalls: [][]interface{}{
			{"Email/get", map[string]interface{}{
				"accountId": c.accountID,
				"ids":       []string{emailID},
				"properties": []string{
					"id", "subject", "from", "to", "cc", "bcc",
					"receivedAt", "sentAt", "bodyValues", "bodyStructure",
					"preview", "keywords", "size", "threadId", "messageId",
					"headers", "textBody", "htmlBody", "attachments",
				},
			}, "0"},
		},
	}

	resp, err := c.makeRequest(request)
	if err != nil {
		return nil, err
	}

	if len(resp.MethodResponses) == 0 {
		return nil, fmt.Errorf("no response")
	}

	responseData := resp.MethodResponses[0][1].(map[string]interface{})
	var emailResp EmailGetResponse

	jsonData, _ := json.Marshal(responseData)
	json.Unmarshal(jsonData, &emailResp)

	if len(emailResp.List) == 0 {
		return nil, fmt.Errorf("email not found")
	}

	return &emailResp.List[0], nil
}

// GetFullEmailBody retrieves the complete readable text content of an email
func (c *EmailClient) GetFullEmailBody(emailID string) (string, error) {
	email, err := c.GetEmailDetails(emailID)
	if err != nil {
		return "", err
	}

	// Try to get text content from bodyValues if available
	if email.BodyValues != nil {
		for _, bodyValue := range email.BodyValues {
			if bodyText, ok := bodyValue.(map[string]interface{}); ok {
				if value, exists := bodyText["value"]; exists {
					if textContent, ok := value.(string); ok && textContent != "" {
						return textContent, nil
					}
				}
			}
		}
	}

	// Fallback to preview if no body content available
	return email.Preview, nil
}

func (c *EmailClient) getInboxID() (string, error) {
	return c.getMailboxID("inbox")
}

// Generic function to get mailbox ID by role
func (c *EmailClient) getMailboxID(role string) (string, error) {
	request := JMAPRequest{
		Using: []string{"urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"},
		MethodCalls: [][]interface{}{
			{"Mailbox/get", map[string]interface{}{
				"accountId": c.accountID,
			}, "0"},
		},
	}

	resp, err := c.makeRequest(request)
	if err != nil {
		return "", err
	}

	if len(resp.MethodResponses) == 0 {
		return "", fmt.Errorf("no response")
	}

	responseData := resp.MethodResponses[0][1].(map[string]interface{})
	var mailboxResp MailboxGetResponse

	jsonData, _ := json.Marshal(responseData)
	json.Unmarshal(jsonData, &mailboxResp)

	for _, mailbox := range mailboxResp.List {
		if mailbox.Role == role {
			return mailbox.ID, nil
		}
	}

	return "", fmt.Errorf("%s mailbox not found", role)
}

func (c *EmailClient) queryEmails(mailboxID string, limit int) ([]string, error) {
	request := JMAPRequest{
		Using: []string{"urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"},
		MethodCalls: [][]interface{}{
			{"Email/query", map[string]interface{}{
				"accountId": c.accountID,
				"filter": map[string]interface{}{
					"inMailbox": mailboxID,
				},
				"sort": []map[string]interface{}{
					{
						"property":    "receivedAt",
						"isAscending": false,
					},
				},
				"limit": limit,
			}, "0"},
		},
	}

	resp, err := c.makeRequest(request)
	if err != nil {
		return nil, err
	}

	if len(resp.MethodResponses) == 0 {
		return nil, fmt.Errorf("no response")
	}

	responseData := resp.MethodResponses[0][1].(map[string]interface{})
	var queryResp EmailQueryResponse

	jsonData, _ := json.Marshal(responseData)
	json.Unmarshal(jsonData, &queryResp)

	return queryResp.IDs, nil
}

func (c *EmailClient) getEmails(emailIDs []string) ([]Email, error) {
	request := JMAPRequest{
		Using: []string{"urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"},
		MethodCalls: [][]interface{}{
			{"Email/get", map[string]interface{}{
				"accountId": c.accountID,
				"ids":       emailIDs,
				"properties": []string{
					"id", "subject", "from", "to", "receivedAt", "preview", "keywords",
				},
			}, "0"},
		},
	}

	resp, err := c.makeRequest(request)
	if err != nil {
		return nil, err
	}

	if len(resp.MethodResponses) == 0 {
		return nil, fmt.Errorf("no response")
	}

	responseData := resp.MethodResponses[0][1].(map[string]interface{})
	var emailResp EmailGetResponse

	jsonData, _ := json.Marshal(responseData)
	json.Unmarshal(jsonData, &emailResp)

	return emailResp.List, nil
}

func (c *EmailClient) makeRequest(request JMAPRequest) (*JMAPResponse, error) {
	jsonData, err := json.Marshal(request)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest("POST", c.apiURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Authorization", "Bearer "+c.apiKey)
	req.Header.Set("Content-Type", "application/json")

	httpClient := &http.Client{}
	resp, err := httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed: %d - %s", resp.StatusCode, string(body))
	}

	var jmapResp JMAPResponse
	if err := json.NewDecoder(resp.Body).Decode(&jmapResp); err != nil {
		return nil, err
	}

	return &jmapResp, nil
}

// Helper function to detect FastMail domains and aliases
func containsFastMailDomain(email string) bool {
	// Common FastMail domains and patterns
	fastmailDomains := []string{
		"fastmail.com",
		"fastmail.fm",
		"fastmail.net",
		"fastmail.org",
		"messagingengine.com",
		"123mail.org",
		"airpost.net",
		"eml.cc",
		"fmail.co.uk",
		"fmgirl.com",
		"fmguy.com",
		"mailmight.com",
		"ml1.net",
		"mm.st",
		"myfastmail.com",
		"proinbox.com",
		"promessage.com",
		"rushpost.com",
		"sent.as",
		"sent.at",
		"sent.com",
		"speedymail.org",
		"warpmail.net",
	}

	emailLower := strings.ToLower(email)
	for _, domain := range fastmailDomains {
		if strings.Contains(emailLower, "@"+domain) {
			return true
		}
	}

	return false
}
