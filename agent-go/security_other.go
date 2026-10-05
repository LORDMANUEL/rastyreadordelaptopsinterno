//go:build !windows

package main

import "os"

func secureConfigFile(path string) error {
	return os.Chmod(path, 0600)
}
