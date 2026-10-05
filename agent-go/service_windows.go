//go:build windows

package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"golang.org/x/sys/windows/svc"
	"golang.org/x/sys/windows/svc/mgr"
)

const serviceName = "YudeAssetGuard"

type serviceHandler struct{}

func (h *serviceHandler) Execute(args []string, requests <-chan svc.ChangeRequest, status chan<- svc.Status) (bool, uint32) {
	const accepts = svc.AcceptStop | svc.AcceptShutdown
	status <- svc.Status{State: svc.StartPending}
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() { done <- agentLoop(ctx) }()
	status <- svc.Status{State: svc.Running, Accepts: accepts}

	for {
		select {
		case req := <-requests:
			switch req.Cmd {
			case svc.Interrogate:
				status <- req.CurrentStatus
			case svc.Stop, svc.Shutdown:
				status <- svc.Status{State: svc.StopPending}
				cancel()
				select {
				case <-done:
				case <-time.After(20 * time.Second):
				}
				return false, 0
			}
		case <-done:
			return false, 0
		}
	}
}

func runPlatform(loop func(context.Context) error) error {
	isService, err := svc.IsWindowsService()
	if err != nil { return err }
	if isService { return svc.Run(serviceName, &serviceHandler{}) }
	return loop(context.Background())
}

func handlePlatformCommand(args []string) (bool, error) {
	if len(args) == 0 { return false, nil }
	switch args[0] {
	case "install":
		return true, installService()
	case "uninstall":
		return true, uninstallService()
	case "start":
		return true, serviceControl("start")
	case "stop":
		return true, serviceControl("stop")
	default:
		return false, nil
	}
}

func installService() error {
	exe, err := os.Executable()
	if err != nil { return err }
	exe, err = filepath.Abs(exe)
	if err != nil { return err }
	m, err := mgr.Connect()
	if err != nil { return err }
	defer m.Disconnect()

	if existing, err := m.OpenService(serviceName); err == nil {
		existing.Close()
		return fmt.Errorf("%s is already installed", serviceName)
	}
	s, err := m.CreateService(serviceName, exe, mgr.Config{
		DisplayName: "YUDE Asset Guard",
		Description: "Inventario y monitoreo autorizado de activos corporativos YUDE.",
		StartType: mgr.StartAutomatic,
	})
	if err != nil { return err }
	defer s.Close()
	return nil
}

func uninstallService() error {
	m, err := mgr.Connect()
	if err != nil { return err }
	defer m.Disconnect()
	s, err := m.OpenService(serviceName)
	if err != nil { return err }
	defer s.Close()
	return s.Delete()
}

func serviceControl(action string) error {
	m, err := mgr.Connect()
	if err != nil { return err }
	defer m.Disconnect()
	s, err := m.OpenService(serviceName)
	if err != nil { return err }
	defer s.Close()
	if action == "start" { return s.Start() }
	_, err = s.Control(svc.Stop)
	return err
}
