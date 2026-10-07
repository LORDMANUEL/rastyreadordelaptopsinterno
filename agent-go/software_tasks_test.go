package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"
)

func TestSyncSoftwareTasksClaimsAndReportsResult(t *testing.T) {
	var mu sync.Mutex
	claimed := false
	reported := false
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if got := r.Header.Get("Authorization"); got != "Bearer device-token" {
			t.Fatalf("unexpected authorization header: %q", got)
		}
		switch {
		case r.Method == http.MethodGet && r.URL.Path == "/api/v1/device-tasks/pending":
			_ = json.NewEncoder(w).Encode([]SoftwareTask{{
				ID: "task-1",
				Action: "INSTALL",
				Name: "Test MSI",
				PackageURL: "https://downloads.example.invalid/test.msi",
				PackageSHA256: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
			}})
		case r.Method == http.MethodPost && r.URL.Path == "/api/v1/device-tasks/task-1/claim":
			mu.Lock()
			claimed = true
			mu.Unlock()
			_ = json.NewEncoder(w).Encode(SoftwareTaskClaimResponse{OK: true, Status: "RUNNING", Attempts: 1})
		case r.Method == http.MethodPost && r.URL.Path == "/api/v1/device-tasks/task-1/result":
			var payload SoftwareTaskResultRequest
			if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
				t.Fatalf("decode result: %v", err)
			}
			if payload.Status != "FAILED" {
				t.Fatalf("expected FAILED on non-Windows test runner, got %s", payload.Status)
			}
			mu.Lock()
			reported = true
			mu.Unlock()
			_ = json.NewEncoder(w).Encode(map[string]any{"ok": true})
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()

	cfg := Config{ServerURL: server.URL, DeviceToken: "device-token"}
	if err := syncSoftwareTasks(cfg); err != nil {
		t.Fatalf("syncSoftwareTasks returned error: %v", err)
	}

	mu.Lock()
	defer mu.Unlock()
	if !claimed {
		t.Fatal("task was not claimed")
	}
	if !reported {
		t.Fatal("task result was not reported")
	}
}

func TestSyncSoftwareTasksNoPendingTasks(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_ = json.NewEncoder(w).Encode([]SoftwareTask{})
	}))
	defer server.Close()

	cfg := Config{ServerURL: server.URL, DeviceToken: "device-token"}
	if err := syncSoftwareTasks(cfg); err != nil {
		t.Fatalf("syncSoftwareTasks returned error: %v", err)
	}
}
