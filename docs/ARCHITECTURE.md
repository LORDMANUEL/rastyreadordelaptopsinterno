# Arquitectura — YUDE Asset Guard

## Vista general

```text
Windows Agent (Go)       Android Client (Kotlin)
        |                         |
        +--------- HTTPS ---------+
                    |
              Reverse Proxy
                    |
                  FastAPI
                /        \
        PostgreSQL       Web UI
            |
        Backup/Restore
```

## Backend

Responsabilidades:
- autenticación/RBAC;
- enrolamientos temporales;
- identidad de dispositivos;
- heartbeat;
- observabilidad;
- auditoría;
- software inventory/policy/tasks;
- GeoIP aproximado;
- panel web.

## Windows

Servicio nativo:
- LocalSystem;
- inventario hardware/red/seguridad;
- software inventory;
- logs persistentes;
- installer update-safe + rollback;
- service recovery;
- MSI install/uninstall desde catálogo aprobado.

## Android

Cliente corporativo:
- enrolamiento HTTPS;
- identidad por dispositivo;
- heartbeat;
- WorkManager;
- Device Owner base.

Pendiente productivo:
- QR/zero-touch;
- Android Keystore;
- release signing;
- push rápido.

## Identidad del dispositivo

1. código temporal;
2. enrolamiento;
3. servidor emite token aleatorio individual;
4. servidor guarda hash;
5. agente almacena identidad protegida;
6. token rota y puede revocarse.

## Software remoto

No existe shell remoto.

Flujo permitido:
- catálogo aprobado;
- HTTPS;
- SHA-256;
- MSI;
- msiexec silencioso;
- task lease/retry;
- auditoría.

## Seguridad

- backend non-root;
- CSRF;
- rate limiting;
- request limits;
- trusted proxy;
- HTTPS para agentes;
- PostgreSQL privado;
- backup + checksum;
- roles.

## Escalado

El monitor offline interno está diseñado para una instancia API.
Con múltiples replicas debe moverse a un scheduler único.
