# Arquitectura - YUDE Asset Guard

## Objetivo

Mantener inventario y telemetría de laptops/tablets corporativas, con trazabilidad suficiente para auditoría y recuperación de activos.

## Flujo

```text
Windows Agent (Go)            Android Enterprise
        |                           |
        +-------- HTTPS/TLS --------+
                    |
              Reverse Proxy
                    |
                FastAPI
              /         \
       PostgreSQL       Web UI
```

## Identidad del dispositivo

1. El instalador recibe un token de enrolamiento.
2. El agente envía inventario inicial.
3. El servidor genera un token aleatorio único por dispositivo.
4. El servidor guarda únicamente SHA-256 del token.
5. El agente conserva el token local y lo usa como Bearer token.
6. Una fase posterior migrará a certificados de dispositivo/mTLS.

## Modo pérdida

En el MVP el Modo Pérdida:
- incrementa la frecuencia del heartbeat;
- destaca el activo en el panel;
- mantiene trazabilidad de conectividad;
- registra quién activó el modo y por qué.

No activa vigilancia personal.

## Límites

No se implementarán keyloggers, captura silenciosa de cámara/micrófono, robo de credenciales, lectura de mensajería personal, extracción de archivos privados ni bypass de controles del sistema operativo.

## Próximas fases

- RBAC y SSO.
- Certificados por dispositivo.
- Servicio nativo de Windows.
- Historial de redes/SSID.
- BitLocker/TPM/antivirus/compliance.
- Android Device Owner/Android Enterprise.
- Exportes de auditoría.
- CI/CD y paquetes MSI/APK.
