//go:build windows

package main

import (
	"encoding/json"
	"fmt"
	"os/exec"
	"strings"
)

func collectSoftwareInventory() ([]SoftwareItem, error) {
	script := `
$ErrorActionPreference='SilentlyContinue'
$targets=@(
 @{Path='HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'; Source='registry-64'},
 @{Path='HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'; Source='registry-32'}
)
$items=@()
foreach($target in $targets){
 Get-ItemProperty $target.Path -ErrorAction SilentlyContinue |
  Where-Object { $_.DisplayName } |
  ForEach-Object {
   $items += [pscustomobject]@{
    name=[string]$_.DisplayName
    version=[string]$_.DisplayVersion
    publisher=[string]$_.Publisher
    source=$target.Source
   }
  }
}
@($items | Sort-Object name,version,publisher,source -Unique) | ConvertTo-Json -Compress -Depth 3
`

	cmd := exec.Command("powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script)
	out, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("software inventory collection failed: %w", err)
	}

	raw := strings.TrimSpace(string(out))
	if raw == "" || raw == "null" {
		return []SoftwareItem{}, nil
	}

	var apps []SoftwareItem
	if err := json.Unmarshal(out, &apps); err != nil {
		return nil, fmt.Errorf("software inventory JSON parse failed: %w", err)
	}

	result := make([]SoftwareItem, 0, len(apps))
	for _, app := range apps {
		app.Name = strings.TrimSpace(app.Name)
		if app.Name == "" {
			continue
		}
		app.Version = strings.TrimSpace(app.Version)
		app.Publisher = strings.TrimSpace(app.Publisher)
		app.Source = strings.TrimSpace(app.Source)
		result = append(result, app)
	}
	return result, nil
}
