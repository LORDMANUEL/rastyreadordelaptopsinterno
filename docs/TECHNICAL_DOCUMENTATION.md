# Technical Documentation — YUDE Asset Guard

Versión: 1.0
Fecha: 2026-10-13

## Componentes

### server/
FastAPI, SQLAlchemy, Alembic, PostgreSQL, panel web, RBAC, enrolamientos, auditoría, GeoIP, software/policy/tasks.

### agent-go/
Agente Windows:
- servicio SCM;
- inventario hardware/red/seguridad;
- software inventory;
- heartbeat;
- rotación de identidad;
- tareas MSI seguras;
- logs locales;
- install/uninstall scripts.

### android-mdm/
Cliente Kotlin:
- enrolamiento;
- heartbeat;
- WorkManager;
- Device Admin/Device Owner base.

### ops/
Scripts de backup/restore.

## Configuración crítica

Variables sensibles viven solo en .env del servidor.

Nunca versionar:
- POSTGRES_PASSWORD;
- ADMIN_TOKEN;
- SESSION_SECRET;
- certificados;
- keystores;
- códigos/tokens reales.

## Despliegue

1. Debian + Docker.
2. copiar .env.example -> .env.
3. definir secretos.
4. montar GeoLite2 si aplica.
5. docker compose up -d --build.
6. verificar /health y /ready.
7. publicar mediante reverse proxy HTTPS.
8. restringir FORWARDED_ALLOW_IPS.
9. configurar backup off-host.

## Operación Windows

Instalación:
```powershell
.\install.ps1 -ServerUrl "https://asset.example" -EnrollmentToken "CODIGO_TEMPORAL"
```

El instalador:
- exige admin;
- exige HTTPS;
- detiene/elimina servicio previo;
- reemplaza binario;
- aplica ACL;
- configura recovery;
- inicia servicio;
- rollback en fallo.

Logs:
```text
C:\ProgramData\YUDEAssetGuard\agent.log
```

## Operación backend

Health:
```text
GET /health
GET /ready
```

Panel:
```text
GET /
```

Roles:
- ADMINISTRADOR;
- SOPORTE;
- AUDITORIA.

## Software Windows

Catálogo:
- URL HTTPS;
- SHA-256;
- ProductCode.

Agente:
- descarga MSI;
- valida hash;
- valida cabecera OLE/MSI;
- msiexec silencioso;
- reporta resultado;
- no acepta shell arbitrario.

## Backup

```bash
docker compose exec backup sh /ops/backup-postgres.sh
```

Restauración:
- validar SHA-256;
- usar script restore;
- verificar /ready;
- ejecutar smoke test funcional.

## Troubleshooting básico

### API no ready
- docker compose ps;
- logs del API;
- conectividad PostgreSQL;
- DATABASE_URL;
- migraciones.

### Windows no heartbeat
- Get-Service YudeAssetGuard;
- revisar agent.log;
- validar HTTPS;
- validar config.json ACL;
- revisar token revocado/expirado.

### Software task falla
- revisar task.result_detail;
- validar HTTPS;
- validar SHA-256;
- validar ProductCode;
- revisar Event Viewer/msiexec si es necesario.

## Seguridad

No hay:
- shell remoto;
- keylogger;
- cámara/micrófono ocultos;
- extracción de archivos;
- lectura de mensajería.

Toda ampliación de ejecución remota debe pasar revisión de seguridad y tener executor explícito.
