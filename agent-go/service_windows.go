//go:build windows

package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
	"time"
	"unsafe"
)

const (
	serviceName = "YudeAssetGuard"

	serviceStopped            = 0x00000001
	serviceStartPending       = 0x00000002
	serviceStopPending        = 0x00000003
	serviceRunning            = 0x00000004
	serviceAcceptStop         = 0x00000001
	serviceAcceptShutdown     = 0x00000004
	serviceControlStop        = 0x00000001
	serviceControlInterrogate = 0x00000004
	serviceControlShutdown    = 0x00000005

	errorFailedServiceControllerConnect syscall.Errno = 1063
)

type serviceStatus struct {
	ServiceType             uint32
	CurrentState            uint32
	ControlsAccepted        uint32
	Win32ExitCode           uint32
	ServiceSpecificExitCode uint32
	CheckPoint              uint32
	WaitHint                uint32
}

type serviceTableEntry struct {
	ServiceName *uint16
	ServiceProc uintptr
}

var (
	advapi32                          = syscall.NewLazyDLL("advapi32.dll")
	procStartServiceCtrlDispatcherW   = advapi32.NewProc("StartServiceCtrlDispatcherW")
	procRegisterServiceCtrlHandlerExW = advapi32.NewProc("RegisterServiceCtrlHandlerExW")
	procSetServiceStatus              = advapi32.NewProc("SetServiceStatus")

	serviceMainCallback = syscall.NewCallback(serviceMain)
	serviceCtrlCallback = syscall.NewCallback(serviceControlHandler)
	serviceCancel       context.CancelFunc
	statusHandle        uintptr
)

func runPlatform(loop func(context.Context) error) error {
	err := runAsWindowsService()
	if errors.Is(err, errorFailedServiceControllerConnect) {
		return loop(context.Background())
	}
	return err
}

func runAsWindowsService() error {
	name, err := syscall.UTF16PtrFromString(serviceName)
	if err != nil {
		return err
	}

	table := [...]serviceTableEntry{
		{ServiceName: name, ServiceProc: serviceMainCallback},
		{},
	}

	r1, _, callErr := procStartServiceCtrlDispatcherW.Call(uintptr(unsafe.Pointer(&table[0])))
	if r1 == 0 {
		if errno, ok := callErr.(syscall.Errno); ok && errno != 0 {
			return errno
		}
		return errors.New("StartServiceCtrlDispatcherW failed")
	}
	return nil
}

func serviceMain(_ uint32, _ uintptr) uintptr {
	name, _ := syscall.UTF16PtrFromString(serviceName)
	handle, _, _ := procRegisterServiceCtrlHandlerExW.Call(
		uintptr(unsafe.Pointer(name)),
		serviceCtrlCallback,
		0,
	)
	if handle == 0 {
		return 0
	}
	statusHandle = handle
	setServiceStatus(serviceStartPending, 0, 5000, 0)

	ctx, cancel := context.WithCancel(context.Background())
	serviceCancel = cancel
	done := make(chan error, 1)
	go func() { done <- agentLoop(ctx) }()

	setServiceStatus(serviceRunning, serviceAcceptStop|serviceAcceptShutdown, 0, 0)
	err := <-done
	if err != nil {
		setServiceStatus(serviceStopped, 0, 0, 1)
	} else {
		setServiceStatus(serviceStopped, 0, 0, 0)
	}
	return 0
}

func serviceControlHandler(control uint32, _ uint32, _ uintptr, _ uintptr) uintptr {
	switch control {
	case serviceControlStop, serviceControlShutdown:
		setServiceStatus(serviceStopPending, 0, 20000, 0)
		if serviceCancel != nil {
			serviceCancel()
		}
	case serviceControlInterrogate:
	}
	return 0
}

func setServiceStatus(state, accepted, waitHint, exitCode uint32) {
	if statusHandle == 0 {
		return
	}
	status := serviceStatus{
		ServiceType:      0x00000010,
		CurrentState:     state,
		ControlsAccepted: accepted,
		Win32ExitCode:    exitCode,
		WaitHint:         waitHint,
	}
	procSetServiceStatus.Call(statusHandle, uintptr(unsafe.Pointer(&status)))
}

func handlePlatformCommand(args []string) (bool, error) {
	if len(args) == 0 {
		return false, nil
	}
	switch args[0] {
	case "install":
		return true, installService()
	case "uninstall":
		return true, runSC("delete", serviceName)
	case "start":
		return true, runSC("start", serviceName)
	case "stop":
		return true, stopService()
	default:
		return false, nil
	}
}

func installService() error {
	exePath, err := os.Executable()
	if err != nil {
		return err
	}
	exePath, err = filepath.Abs(exePath)
	if err != nil {
		return err
	}
	binPath := fmt.Sprintf(""%s"", exePath)
	if err := runSC(
		"create", serviceName,
		"binPath=", binPath,
		"start=", "auto",
		"DisplayName=", "YUDE Asset Guard",
	); err != nil {
		return err
	}
	_ = runSC("description", serviceName, "Inventario y monitoreo autorizado de activos corporativos YUDE.")
	return nil
}

func stopService() error {
	cmd := exec.Command("sc.exe", "stop", serviceName)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("sc.exe stop failed: %w: %s", err, string(out))
	}
	deadline := time.Now().Add(20 * time.Second)
	for time.Now().Before(deadline) {
		time.Sleep(500 * time.Millisecond)
		query := exec.Command("sc.exe", "query", serviceName)
		qout, _ := query.CombinedOutput()
		if !containsWindowsServiceRunningState(string(qout)) {
			return nil
		}
	}
	return errors.New("service did not stop within 20 seconds")
}

func containsWindowsServiceRunningState(output string) bool {
	return containsASCII(output, "RUNNING") || containsASCII(output, "STOP_PENDING")
}

func containsASCII(haystack, needle string) bool {
	if len(needle) == 0 {
		return true
	}
	for i := 0; i+len(needle) <= len(haystack); i++ {
		match := true
		for j := 0; j < len(needle); j++ {
			a := haystack[i+j]
			b := needle[j]
			if a >= 'a' && a <= 'z' {
				a -= 32
			}
			if b >= 'a' && b <= 'z' {
				b -= 32
			}
			if a != b {
				match = false
				break
			}
		}
		if match {
			return true
		}
	}
	return false
}

func runSC(args ...string) error {
	cmd := exec.Command("sc.exe", args...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("sc.exe %v failed: %w: %s", args, err, string(out))
	}
	return nil
}
