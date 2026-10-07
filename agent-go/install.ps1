param(
    [Parameter(Mandatory=$true)]
    [string]$ServerUrl,

    [Parameter(Mandatory=$true)]
    [string]$EnrollmentToken,

    [string]$InstallDir = "$env:ProgramFiles\YUDE\AssetGuard"
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

if (-not $ServerUrl.StartsWith("https://", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "ServerUrl debe utilizar HTTPS."
}

$sourceExe = Join-Path $PSScriptRoot "YudeAssetGuard.exe"
if (-not (Test-Path $sourceExe)) {
    throw "No se encontró YudeAssetGuard.exe junto al instalador."
}

$programDataDir = Join-Path $env:ProgramData "YUDEAssetGuard"
$configPath = Join-Path $programDataDir "config.json"
$targetExe = Join-Path $InstallDir "YudeAssetGuard.exe"
$backupExe = Join-Path $InstallDir "YudeAssetGuard.exe.previous"

Write-Host "YUDE Asset Guard - Instalación corporativa"
Write-Host "Servidor: $ServerUrl"

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $programDataDir | Out-Null

$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "Deteniendo servicio existente..."
    if ($existingService.Status -ne "Stopped") {
        Stop-Service -Name $ServiceName -Force
        $existingService.WaitForStatus("Stopped", [TimeSpan]::FromSeconds(20))
    }

    if (Test-Path $targetExe) {
        & $targetExe uninstall
        if ($LASTEXITCODE -ne 0) {
            throw "No se pudo eliminar el servicio existente."
        }
    } else {
        & sc.exe delete $ServiceName | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "No se pudo eliminar el servicio existente."
        }
    }
    Wait-ServiceDeletion -Name $ServiceName
}

if (Test-Path $backupExe) {
    Remove-Item $backupExe -Force
}
if (Test-Path $targetExe) {
    Move-Item $targetExe $backupExe -Force
}

try {
    Copy-Item $sourceExe $targetExe -Force

    $config = @{
        server_url = $ServerUrl.TrimEnd("/")
        enrollment_token = $EnrollmentToken
        heartbeat_seconds = 300
    } | ConvertTo-Json

    Set-Content -Path $configPath -Value $config -Encoding UTF8

    & icacls $programDataDir /inheritance:r /grant:r "*S-1-5-18:(OI)(CI)(F)" "*S-1-5-32-544:(OI)(CI)(F)" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudieron aplicar ACL al directorio de configuración."
    }

    & $targetExe install
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo instalar el servicio."
    }

    & sc.exe failure $ServiceName reset= 86400 actions= restart/60000/restart/60000/none/0 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo configurar la recuperación automática del servicio."
    }
    & sc.exe failureflag $ServiceName 1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo habilitar la recuperación ante fallos no controlados."
    }

    & $targetExe start
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo iniciar el servicio."
    }

    $service = Get-Service -Name $ServiceName
    $service.WaitForStatus("Running", [TimeSpan]::FromSeconds(20))

    if (Test-Path $backupExe) {
        Remove-Item $backupExe -Force
    }

    Write-Host ""
    Write-Host "Instalación finalizada."
    Write-Host "Servicio: $($service.Name)"
    Write-Host "Estado: $($service.Status)"
    Write-Host "Configuración: $configPath"
    Write-Host "Log: $(Join-Path $programDataDir 'agent.log')"
}
catch {
    Write-Warning "La instalación falló. Intentando rollback."

    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        try {
            if ($service.Status -ne "Stopped") {
                Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
            }
            & sc.exe delete $ServiceName | Out-Null
            Wait-ServiceDeletion -Name $ServiceName -TimeoutSeconds 15
        } catch {
            Write-Warning "No se pudo limpiar completamente el servicio durante rollback."
        }
    }

    if (Test-Path $targetExe) {
        Remove-Item $targetExe -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path $backupExe) {
        Move-Item $backupExe $targetExe -Force
        try {
            & $targetExe install
            & $targetExe start
        } catch {
            Write-Warning "No se pudo restaurar automáticamente la versión anterior."
        }
    }

    throw
}
