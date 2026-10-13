# Changelog

Todos los cambios relevantes de YUDE Asset Guard se documentan aquí.

## [Unreleased]

### Added — integración en validación
- Ficha empresarial y exportaciones XLSX/PDF.
- Neutralización de fórmulas no confiables en Excel y límites de resultados.


### Pendiente
- Android Enterprise productivo: validación física Device Owner/QR, keystore corporativo real y canal push rápido.
- Ficha empresarial/Leasing y exportes.
- Release pipeline Windows firmado y cierre de release empresarial.
- Piloto físico y aceptación.

## [0.13.0] - 2026-10-13

### Added
- Android Keystore-backed secure token storage.
- Android 12+ provisioning flow y generador QR reproducible.
- Workflow Android Release con signing mediante secretos.
- Catálogo de software con metadatos MSI.
- Cola de tareas de software Windows.
- Lease/reintentos para tareas.
- Ejecución MSI con HTTPS + SHA-256.
- Desinstalación por ProductCode.
- Logs persistentes Windows.
- Recovery SCM.
- Instalador Windows update-safe con rollback.
- Smoke test Docker Compose.
- Backups host-visible + SHA-256.
- Documentos PRD/TRD/UI-UX/App Flow/Backend Schema/Development Plan.

### Security
- API non-root.
- no-new-privileges.
- cap_drop ALL.
- CSRF.
- rate limiting.
- request limits.
- trusted proxy restrictivo.
- tokens por dispositivo con rotación/revocación.
- códigos temporales de enrolamiento.

## [0.10.0] - 2026-10-07

### Added
- /ready con PostgreSQL.
- hardening HTTP.
- observabilidad online/offline.
- inventario software.
- política software.

## [0.6.0] - 2026-10-06

### Added
- RBAC ADMINISTRADOR/SOPORTE/AUDITORIA.
- identidad técnica por dispositivo.
- historial de observaciones.
- GeoIP aproximado.

## [0.4.0] - 2026-10-05

### Added
- MVP FastAPI/PostgreSQL.
- agente Go Windows.
- Android debug.
- Docker Compose y CI.
