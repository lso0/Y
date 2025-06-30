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
	Status       int    `yaml:"status"`
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
	if s.Status == 1 {
		return "Active"
	}
	return "Inactive"
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
		if service.Status == 1 {
			total += service.GetMonthlyCost()
		}
	}
	return total
}

func (data *FinanceData) GetTotalYearlyCost() float64 {
	total := 0.0
	for _, service := range data.Services {
		if service.Status == 1 {
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
