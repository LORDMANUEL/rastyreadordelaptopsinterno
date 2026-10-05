//go:build windows

package main

import (
	"encoding/json"
	"os/exec"
	"strconv"
	"strings"
)

type inventoryJSON struct {
	Serial string `json:"serial"`
	OSVersion string `json:"os_version"`
	Manufacturer string `json:"manufacturer"`
	Model string `json:"model"`
	HardwareUUID string `json:"hardware_uuid"`
	WiFiSSID string `json:"wifi_ssid"`
	BatteryPercent *int `json:"battery_percent"`
	BitLockerStatus string `json:"bitlocker_status"`
	TPMStatus string `json:"tpm_status"`
	AntivirusStatus string `json:"antivirus_status"`
}

func collectInventory() Inventory {
	script := `
$ErrorActionPreference='SilentlyContinue'
$cs=Get-CimInstance Win32_ComputerSystem
$bios=Get-CimInstance Win32_BIOS
$os=Get-CimInstance Win32_OperatingSystem
$csp=Get-CimInstance Win32_ComputerSystemProduct
$b=Get-CimInstance Win32_Battery | Select-Object -First 1
$bl=(Get-BitLockerVolume -MountPoint $env:SystemDrive).ProtectionStatus
$tpm=Get-Tpm
$av=(Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | Select-Object -ExpandProperty displayName) -join ', '
$ssid=((netsh wlan show interfaces) | Select-String '^\s*SSID\s*:' | Select-Object -First 1).ToString().Split(':',2)[1].Trim()
[pscustomobject]@{
 serial=$bios.SerialNumber
 os_version=($os.Caption+' '+$os.Version)
 manufacturer=$cs.Manufacturer
 model=$cs.Model
 hardware_uuid=$csp.UUID
 wifi_ssid=$ssid
 battery_percent=if($b){[int]$b.EstimatedChargeRemaining}else{$null}
 bitlocker_status=[string]$bl
 tpm_status=if($tpm){'Present='+$tpm.TpmPresent+';Ready='+$tpm.TpmReady}else{''}
 antivirus_status=$av
} | ConvertTo-Json -Compress
`
	cmd := exec.Command("powershell", "-NoProfile", "-NonInteractive", "-Command", script)
	out, err := cmd.Output()
	if err != nil { return Inventory{} }
	var parsed inventoryJSON
	if json.Unmarshal(out, &parsed) != nil { return Inventory{} }
	return Inventory{
		Serial: strings.TrimSpace(parsed.Serial),
		OSVersion: strings.TrimSpace(parsed.OSVersion),
		Manufacturer: strings.TrimSpace(parsed.Manufacturer),
		Model: strings.TrimSpace(parsed.Model),
		HardwareUUID: strings.TrimSpace(parsed.HardwareUUID),
		WiFiSSID: strings.TrimSpace(parsed.WiFiSSID),
		BatteryPercent: parsed.BatteryPercent,
		BitLockerStatus: normalizeBitLocker(parsed.BitLockerStatus),
		TPMStatus: strings.TrimSpace(parsed.TPMStatus),
		AntivirusStatus: strings.TrimSpace(parsed.AntivirusStatus),
	}
}

func normalizeBitLocker(v string) string {
	v = strings.TrimSpace(v)
	if n, err := strconv.Atoi(v); err == nil {
		if n == 1 { return "On" }
		if n == 0 { return "Off" }
	}
	return v
}
