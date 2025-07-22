package main

import (
	"fmt"
	"io/ioutil"
	"sort"
	"strings"
	"time"

	"gopkg.in/yaml.v3"
)

type FinanceData struct {
	Services []Service `yaml:"services"`
}

type Service struct {
	Name         string `yaml:"name"`
	Tags         string `yaml:"tags"`
	Prices       Prices `yaml:"prices"`
	Recurrence   string `yaml:"recurrence"`
	RenewalDate  string `yaml:"renewal_date"`
	Status       int    `yaml:"status"` // Keep for backward compatibility
	State        string `yaml:"state"`  // New: "active", "cancelled", "inactive"
	Student      bool   `yaml:"student"`
	TrialEndDate string `yaml:"trial_end_date"`
	BankService  string `yaml:"bank_service"`
	Card         string `yaml:"card"`
	Account      string `yaml:"account"`
}

type Prices struct {
	Currency string  `yaml:"currency"`
	CMonthly float64 `yaml:"c_monthly"`
	CYearly  float64 `yaml:"c_yearly"`
}

func loadFinanceData() (*FinanceData, error) {
	data, err := ioutil.ReadFile("data/finance.yaml")
	if err != nil {
		return nil, err
	}

	var financeData FinanceData
	err = yaml.Unmarshal(data, &financeData)
	if err != nil {
		return nil, err
	}

	// Ensure state consistency for all services (backward compatibility)
	for i := range financeData.Services {
		financeData.Services[i].EnsureStateConsistency()
	}

	return &financeData, nil
}

func saveFinanceData(data *FinanceData) error {
	yamlData, err := yaml.Marshal(data)
	if err != nil {
		return err
	}

	return ioutil.WriteFile("data/finance.yaml", yamlData, 0644)
}

func (s *Service) GetMonthlyCost() float64 {
	if s.Prices.CMonthly > 0 {
		return s.Prices.CMonthly
	}

	switch s.Recurrence {
	case "Y":
		return s.Prices.CYearly / 12
	case "2Y":
		return s.Prices.CYearly / 24
	default:
		return s.Prices.CMonthly
	}
}

func (s *Service) GetYearlyCost() float64 {
	if s.Prices.CYearly > 0 {
		return s.Prices.CYearly
	}

	return s.Prices.CMonthly * 12
}

func (s *Service) GetStatusText() string {
	// Use new State field if available, otherwise fall back to Status
	if s.State != "" {
		switch s.State {
		case "active":
			return "Active"
		case "cancelled":
			return "Cancelled"
		case "inactive":
			return "Inactive"
		default:
			return "Unknown"
		}
	}

	// Backward compatibility with old Status field
	if s.Status == 1 {
		return "Active"
	}
	return "Inactive"
}

func (s *Service) IsActive() bool {
	// Use new State field if available, otherwise fall back to Status
	if s.State != "" {
		return s.State == "active"
	}

	// Backward compatibility with old Status field
	return s.Status == 1
}

func (s *Service) IsCancelled() bool {
	return s.State == "cancelled"
}

func (s *Service) SetActive() {
	s.State = "active"
	s.Status = 1 // Keep old field in sync
}

func (s *Service) SetCancelled() {
	s.State = "cancelled"
	s.Status = 0 // Keep old field in sync
}

func (s *Service) SetInactive() {
	s.State = "inactive"
	s.Status = 0 // Keep old field in sync
}

func (s *Service) EnsureStateConsistency() {
	// If State is empty, initialize from Status for backward compatibility
	if s.State == "" {
		if s.Status == 1 {
			s.State = "active"
		} else {
			s.State = "inactive"
		}
	}
}

func (s *Service) GetRenewalInfo() string {
	renewalDate, err := time.Parse("2006-01-02", s.RenewalDate)
	if err != nil {
		return s.RenewalDate
	}

	now := time.Now()
	days := int(renewalDate.Sub(now).Hours() / 24)

	if days < 0 {
		return fmt.Sprintf("Expired %d days ago", -days)
	} else if days == 0 {
		return "Expires today"
	} else if days <= 30 {
		return fmt.Sprintf("Expires in %d days", days)
	} else {
		return renewalDate.Format("Jan 2, 2006")
	}
}

func (s *Service) GetStatusIndicator() string {
	renewalDate, err := time.Parse("2006-01-02", s.RenewalDate)
	if err != nil {
		return "●" // Default gray dot if date parsing fails
	}

	now := time.Now()
	days := int(renewalDate.Sub(now).Hours() / 24)

	if days < 0 {
		return "🔴" // Red - expired
	} else if days <= 7 {
		return "🟠" // Orange - expires soon (within 7 days)
	} else {
		return "🟢" // Green - OK (more than 7 days)
	}
}

func formatCurrency(amount float64, currency string) string {
	return fmt.Sprintf("%.2f %s", amount, currency)
}

func (data *FinanceData) GetServicesByTag(tag string) []Service {
	var services []Service
	for _, service := range data.Services {
		if tag == "" || strings.EqualFold(service.Tags, tag) {
			services = append(services, service)
		}
	}
	return services
}

func (data *FinanceData) GetTotalMonthlyCost() float64 {
	total := 0.0
	for _, service := range data.Services {
		if service.IsActive() {
			total += service.GetMonthlyCost()
		}
	}
	return total
}

func (data *FinanceData) GetTotalYearlyCost() float64 {
	total := 0.0
	for _, service := range data.Services {
		if service.IsActive() {
			total += service.GetYearlyCost()
		}
	}
	return total
}

func (data *FinanceData) GetCategories() []string {
	tagMap := make(map[string]bool)
	for _, service := range data.Services {
		tagMap[service.Tags] = true
	}

	var categories []string
	for tag := range tagMap {
		categories = append(categories, tag)
	}

	sort.Strings(categories)
	return categories
}

func (data *FinanceData) AddService(service Service) {
	data.Services = append(data.Services, service)
}

func (data *FinanceData) UpdateService(index int, service Service) error {
	if index < 0 || index >= len(data.Services) {
		return fmt.Errorf("index out of range")
	}
	data.Services[index] = service
	return nil
}

func (data *FinanceData) DeleteService(index int) error {
	if index < 0 || index >= len(data.Services) {
		return fmt.Errorf("index out of range")
	}
	data.Services = append(data.Services[:index], data.Services[index+1:]...)
	return nil
}

func (data *FinanceData) CancelService(index int) error {
	if index < 0 || index >= len(data.Services) {
		return fmt.Errorf("index out of range")
	}
	data.Services[index].SetCancelled()
	return nil
}

func (data *FinanceData) ActivateService(index int) error {
	if index < 0 || index >= len(data.Services) {
		return fmt.Errorf("index out of range")
	}
	data.Services[index].SetActive()
	return nil
}

func (data *FinanceData) GetActiveServices() []Service {
	var activeServices []Service
	for _, service := range data.Services {
		if service.IsActive() {
			activeServices = append(activeServices, service)
		}
	}
	return activeServices
}

func (data *FinanceData) GetCancelledServices() []Service {
	var cancelledServices []Service
	for _, service := range data.Services {
		if service.IsCancelled() {
			cancelledServices = append(cancelledServices, service)
		}
	}
	return cancelledServices
}

func (data *FinanceData) GetServiceCount() (active, cancelled, total int) {
	for _, service := range data.Services {
		if service.IsActive() {
			active++
		} else if service.IsCancelled() {
			cancelled++
		}
		total++
	}
	return active, cancelled, total
}
