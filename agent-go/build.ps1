$ErrorActionPreference = "Stop"
$env:GOOS = "windows"
$env:GOARCH = "amd64"
New-Item -ItemType Directory -Force -Path ".\bin" | Out-Null
go fmt ./...
go vet ./...
go build -trimpath -ldflags="-s -w" -o ".\bin\YudeAssetGuard.exe" .
Write-Host "Build listo: agent-go\bin\YudeAssetGuard.exe"
