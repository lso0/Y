package system

import (
	"os/exec"
	"strings"
)

type VPNInfo struct {
	IsConnected bool
	Icon        string
}

func GetVPNInfo() (*VPNInfo, error) {
	// Use mullvad status to get VPN information
	cmd := exec.Command("mullvad", "status")
	output, err := cmd.Output()
	if err != nil {
		// If mullvad command fails, assume VPN is not available/connected
		return &VPNInfo{
			IsConnected: false,
			Icon:        "○", // Empty circle for no VPN
		}, nil
	}

	outputStr := string(output)

	// Check if connected or disconnected
	isConnected := strings.Contains(strings.ToLower(outputStr), "connected")

	var icon string
	if isConnected {
		icon = "●" // Filled circle for connected
	} else {
		icon = "○" // Empty circle for disconnected
	}

	return &VPNInfo{
		IsConnected: isConnected,
		Icon:        icon,
	}, nil
}
