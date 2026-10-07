param(
    [string]$InstallDir = "$env:ProgramFiles\YUDE\AssetGuard",
    [switch]$RemoveConfiguration
)

$ErrorActionPreference = "Stop"
$ServiceName = "YudeAssetGuard"

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Ejecute PowerShell como Administrador."
    }
}

function Wait-ServiceDeletion {
    param([string]$Name, [int]$TimeoutSeconds = 30)

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $service = Get-Service -Name $Name -ErrorAction SilentlyContinue
        if (-not $service) {
            return
        }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)

    throw "El servicio $Name no se eliminó dentro de $TimeoutSeconds segundos."
}

Assert-Administrator

$targetExe = Join-Path $InstallDir "YudeAssetGuard.exe"
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if ($service) {
    if ($service.Status -ne "Stopped") {
        Stop-Service -Name $ServiceName -Force
        $service.WaitForStatus("Stopped", [TimeSpan]::FromSeconds(20))
    }

    if (Test-Path $targetExe) {
        & $targetExe uninstall
        if ($LASTEXITCODE -ne 0) {
            throw "No se pudo eliminar el servicio."
        }
    } else {
        & sc.exe delete $ServiceName | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "No se pudo eliminar el servicio."
        }
    }

    Wait-ServiceDeletion -Name $ServiceName
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
