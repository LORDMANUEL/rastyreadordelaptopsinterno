# TRD — Technical Requirements Document

Estado: Baseline de cierre
Versión: 1.0
Fecha: 2026-10-13

## 1. Stack

- Backend: Python 3.12 + FastAPI.
- ORM: SQLAlchemy 2.
- Migraciones: Alembic.
- DB: PostgreSQL.
- Agente Windows: Go.
- Android: Kotlin + WorkManager + Device Admin/Device Owner base.
- UI: HTML/CSS/JavaScript servido por FastAPI.
- Deploy: Debian + Docker Compose + reverse proxy HTTPS.
- CI: GitHub Actions.

## 2. Arquitectura

```text
Windows Agent / Android Client
          |
        HTTPS
          |
    Reverse Proxy
          |
       FastAPI
      /      \
PostgreSQL   Web UI
     |
 Backups/Restore
```

## 3. Requisitos técnicos

### API
- HTTPS delante del backend.
- request size limits.
- rate limiting para login/enrolamiento.
- CSRF para escrituras autenticadas por cookie.
- headers de seguridad.
- request/correlation ID.
- health y readiness.
- trusted proxy restringido.

### Autenticación humana
- usuarios persistentes;
- roles ADMINISTRADOR/SOPORTE/AUDITORIA;
- scrypt para derivación;
- sesión HMAC;
- cookie HttpOnly/Secure/SameSite=Strict;
- cuenta activa verificada en cada request.

### Identidad del dispositivo
- token aleatorio único;
- servidor almacena hash;
- expiración;
- rotación;
- revocación;
- código de enrolamiento temporal;
- no reutilizar token entre equipos.

### Windows
- servicio SCM;
- LocalSystem;
- instalador PowerShell;
- update-safe;
- rollback;
- service recovery;
- logs persistentes;
- inventario hardware/red/seguridad/software;
- HTTPS obligatorio;
- software remoto solo MSI aprobado.

### Android
- HTTPS;
- token por dispositivo;
- heartbeat;
- Device Owner base;
- WorkManager;
- sin bypass de controles Android.

## 4. Seguridad de software remoto

Permitido:
- INSTALL MSI.
- UNINSTALL MSI.
- package_url HTTPS.
- SHA-256 obligatorio.
- ProductCode validado.
- msiexec silencioso.
- máximo de intentos.
- lease para recuperación.

Prohibido:
- shell remoto;
- PowerShell arbitrario;
- argumentos arbitrarios;
- EXE genéricos;
- HTTP;
- URLs con credenciales embebidas.

## 5. Persistencia

PostgreSQL es la fuente de verdad para:
- dispositivos;
- usuarios;
- enrolamientos;
- auditoría;
- observaciones;
- software instalado;
- catálogo/políticas;
- tareas de software.

## 6. CI/CD

Cada cambio debe validar:
- Docker Compose;
- build imagen API;
- usuario non-root;
- healthcheck;
- smoke test PostgreSQL/API/backup;
- Python compile/import/tests;
- migraciones;
- gofmt;
- go vet Linux/Windows;
- build agente Windows;
- parse de PowerShell;
- build Android.

## 7. Disponibilidad

MVP:
- una instancia API;
- PostgreSQL persistente;
- restart policies;
- health/readiness;
- monitor offline interno.

Escala futura:
- si hay múltiples replicas, mover monitor offline a scheduler único.

## 8. Logging

Backend:
- logging estructurado recomendado.
Agente Windows:
- agent.log;
- rotación local;
- ACL restrictiva.

## 9. Backup

- pg_dump automático;
- checksum SHA-256;
- retención configurable;
- directorio visible en host;
- copia off-host requerida;
- restore documentado.

## 10. Compatibilidad

Windows:
- Windows 10/11 x64.
Android:
- validar versiones reales de flota antes de producción.

## 11. Requisitos externos de producción

No se pueden cerrar únicamente con código:
- certificado Authenticode;
- keystore Android release;
- dominio/TLS productivo;
- repositorio privado/protegido;
- hardware físico para piloto;
- requisitos finales Leasing Atlántida.
