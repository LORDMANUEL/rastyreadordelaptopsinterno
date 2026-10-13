# PRD — YUDE Asset Guard

Estado: Baseline de cierre
Versión: 1.0
Fecha: 2026-10-13

## 1. Propósito

YUDE Asset Guard es una plataforma interna para inventario, telemetría operativa, recuperación, auditoría y administración de software de activos corporativos Windows y Android.

El producto está diseñado exclusivamente para equipos propiedad o bajo custodia de la empresa. No contempla keylogging, captura silenciosa de cámara/micrófono, lectura de mensajes, extracción de archivos privados ni bypass de controles del sistema operativo.

## 2. Usuarios

### ADMINISTRADOR
Control total del sistema, activos, enrolamientos, identidad técnica, auditoría y tareas de software.

### SOPORTE
Consulta de activos, historial, ficha operativa, Modo Pérdida y tareas operativas autorizadas.

### AUDITORIA
Acceso de solo lectura a activos, historial y eventos de auditoría.

## 3. Objetivos de producto

1. Registrar activos Windows/Android con identidad técnica individual.
2. Mantener telemetría operativa sin interacción diaria del usuario final.
3. Detectar estado online/offline y cambios de red.
4. Mantener historial auditable.
5. Permitir Modo Pérdida administrativo.
6. Inventariar hardware, seguridad y software.
7. Administrar software Windows únicamente desde catálogo aprobado.
8. Operar con controles de acceso y trazabilidad.
9. Desplegarse sobre Debian + PostgreSQL + HTTPS.
10. Permitir backup/restore reproducible.

## 4. Requisitos funcionales

| ID | Requisito | Estado |
|---|---|---|
| FR-001 | Enrolar dispositivo con código temporal | CUMPLE |
| FR-002 | Emitir token individual por dispositivo | CUMPLE |
| FR-003 | Rotar/revocar identidad técnica | CUMPLE |
| FR-004 | Heartbeat autenticado | CUMPLE |
| FR-005 | Inventario Windows: serial, UUID, fabricante, modelo, SO | CUMPLE |
| FR-006 | IP LAN/pública y SSID | CUMPLE |
| FR-007 | Batería, BitLocker, TPM, antivirus | CUMPLE |
| FR-008 | Ubicación aproximada derivada de IP | CUMPLE |
| FR-009 | Historial de red/usuario/Modo Pérdida | CUMPLE |
| FR-010 | Estado online/offline | CUMPLE |
| FR-011 | Modo Pérdida | CUMPLE |
| FR-012 | Inventario de software Windows | CUMPLE |
| FR-013 | Catálogo de software aprobado | CUMPLE |
| FR-014 | Tareas MSI install/uninstall con SHA-256 | CUMPLE EN CÓDIGO |
| FR-015 | Panel web con RBAC | CUMPLE |
| FR-016 | Usuarios ADMINISTRADOR/SOPORTE/AUDITORIA | CUMPLE |
| FR-017 | Auditoría de acciones administrativas | CUMPLE |
| FR-018 | Android enrolamiento/heartbeat | CUMPLE EN CÓDIGO |
| FR-019 | Android Enterprise Device Owner productivo | CUMPLE EN CÓDIGO / VALIDACIÓN FÍSICA PENDIENTE |
| FR-020 | QR provisioning Android | CUMPLE EN CÓDIGO / VALIDACIÓN FÍSICA PENDIENTE |
| FR-021 | Firma release Windows | EXTERNO |
| FR-022 | Firma release Android | CUMPLE EN PIPELINE / KEYSTORE CORPORATIVO EXTERNO |
| FR-023 | Exportes XLSX/PDF de activos/auditoría | PENDIENTE |
| FR-024 | Ficha completa leasing | PENDIENTE |
| FR-025 | Release pipeline firmado | PENDIENTE |

## 5. Requisitos no funcionales

| ID | Requisito | Estado |
|---|---|---|
| NFR-001 | HTTPS obligatorio para agentes Windows | CUMPLE |
| NFR-002 | Backend non-root | CUMPLE |
| NFR-003 | PostgreSQL no expuesto públicamente | CUMPLE |
| NFR-004 | CSRF/rate limiting/request limits | CUMPLE |
| NFR-005 | Health/readiness | CUMPLE |
| NFR-006 | Backups automáticos + checksum | CUMPLE |
| NFR-007 | Restore documentado | CUMPLE |
| NFR-008 | Logs persistentes agente Windows | CUMPLE |
| NFR-009 | CI server/Windows/Android | CUMPLE |
| NFR-010 | Branch protection + repo privado | EXTERNO |
| NFR-011 | Firma de artefactos | EXTERNO/PENDIENTE |
| NFR-012 | Piloto físico de aceptación | EXTERNO |

## 6. Criterios de aceptación

El producto se considera técnicamente listo cuando:

- CI principal está verde;
- migraciones aplican desde cero;
- Docker Compose levanta PostgreSQL/API/backup;
- /ready responde database=ok;
- enrolamiento temporal funciona;
- heartbeat actualiza telemetría;
- RBAC impide operaciones no autorizadas;
- software Windows se ejecuta solo desde catálogo aprobado;
- backup genera dump + SHA-256;
- documentación de instalación y recuperación está actualizada.

El producto se considera listo para producción empresarial únicamente después de:

- prueba física Windows;
- firma Authenticode;
- validación física Android Enterprise (Device Owner/QR/reboot/Doze/update) y keystore corporativo real;
- TLS/DNS real;
- restore real en entorno productivo;
- repositorio privado/protegido;
- piloto y aceptación.

## 7. Fuera de alcance

- vigilancia personal;
- keylogging;
- cámara/micrófono ocultos;
- shell remoto arbitrario;
- comandos PowerShell arbitrarios desde servidor;
- extracción de archivos personales;
- evasión de permisos del SO.

## 8. Métricas de éxito

- >= 99% de heartbeats procesados sin error en operación normal;
- 100% de activos enrolados con identidad individual;
- 100% de tareas de software auditadas;
- 100% de acciones privilegiadas asociadas a usuario/actor;
- restore de backup probado;
- cero secretos versionados en Git.
