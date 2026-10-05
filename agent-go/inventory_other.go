//go:build !windows

package main

import "runtime"

func collectInventory() Inventory {
	return Inventory{OSVersion: runtime.GOOS}
}
