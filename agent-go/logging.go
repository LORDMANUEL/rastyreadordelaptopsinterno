package main

import (
	"fmt"
	"os"
	"path/filepath"
)

const maxLogBytes int64 = 5 * 1024 * 1024

func writePersistentLog(line string) {
	path := filepath.Join(filepath.Dir(configPath()), "agent.log")
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return
	}

	if info, err := os.Stat(path); err == nil && info.Size() >= maxLogBytes {
		rotated := path + ".1"
		_ = os.Remove(rotated)
		_ = os.Rename(path, rotated)
	}

	f, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0600)
	if err != nil {
		return
	}
	defer f.Close()
	_, _ = fmt.Fprintln(f, line)
	_ = secureConfigFile(path)
}
