//go:build !windows

package main

import "context"

func runPlatform(loop func(context.Context) error) error {
	return loop(context.Background())
}

func handlePlatformCommand(args []string) (bool, error) {
	return false, nil
}
