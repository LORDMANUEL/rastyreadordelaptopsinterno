# Instalación del agente Windows

## Requisitos

- Windows 10/11 x64.
- Acceso HTTPS al servidor YUDE Asset Guard.
- Permisos de administrador para instalar/iniciar el servicio.
- Equipo propiedad o bajo custodia de la empresa y cubierto por la política interna correspondiente.

## Paquete de GitHub Actions

El artefacto `YudeAssetGuard-windows-amd64` contiene:

```text
YudeAssetGuard.exe
install.ps1
uninstall.ps1
config.example.json
SHA256SUMS.txt
```

Puede validar el binario antes de instalar:

```powershell
Get-FileHash .\YudeAssetGuard.exe -Algorithm SHA256
Get-Content .\SHA256SUMS.txt
```

## Instalación recomendada

Abrir PowerShell como administrador desde la carpeta del artefacto:

```powershell
.\install.ps1 -ServerUrl "https://assets.example.com" -EnrollmentToken "CODIGO_TEMPORAL"
```

El script:

1. exige HTTPS;
2. copia el agente a `C:\Program Files\YUDE\AssetGuard\`;
3. crea `C:\ProgramData\YUDEAssetGuard\config.json`;
4. restringe la configuración a SYSTEM y Administradores;
5. instala el servicio `YudeAssetGuard`;
6. inicia el servicio;
7. muestra su estado final.

Después del enrolamiento correcto, el agente elimina el código temporal de enrolamiento y conserva únicamente su identidad técnica individual.

## Servicio

```text
Nombre: YudeAssetGuard
Inicio: Automático
Cuenta: LocalSystem
```

El usuario interactivo no se toma de la cuenta LocalSystem: se consulta mediante `Win32_ComputerSystem.UserName`.

## Instalación manual

También puede utilizarse:

```powershell
YudeAssetGuard.exe install
YudeAssetGuard.exe start
YudeAssetGuard.exe stop
YudeAssetGuard.exe uninstall
```

## Desinstalación

Conservar identidad/configuración para reinstalar:

```powershell
.\uninstall.ps1
```

Eliminar también configuración/identidad local:

```powershell
.\uninstall.ps1 -RemoveConfiguration
```

## Telemetría de solo lectura

El agente reporta:

- hostname;
- serial BIOS;
- UUID de hardware;
- fabricante/modelo;
- versión de Windows;
- usuario interactivo;
- IP LAN;
- SSID;
- batería;
- BitLocker;
- TPM;
- antivirus registrado en Windows Security Center;
- IP pública observada por el servidor.

El servidor conserva observaciones cuando cambia la red/IP/usuario y, durante Modo Pérdida, en cada heartbeat.

No captura teclado, pantalla, cámara, micrófono, mensajes ni archivos personales.
