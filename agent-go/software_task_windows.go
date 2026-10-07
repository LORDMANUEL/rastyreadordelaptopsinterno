//go:build windows

package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

const maxMSIBytes int64 = 1024 * 1024 * 1024

var msiProductCodePattern = regexp.MustCompile(`^\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}$`)

func executeSoftwareTask(task SoftwareTask) (string, error) {
	switch task.Action {
	case "INSTALL":
		return installMSIPackage(task)
	case "UNINSTALL":
		return uninstallMSIPackage(task)
	default:
		return "", fmt.Errorf("unsupported software action: %s", task.Action)
	}
}

func installMSIPackage(task SoftwareTask) (string, error) {
	if task.PackageURL == "" || task.PackageSHA256 == "" {
		return "", errors.New("install task missing package URL or SHA-256")
	}

	parsed, err := url.Parse(task.PackageURL)
	if err != nil || !strings.EqualFold(parsed.Scheme, "https") || parsed.Host == "" || parsed.User != nil {
		return "", errors.New("package URL must be HTTPS without embedded credentials")
	}

	packageDir := filepath.Join(filepath.Dir(configPath()), "packages")
	if err := os.MkdirAll(packageDir, 0700); err != nil {
		return "", fmt.Errorf("create package directory: %w", err)
	}
	packagePath := filepath.Join(packageDir, task.ID+".msi")
	defer os.Remove(packagePath)

	actualHash, err := downloadMSI(task.PackageURL, packagePath)
	if err != nil {
		return "", err
	}
	if !strings.EqualFold(actualHash, task.PackageSHA256) {
		return "", fmt.Errorf("package SHA-256 mismatch: expected=%s actual=%s", task.PackageSHA256, actualHash)
	}
	if err := validateMSIHeader(packagePath); err != nil {
		return "", err
	}

	return runMSIExec("/i", packagePath)
}

func uninstallMSIPackage(task SoftwareTask) (string, error) {
	if !msiProductCodePattern.MatchString(task.ProductCode) {
		return "", errors.New("uninstall task has invalid MSI product code")
	}
	return runMSIExec("/x", strings.ToUpper(task.ProductCode))
}

func downloadMSI(packageURL, destination string) (string, error) {
	req, err := http.NewRequest(http.MethodGet, packageURL, nil)
	if err != nil {
		return "", err
	}
	client := &http.Client{
		Timeout: 10 * time.Minute,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			if len(via) >= 5 {
				return errors.New("too many package redirects")
			}
			if !strings.EqualFold(req.URL.Scheme, "https") {
				return errors.New("package redirect must remain HTTPS")
			}
			return nil
		},
	}

	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("download MSI: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return "", fmt.Errorf("download MSI returned %s", resp.Status)
	}

	f, err := os.OpenFile(destination, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0600)
	if err != nil {
		return "", fmt.Errorf("create MSI file: %w", err)
	}
	hasher := sha256.New()
	limited := io.LimitReader(resp.Body, maxMSIBytes+1)
	written, copyErr := io.Copy(io.MultiWriter(f, hasher), limited)
	closeErr := f.Close()
	if copyErr != nil {
		return "", fmt.Errorf("write MSI file: %w", copyErr)
	}
	if closeErr != nil {
		return "", fmt.Errorf("close MSI file: %w", closeErr)
	}
	if written > maxMSIBytes {
		return "", errors.New("MSI package exceeds 1 GiB limit")
	}
	return hex.EncodeToString(hasher.Sum(nil)), nil
}

func validateMSIHeader(path string) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()

	header := make([]byte, 8)
	if _, err := io.ReadFull(f, header); err != nil {
		return errors.New("MSI package is too small")
	}
	expected := []byte{0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1}
	for i := range expected {
		if header[i] != expected[i] {
			return errors.New("package is not a valid MSI/OLE file")
		}
	}
	return nil
}

func runMSIExec(action, target string) (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 12*time.Minute)
	defer cancel()

	cmd := exec.CommandContext(ctx, "msiexec.exe", action, target, "/qn", "/norestart")
	out, err := cmd.CombinedOutput()
	detail := strings.TrimSpace(string(out))
	if len(detail) > 1000 {
		detail = detail[:1000]
	}
	if ctx.Err() == context.DeadlineExceeded {
		return detail, errors.New("msiexec timed out after 12 minutes")
	}
	if err == nil {
		return "msiexec exit=0", nil
	}

	var exitErr *exec.ExitError
	if errors.As(err, &exitErr) {
		code := exitErr.ExitCode()
		if code == 3010 || code == 1641 {
			return fmt.Sprintf("msiexec exit=%d; restart required", code), nil
		}
		if detail != "" {
			return detail, fmt.Errorf("msiexec failed with exit code %d: %s", code, detail)
		}
		return "", fmt.Errorf("msiexec failed with exit code %d", code)
	}
	return detail, fmt.Errorf("msiexec failed: %w", err)
}
