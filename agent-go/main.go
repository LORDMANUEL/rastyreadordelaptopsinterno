package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/exec"
	"os/user"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

const agentVersion = "0.1.0"

type Config struct {
	ServerURL        string `json:"server_url"`
	EnrollmentToken  string `json:"enrollment_token,omitempty"`
	DeviceID         string `json:"device_id,omitempty"`
	DeviceToken      string `json:"device_token,omitempty"`
	HeartbeatSeconds int    `json:"heartbeat_seconds,omitempty"`
}

type EnrollRequest struct {
	EnrollmentToken string `json:"enrollment_token"`
	Hostname        string `json:"hostname"`
	Serial          string `json:"serial,omitempty"`
	Platform        string `json:"platform"`
	OSVersion       string `json:"os_version,omitempty"`
	Architecture    string `json:"architecture,omitempty"`
	AgentVersion    string `json:"agent_version"`
}

type EnrollResponse struct {
	DeviceID         string `json:"device_id"`
	DeviceToken      string `json:"device_token"`
	HeartbeatSeconds int    `json:"heartbeat_seconds"`
}

type HeartbeatRequest struct {
	Username     string `json:"username,omitempty"`
	LANIP        string `json:"lan_ip,omitempty"`
	Hostname     string `json:"hostname,omitempty"`
	Serial       string `json:"serial,omitempty"`
	OSVersion    string `json:"os_version,omitempty"`
	Architecture string `json:"architecture,omitempty"`
	AgentVersion string `json:"agent_version"`
}

type HeartbeatResponse struct {
	OK                   bool `json:"ok"`
	LostMode             bool `json:"lost_mode"`
	NextHeartbeatSeconds int  `json:"next_heartbeat_seconds"`
}

func main() {
	cfgPath := configPath()
	cfg, err := loadConfig(cfgPath)
	if err != nil {
		fatal(err)
	}

	if cfg.DeviceToken == "" {
		if err := enroll(&cfg); err != nil {
			fatal(err)
		}
		if err := saveConfig(cfgPath, cfg); err != nil {
			fatal(err)
		}
	}

	for {
		next, err := heartbeat(cfg)
		if err != nil {
			fmt.Printf("%s heartbeat error: %v\n", time.Now().Format(time.RFC3339), err)
			next = 60
		}
		if next < 30 {
			next = 30
		}
		time.Sleep(time.Duration(next) * time.Second)
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
		return cfg, err
	}
	cfg.ServerURL = strings.TrimRight(cfg.ServerURL, "/")
	if cfg.ServerURL == "" {
		return cfg, errors.New("server_url is required")
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
	return os.WriteFile(path, raw, 0600)
}

func enroll(cfg *Config) error {
	if cfg.EnrollmentToken == "" {
		return errors.New("enrollment_token is required for first registration")
	}
	host, _ := os.Hostname()
	payload := EnrollRequest{
		EnrollmentToken: cfg.EnrollmentToken,
		Hostname:        host,
		Serial:          serialNumber(),
		Platform:        runtime.GOOS,
		OSVersion:       windowsVersion(),
		Architecture:    runtime.GOARCH,
		AgentVersion:    agentVersion,
	}
	var out EnrollResponse
	if err := postJSON(cfg.ServerURL+"/api/v1/enroll", "", payload, &out); err != nil {
		return err
	}
	cfg.DeviceID = out.DeviceID
	cfg.DeviceToken = out.DeviceToken
	cfg.EnrollmentToken = ""
	cfg.HeartbeatSeconds = out.HeartbeatSeconds
	return nil
}

func heartbeat(cfg Config) (int, error) {
	host, _ := os.Hostname()
	u, _ := user.Current()
	payload := HeartbeatRequest{
		Hostname:     host,
		Serial:       serialNumber(),
		OSVersion:    windowsVersion(),
		Architecture: runtime.GOARCH,
		AgentVersion: agentVersion,
		LANIP:        firstLANIP(),
	}
	if u != nil {
		payload.Username = u.Username
	}
	var out HeartbeatResponse
	err := postJSON(cfg.ServerURL+"/api/v1/heartbeat", cfg.DeviceToken, payload, &out)
	if err != nil {
		return 0, err
	}
	if out.NextHeartbeatSeconds > 0 {
		return out.NextHeartbeatSeconds, nil
	}
	if cfg.HeartbeatSeconds > 0 {
		return cfg.HeartbeatSeconds, nil
	}
	return 300, nil
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
	return json.Unmarshal(raw, out)
}

func firstLANIP() string {
	ifaces, _ := net.Interfaces()
	for _, iface := range ifaces {
		if iface.Flags&net.FlagUp == 0 || iface.Flags&net.FlagLoopback != 0 {
			continue
		}
		addrs, _ := iface.Addrs()
		for _, addr := range addrs {
			var ip net.IP
			switch v := addr.(type) {
			case *net.IPNet:
				ip = v.IP
			case *net.IPAddr:
				ip = v.IP
			}
			if ip != nil && ip.To4() != nil {
				return ip.String()
			}
		}
	}
	return ""
}

func serialNumber() string {
	if runtime.GOOS != "windows" {
		return ""
	}
	cmd := exec.Command("powershell", "-NoProfile", "-NonInteractive", "-Command",
		"(Get-CimInstance Win32_BIOS).SerialNumber")
	out, err := cmd.Output()
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(out))
}

func windowsVersion() string {
	if runtime.GOOS != "windows" {
		return runtime.GOOS
	}
	cmd := exec.Command("powershell", "-NoProfile", "-NonInteractive", "-Command",
		"(Get-CimInstance Win32_OperatingSystem).Caption + ' ' + (Get-CimInstance Win32_OperatingSystem).Version")
	out, err := cmd.Output()
	if err != nil {
		return "Windows"
	}
	return strings.TrimSpace(string(out))
}

func fatal(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}
