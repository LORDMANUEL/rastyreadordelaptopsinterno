//go:build !windows

package main

import "errors"

func executeSoftwareTask(task SoftwareTask) (string, error) {
	return "", errors.New("software execution is supported only on Windows")
}
