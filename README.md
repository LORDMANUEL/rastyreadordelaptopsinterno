# YUDE Asset Guard

Plataforma interna para inventario, telemetría, recuperación, auditoría y administración controlada de software en activos corporativos Windows y Android.

> Diseñada para equipos propiedad o bajo custodia de la empresa. No implementa keylogging, captura silenciosa de cámara/micrófono, lectura de mensajes, extracción de archivos privados ni shell remoto arbitrario.

## Arquitectura

- Backend: Python 3.12 + FastAPI + PostgreSQL + Alembic.
- Panel web: HTML/CSS/JavaScript servido por FastAPI.
- Windows: agente Go como servicio Windows.
- Android: Kotlin + WorkManager + Device Owner base.
- Deploy: Debian + Docker Compose + reverse proxy HTTPS.
- CI: GitHub Actions.

## Funciones implementadas

- RBAC: ADMINISTRADOR / SOPORTE / AUDITORIA.
- Códigos temporales de enrolamiento.
- Identidad individual por dispositivo con rotación/revocación.
- Heartbeat autenticado.
- Inventario Windows: hardware, red, batería, BitLocker, TPM, antivirus.
- IP pública/LAN, SSID y ubicación IP aproximada.
- Estado online/offline e historial.
- Modo Pérdida.
- Inventario y políticas de software.
- Catálogo MSI aprobado.
- Tareas INSTALL/UNINSTALL sin shell remoto.
- Backups PostgreSQL + SHA-256.
- Health/readiness.
- Contenedor backend non-root.
- CI server/Windows/Android.

## Documentación formal

- PRD: docs/PRD.md
- TRD: docs/TRD.md
- UI/UX Design: docs/UI_UX_DESIGN.md
- App Flow: docs/APP_FLOW.md
- Backend Schema: docs/BACKEND_SCHEMA.md
- Development Plan: docs/DEVELOPMENT_PLAN.md
- Traceability Matrix: docs/TRACEABILITY_MATRIX.md
- Technical Documentation: docs/TECHNICAL_DOCUMENTATION.md
- Project Completion: docs/PROJECT_COMPLETION.md
- Changelog: CHANGELOG.md

## Estado

Core backend: cerrado en código y CI.
Windows: cerrado en código; falta validación física y firma Authenticode.
Android: código de provisioning/Keystore/release cerrado; falta validación física Device Owner/QR, keystore corporativo real y canal push rápido.
Activos/Leasing/exportes: pendientes.
Release/piloto: pendientes o externos; el workflow Android release ya existe, pero la firma corporativa y la aceptación física siguen pendientes.

No se declara producción empresarial final hasta completar los criterios de docs/PROJECT_COMPLETION.md.

## Desarrollo

Copie .env.example a .env únicamente en el servidor. Nunca versione secretos, certificados, keystores, contraseñas ni tokens reales.
