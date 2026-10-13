# Changelog

Todos los cambios relevantes de YUDE Asset Guard se documentan aquí.

## [Unreleased]

### Pendiente
- Android Enterprise productivo: QR/zero-touch, Keystore y release signing.
- Ficha empresarial/Leasing y exportes.
- Release pipeline firmado.
- Piloto físico y aceptación.

## [0.13.0] - 2026-10-13

### Added
- Enterprise asset fields for department, condition, ownership/lease, contract, provider, dates, cost, notes and last audit.
- XLSX/PDF exports for assets and audit.
- Android Keystore-backed identity, Android 12+ provisioning and QR payload generation.
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
