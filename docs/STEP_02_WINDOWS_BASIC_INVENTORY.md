# Paso 02 - Inventario básico Windows

Estado: VALIDADO LOCALMENTE
Versión agente local validada: 0.6.0-local

## Alcance

Inventario Windows de solo lectura para:

- usuario interactivo (`Win32_ComputerSystem.UserName`);
- serial BIOS (`Win32_BIOS.SerialNumber`);
- fabricante;
- modelo;
- UUID de hardware;
- nombre y versión de Windows.

La recolección utiliza PowerShell/CIM estándar. No modifica políticas del sistema.

## Validación local

```text
go test ./...                                  PASS
GOOS=windows GOARCH=amd64 go vet ./...         PASS
GOOS=windows GOARCH=amd64 go build             PASS
file YudeAssetGuard.exe                         PE32+ x86-64
```

SHA-256 del binario local validado:

```text
2fbfb36cc918caee49fe4d50b13c5ef8ca3d7302581e2d8b4c422ef72020e930
```

## Servicio Windows

En este corte también se sustituyó `golang.org/x/sys/windows/svc` por una implementación SCM basada en las APIs nativas de Windows expuestas por `advapi32.dll`.

Resultado:

- un solo ejecutable;
- sin dependencia Go externa para el servicio;
- instalación visible con `sc.exe`;
- start/stop/uninstall administrables;
- modo consola cuando no es iniciado por SCM.

## Pendiente de hardware real

Aún debe validarse en una laptop Windows física:

1. inicio real bajo SCM;
2. valores CIM en hardware corporativo;
3. usuario interactivo con sesión iniciada/cerrada.

## Fuera de este paso

No se añadieron aquí:

- BitLocker;
- TPM;
- antivirus/ESET;
- batería;
- Wi-Fi/SSID;
- gateway.

Esas funciones se mantienen para pasos posteriores y deben validarse por separado.
