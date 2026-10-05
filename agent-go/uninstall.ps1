param(
    [string]$InstallDir = "$env:ProgramFiles\YUDE\AssetGuard",
    [switch]$RemoveConfiguration
)

$ErrorActionPreference = "Stop"

$targetExe = Join-Path $InstallDir "YudeAssetGuard.exe"
$service = Get-Service -Name "YudeAssetGuard" -ErrorAction SilentlyContinue

if ($service) {
    if ($service.Status -ne "Stopped") {
        Stop-Service -Name "YudeAssetGuard" -Force
    }

    if (Test-Path $targetExe) {
        & $targetExe uninstall
    } else {
        sc.exe delete "YudeAssetGuard" | Out-Null
    }
}

if (Test-Path $InstallDir) {
    Remove-Item $InstallDir -Recurse -Force
}

if ($RemoveConfiguration) {
    $programDataDir = Join-Path $env:ProgramData "YUDEAssetGuard"
    if (Test-Path $programDataDir) {
        Remove-Item $programDataDir -Recurse -Force
    }
}

Write-Host "YUDE Asset Guard desinstalado."
if (-not $RemoveConfiguration) {
    Write-Host "La identidad/configuración del dispositivo se conservó para una futura reinstalación."
}
