package system

import (
	"os/exec"
	"regexp"
	"strconv"
	"strings"
)

type BatteryInfo struct {
	Percentage int
	IsCharging bool
	Icon       string
}

func GetBatteryInfo() (*BatteryInfo, error) {
	// Use pmset to get battery information on macOS
	cmd := exec.Command("pmset", "-g", "batt")
	output, err := cmd.Output()
	if err != nil {
		return nil, err
	}

	outputStr := string(output)

	// Parse battery percentage
	percentageRegex := regexp.MustCompile(`(\d+)%`)
	percentageMatch := percentageRegex.FindStringSubmatch(outputStr)

	var percentage int
	if len(percentageMatch) > 1 {
		percentage, _ = strconv.Atoi(percentageMatch[1])
	}

	// Check if charging
	isCharging := strings.Contains(outputStr, "AC Power")

	// Determine battery icon based on percentage and charging status
	var icon string
	if isCharging {
		icon = "⚡" // Charging icon
	} else if percentage >= 75 {
		icon = "▓" // Full battery
	} else if percentage >= 50 {
		icon = "▒" // Good battery
	} else if percentage >= 25 {
		icon = "░" // Medium battery
	} else {
		icon = "▁" // Low battery
	}

	return &BatteryInfo{
		Percentage: percentage,
		IsCharging: isCharging,
		Icon:       icon,
	}, nil
}
