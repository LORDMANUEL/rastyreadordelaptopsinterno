package main

import (
	"errors"
	"fmt"
)

type SoftwareTask struct {
	ID              string `json:"id"`
	Action          string `json:"action"`
	CatalogID       string `json:"catalog_id"`
	Name            string `json:"name"`
	Publisher       string `json:"publisher,omitempty"`
	ApprovedVersion string `json:"approved_version,omitempty"`
	PackageURL      string `json:"package_url,omitempty"`
	PackageSHA256   string `json:"package_sha256,omitempty"`
	ProductCode     string `json:"product_code,omitempty"`
}

type SoftwareTaskClaimResponse struct {
	OK       bool   `json:"ok"`
	Status   string `json:"status"`
	Attempts int    `json:"attempts"`
}

type SoftwareTaskResultRequest struct {
	Status string `json:"status"`
	Detail string `json:"detail,omitempty"`
}

func syncSoftwareTasks(cfg Config) error {
	var tasks []SoftwareTask
	if err := getJSON(
		cfg.ServerURL+"/api/v1/device-tasks/pending",
		cfg.DeviceToken,
		&tasks,
	); err != nil {
		return err
	}
	if len(tasks) == 0 {
		return nil
	}

	task := tasks[0]
	if task.ID == "" {
		return errors.New("server returned task without id")
	}

	var claim SoftwareTaskClaimResponse
	if err := postJSON(
		cfg.ServerURL+"/api/v1/device-tasks/"+task.ID+"/claim",
		cfg.DeviceToken,
		struct{}{},
		&claim,
	); err != nil {
		return fmt.Errorf("claim task %s: %w", task.ID, err)
	}
	if !claim.OK || claim.Status != "RUNNING" {
		return fmt.Errorf("task %s was not claimed", task.ID)
	}

	detail, execErr := executeSoftwareTask(task)
	result := SoftwareTaskResultRequest{Status: "SUCCEEDED", Detail: detail}
	if execErr != nil {
		result.Status = "FAILED"
		result.Detail = execErr.Error()
	}

	var out map[string]any
	if err := postJSON(
		cfg.ServerURL+"/api/v1/device-tasks/"+task.ID+"/result",
		cfg.DeviceToken,
		result,
		&out,
	); err != nil {
		return fmt.Errorf("report task %s result: %w", task.ID, err)
	}

	if execErr != nil {
		logLine("software task failed: id=%s action=%s name=%s error=%v", task.ID, task.Action, task.Name, execErr)
		return nil
	}
	logLine("software task succeeded: id=%s action=%s name=%s", task.ID, task.Action, task.Name)
	return nil
}
