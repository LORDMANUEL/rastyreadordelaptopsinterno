param(
    [Parameter(Mandatory=$true)]
    [string]$ServerUrl,

    [Parameter(Mandatory=$true)]
    [string]$EnrollmentToken,

    [string]$InstallDir = "$env:ProgramFiles\YUDE\AssetGuard"
)

$ErrorActionPreference = "Stop"

if (-not $ServerUrl.StartsWith("https://")) {
    throw "ServerUrl debe utilizar HTTPS."
}

$sourceExe = Join-Path $PSScriptRoot "YudeAssetGuard.exe"
if (-not (Test-Path $sourceExe)) {
    throw "No se encontró YudeAssetGuard.exe junto al instalador."
}

$programDataDir = Join-Path $env:ProgramData "YUDEAssetGuard"
$configPath = Join-Path $programDataDir "config.json"
$targetExe = Join-Path $InstallDir "YudeAssetGuard.exe"

Write-Host "YUDE Asset Guard - Instalación corporativa"
Write-Host "Servidor: $ServerUrl"

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $programDataDir | Out-Null

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

$service = Get-Service -Name "YudeAssetGuard" -ErrorAction SilentlyContinue
if ($service) {
    if ($service.Status -ne "Stopped") {
        Stop-Service -Name "YudeAssetGuard" -Force
    }
    & $targetExe uninstall
}

& $targetExe install
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo instalar el servicio."
}

& $targetExe start
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo iniciar el servicio."
}

Start-Sleep -Seconds 2
$service = Get-Service -Name "YudeAssetGuard"

Write-Host ""
Write-Host "Instalación finalizada."
Write-Host "Servicio: $($service.Name)"
Write-Host "Estado: $($service.Status)"
Write-Host "Configuración: $configPath"
