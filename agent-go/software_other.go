//go:build !windows

package main

func collectSoftwareInventory() ([]SoftwareItem, error) {
	return []SoftwareItem{}, nil
}
