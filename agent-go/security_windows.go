//go:build windows

package main

import (
	"fmt"
	"os/exec"
)

func secureConfigFile(path string) error {
	cmd := exec.Command(
		"icacls",
		path,
		"/inheritance:r",
		"/grant:r",
		"*S-1-5-18:(F)",
		"*S-1-5-32-544:(F)",
	)
	if out, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("secure config ACL: %w: %s", err, string(out))
	}
	return nil
}
