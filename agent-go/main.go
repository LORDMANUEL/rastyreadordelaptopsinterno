package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

const agentVersion = "0.6.0"

type Config struct {
	ServerURL        string `json:"server_url"`
	EnrollmentToken  string `json:"enrollment_token,omitempty"`
	DeviceID         string `json:"device_id,omitempty"`
	DeviceToken      string `json:"device_token,omitempty"`
	HeartbeatSeconds int    `json:"heartbeat_seconds,omitempty"`
	SoftwareSyncAt   string `json:"software_sync_at,omitempty"`
}

type Inventory struct {
	Username        string
	Serial          string
	OSVersion       string
	Manufacturer    string
	Model           string
	HardwareUUID    string
	WiFiSSID        string
	BatteryPercent  *int
	BitLockerStatus string
	TPMStatus       string
	AntivirusStatus string
}

type EnrollRequest struct {
	EnrollmentToken string `json:"enrollment_token"`
	Hostname        string `json:"hostname"`
	Serial          string `json:"serial,omitempty"`
	Platform        string `json:"platform"`
	OSVersion       string `json:"os_version,omitempty"`
	Architecture    string `json:"architecture,omitempty"`
	AgentVersion    string `json:"agent_version"`
	Manufacturer    string `json:"manufacturer,omitempty"`
	Model           string `json:"model,omitempty"`
	HardwareUUID    string `json:"hardware_uuid,omitempty"`
}

type EnrollResponse struct {
	DeviceID         string `json:"device_id"`
	DeviceToken      string `json:"device_token"`
	HeartbeatSeconds int    `json:"heartbeat_seconds"`
}

type HeartbeatRequest struct {
	Username        string `json:"username,omitempty"`
	LANIP           string `json:"lan_ip,omitempty"`
	Hostname        string `json:"hostname,omitempty"`
	Serial          string `json:"serial,omitempty"`
	OSVersion       string `json:"os_version,omitempty"`
	Architecture    string `json:"architecture,omitempty"`
	AgentVersion    string `json:"agent_version"`
	WiFiSSID        string `json:"wifi_ssid,omitempty"`
	Manufacturer    string `json:"manufacturer,omitempty"`
	Model           string `json:"model,omitempty"`
	HardwareUUID    string `json:"hardware_uuid,omitempty"`
	BatteryPercent  *int   `json:"battery_percent,omitempty"`
	BitLockerStatus string `json:"bitlocker_status,omitempty"`
	TPMStatus       string `json:"tpm_status,omitempty"`
	AntivirusStatus string `json:"antivirus_status,omitempty"`
}

type HeartbeatResponse struct {
	OK                   bool   `json:"ok"`
	LostMode             bool   `json:"lost_mode"`
	NextHeartbeatSeconds int    `json:"next_heartbeat_seconds"`
	DeviceToken          string `json:"device_token,omitempty"`
}

type SoftwareItem struct {
	Name      string `json:"name"`
	Version   string `json:"version,omitempty"`
	Publisher string `json:"publisher,omitempty"`
	Source    string `json:"source,omitempty"`
}

type SoftwareInventoryRequest struct {
	Applications []SoftwareItem `json:"applications"`
}

type SoftwareInventoryResponse struct {
	OK      bool `json:"ok"`
	Present int  `json:"present"`
	Added   int  `json:"added"`
	Removed int  `json:"removed"`
}

func main() {
	handled, err := handlePlatformCommand(os.Args[1:])
	if handled {
		if err != nil {
			fatal(err)
		}
		return
	}
	if err := runPlatform(agentLoop); err != nil {
		fatal(err)
	}
}

func agentLoop(ctx context.Context) error {
	cfgPath := configPath()
	cfg, err := loadConfig(cfgPath)
	if err != nil {
		return err
	}
	if cfg.DeviceToken == "" {
		if err := enroll(&cfg); err != nil {
			return fmt.Errorf("initial enrollment failed: %w", err)
		}
		if err := saveConfig(cfgPath, cfg); err != nil {
			return fmt.Errorf("save enrolled config: %w", err)
		}
	}

	for {
		next, rotated, err := heartbeat(&cfg)
		dirtyConfig := rotated
		if err != nil {
			logLine("heartbeat error: %v", err)
			next = 60
		} else {
			if err := syncSoftwareTasks(cfg); err != nil {
				logLine("software task sync error: %v", err)
			}
			if softwareSyncDue(cfg) {
				if err := syncSoftwareInventory(cfg); err != nil {
					logLine("software inventory sync error: %v", err)
				} else {
					cfg.SoftwareSyncAt = time.Now().UTC().Format(time.RFC3339)
					dirtyConfig = true
				}
			}
		}

		if dirtyConfig {
			if err := saveConfig(cfgPath, cfg); err != nil {
				logLine("cannot persist agent configuration: %v", err)
				next = 60
			}
		}

		if next < 30 {
			next = 30
		}

		timer := time.NewTimer(time.Duration(next) * time.Second)
		select {
		case <-ctx.Done():
			timer.Stop()
			return nil
		case <-timer.C:
		}
	}
}

func configPath() string {
	if p := os.Getenv("YUDE_ASSET_GUARD_CONFIG"); p != "" {
		return p
	}
	base := os.Getenv("ProgramData")
	if base == "" {
		base = "."
	}
	return filepath.Join(base, "YUDEAssetGuard", "config.json")
}

func loadConfig(path string) (Config, error) {
	var cfg Config
	raw, err := os.ReadFile(path)
	if err != nil {
		return cfg, fmt.Errorf("cannot read %s: %w", path, err)
	}
	if err := json.Unmarshal(raw, &cfg); err != nil {
		return cfg, fmt.Errorf("invalid config JSON: %w", err)
	}
	cfg.ServerURL = strings.TrimRight(strings.TrimSpace(cfg.ServerURL), "/")
	if cfg.ServerURL == "" {
		return cfg, errors.New("server_url is required")
	}
	if runtime.GOOS == "windows" && !strings.HasPrefix(strings.ToLower(cfg.ServerURL), "https://") {
		return cfg, errors.New("server_url must use HTTPS on Windows")
	}
	return cfg, nil
}

func saveConfig(path string, cfg Config) error {
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(path, raw, 0600); err != nil {
		return err
	}
	return secureConfigFile(path)
}

func enroll(cfg *Config) error {
	if cfg.EnrollmentToken == "" {
		return errors.New("enrollment_token is required for first registration")
	}
	host, _ := os.Hostname()
	inv := collectInventory()
	if runtime.GOOS == "windows" {
		if err := validateInventory(inv); err != nil {
			return err
		}
	}

	payload := EnrollRequest{
		EnrollmentToken: cfg.EnrollmentToken,
		Hostname:        host,
		Serial:          inv.Serial,
		Platform:        runtime.GOOS,
		OSVersion:       inv.OSVersion,
		Architecture:    runtime.GOARCH,
		AgentVersion:    agentVersion,
		Manufacturer:    inv.Manufacturer,
		Model:           inv.Model,
		HardwareUUID:    inv.HardwareUUID,
	}
	var out EnrollResponse
	if err := postJSON(cfg.ServerURL+"/api/v1/enroll", "", payload, &out); err != nil {
		return err
	}
	if out.DeviceID == "" || out.DeviceToken == "" {
		return errors.New("server returned an incomplete enrollment response")
	}

	cfg.DeviceID = out.DeviceID
	cfg.DeviceToken = out.DeviceToken
	cfg.EnrollmentToken = ""
	cfg.HeartbeatSeconds = out.HeartbeatSeconds
	if cfg.HeartbeatSeconds <= 0 {
		cfg.HeartbeatSeconds = 300
	}
	return nil
}

func heartbeat(cfg *Config) (int, bool, error) {
	host, _ := os.Hostname()
	inv := collectInventory()
	payload := HeartbeatRequest{
		Username:        inv.Username,
		LANIP:           firstLANIP(),
		Hostname:        host,
		Serial:          inv.Serial,
		OSVersion:       inv.OSVersion,
		Architecture:    runtime.GOARCH,
		AgentVersion:    agentVersion,
		WiFiSSID:        inv.WiFiSSID,
		Manufacturer:    inv.Manufacturer,
		Model:           inv.Model,
		HardwareUUID:    inv.HardwareUUID,
		BatteryPercent:  inv.BatteryPercent,
		BitLockerStatus: inv.BitLockerStatus,
		TPMStatus:       inv.TPMStatus,
		AntivirusStatus: inv.AntivirusStatus,
	}
	var out HeartbeatResponse
	if err := postJSON(cfg.ServerURL+"/api/v1/heartbeat", cfg.DeviceToken, payload, &out); err != nil {
		return 0, false, err
	}

	rotated := false
	if out.DeviceToken != "" && out.DeviceToken != cfg.DeviceToken {
		cfg.DeviceToken = out.DeviceToken
		rotated = true
	}

	if out.NextHeartbeatSeconds > 0 {
		return out.NextHeartbeatSeconds, rotated, nil
	}
	if cfg.HeartbeatSeconds > 0 {
		return cfg.HeartbeatSeconds, rotated, nil
	}
	return 300, rotated, nil
}

func softwareSyncDue(cfg Config) bool {
	if cfg.SoftwareSyncAt == "" {
		return true
	}
	last, err := time.Parse(time.RFC3339, cfg.SoftwareSyncAt)
	if err != nil {
		return true
	}
	return time.Since(last) >= 24*time.Hour
}

func syncSoftwareInventory(cfg Config) error {
	apps, err := collectSoftwareInventory()
	if err != nil {
		return err
	}

	var out SoftwareInventoryResponse
	if err := postJSON(
		cfg.ServerURL+"/api/v1/software-inventory",
		cfg.DeviceToken,
		SoftwareInventoryRequest{Applications: apps},
		&out,
	); err != nil {
		return err
	}
	if !out.OK {
		return errors.New("server did not acknowledge software inventory")
	}
	logLine("software inventory synced: present=%d added=%d removed=%d", out.Present, out.Added, out.Removed)
	return nil
}

func getJSON(url, bearer string, out any) error {
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return err
	}
	if bearer != "" {
		req.Header.Set("Authorization", "Bearer "+bearer)
	}

	client := &http.Client{Timeout: 20 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	raw, _ := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("server returned %s: %s", resp.Status, strings.TrimSpace(string(raw)))
	}
	if len(raw) == 0 {
		return nil
	}
	if err := json.Unmarshal(raw, out); err != nil {
		return fmt.Errorf("invalid server response: %w", err)
	}
	return nil
}


func postJSON(url, bearer string, payload any, out any) error {
	body, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	if bearer != "" {
		req.Header.Set("Authorization", "Bearer "+bearer)
	}

	client := &http.Client{Timeout: 20 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	raw, _ := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("server returned %s: %s", resp.Status, strings.TrimSpace(string(raw)))
	}
	if len(raw) == 0 {
		return nil
	}
	if err := json.Unmarshal(raw, out); err != nil {
		return fmt.Errorf("invalid server response: %w", err)
	}
	return nil
}

func firstLANIP() string {
	ifaces, err := net.Interfaces()
	if err != nil {
		return ""
	}
	for _, iface := range ifaces {
		if iface.Flags&net.FlagUp == 0 || iface.Flags&net.FlagLoopback != 0 {
			continue
		}
		addrs, err := iface.Addrs()
		if err != nil {
			continue
		}
		for _, addr := range addrs {
			var ip net.IP
			switch v := addr.(type) {
			case *net.IPNet:
				ip = v.IP
			case *net.IPAddr:
				ip = v.IP
			}
			if ip == nil || ip.To4() == nil || ip.IsLoopback() || ip.IsLinkLocalUnicast() {
				continue
			}
			return ip.String()
		}
	}
	return ""
}

func logLine(format string, args ...any) {
	line := fmt.Sprintf("%s "+format, append([]any{time.Now().Format(time.RFC3339)}, args...)...)
	fmt.Fprintln(os.Stderr, line)
	writePersistentLog(line)
}

func fatal(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}
