package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
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
		}

		if len(email.From) > 0 {
			if email.From[0].Name != "" {
				summary.From = email.From[0].Name
			} else {
				summary.From = email.From[0].Email
			}
		}

		if len(email.To) > 0 {
			if email.To[0].Name != "" {
				summary.To = email.To[0].Name
			} else {
				summary.To = email.To[0].Email
			}
		}

		summaries = append(summaries, summary)
	}

	return summaries, nil
}

func (c *EmailClient) getInboxID() (string, error) {
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
		if mailbox.Role == "inbox" {
			return mailbox.ID, nil
		}
	}

	return "", fmt.Errorf("inbox not found")
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
