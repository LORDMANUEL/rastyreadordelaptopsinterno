# Instalación del agente Windows

## Requisitos

- Windows 10/11 x64.
- Acceso HTTPS al servidor YUDE Asset Guard.
- Permisos de administrador únicamente para instalar/iniciar el servicio.

## 1. Preparar configuración

Crear:

```text
C:\ProgramData\YUDEAssetGuard\config.json
```

Ejemplo:

```json
{
  "server_url": "https://assets.example.com",
  "enrollment_token": "TOKEN_TEMPORAL_DE_ENROLAMIENTO",
  "heartbeat_seconds": 300
}
```

El token de enrolamiento se elimina automáticamente del archivo después del primer enrolamiento correcto y se reemplaza por el token individual del dispositivo.

## 2. Instalar servicio

Abrir PowerShell como administrador:

```powershell
New-Item -ItemType Directory -Force "C:\Program Files\YUDE\AssetGuard"
Copy-Item .\YudeAssetGuard.exe "C:\Program Files\YUDE\AssetGuard\YudeAssetGuard.exe"

& "C:\Program Files\YUDE\AssetGuard\YudeAssetGuard.exe" install
& "C:\Program Files\YUDE\AssetGuard\YudeAssetGuard.exe" start
```

Servicio registrado:

```text
YudeAssetGuard
```

Inicio: automático.

## Comandos

```powershell
YudeAssetGuard.exe install
YudeAssetGuard.exe start
YudeAssetGuard.exe stop
YudeAssetGuard.exe uninstall
```

Sin argumentos, el ejecutable trabaja en modo consola si no fue iniciado por el Service Control Manager.

## Telemetría de solo lectura

El agente reporta:

- hostname;
- serial BIOS;
- UUID de hardware;
- fabricante/modelo;
- versión de Windows;
- usuario de sesión;
- IP LAN;
- SSID;
- batería;
- estado BitLocker;
- presencia/estado TPM;
- producto antivirus registrado en Windows Security Center;
- IP pública observada por el servidor.

No captura teclado, pantalla, cámara, micrófono, mensajes ni archivos personales.

## Desinstalación autorizada

```powershell
& "C:\Program Files\YUDE\AssetGuard\YudeAssetGuard.exe" stop
& "C:\Program Files\YUDE\AssetGuard\YudeAssetGuard.exe" uninstall
```
