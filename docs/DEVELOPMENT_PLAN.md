# Development Plan — YUDE Asset Guard

Estado: Plan de cierre
Versión: 1.0
Fecha: 2026-10-13

## Metodología

Regla de trabajo:
1. un frente pequeño;
2. rama;
3. pruebas;
4. CI verde;
5. merge;
6. actualizar documentación;
7. siguiente frente.

No fusionar deuda conocida ni ramas con CI fallido.

## Fase 1 — Backend core
Estado: CERRADA.

Incluye:
- FastAPI/PostgreSQL;
- migraciones;
- auth/RBAC;
- enrolamientos;
- heartbeat;
- auditoría;
- observaciones;
- hardening;
- readiness;
- backups;
- observabilidad.

## Fase 2 — Windows
Estado: CÓDIGO CERRADO / VALIDACIÓN FÍSICA PENDIENTE.

Incluye:
- servicio SCM;
- inventario;
- network/battery/security;
- software inventory;
- update-safe installer;
- rollback;
- logs;
- service recovery;
- software tasks MSI.

Pendiente externo:
- matriz física Win10/11;
- Authenticode.

## Fase 3 — Android
Estado: PARCIAL.

Hecho:
- proyecto Kotlin;
- enrolamiento;
- heartbeat;
- Device Admin/Owner base;
- WorkManager.

Pendiente:
- Android Keystore;
- release signing;
- QR/zero-touch;
- push rápido;
- hardware real.

## Fase 4 — UX/operación empresarial
Estado: PARCIAL.

Hecho:
- login;
- dashboard;
- detalle;
- historial;
- software/policy;
- RBAC visual.

Pendiente:
- UI de catálogo/tareas más completa;
- filtros/búsqueda/paginación;
- exportes;
- administración visual de cuentas si se decide.

## Fase 5 — Activos/Leasing
Estado: PENDIENTE.

Agregar:
- departamento;
- condición;
- propiedad/lease;
- contrato;
- proveedor;
- fechas/costo;
- última auditoría;
- exportes.

No afirmar cumplimiento con Leasing Atlántida sin formato oficial.

## Fase 6 — Release
Estado: PENDIENTE.

- SemVer;
- changelog;
- tag;
- GitHub Release;
- EXE firmado;
- APK/AAB release firmado;
- checksums;
- release notes.

## Fase 7 — Piloto/aceptación
Estado: EXTERNO.

Matriz mínima:
- 3 laptops Windows;
- 1 desktop Windows;
- 2 tablets;
- 2 redes/sucursales;
- reboot;
- offline/online;
- cambio usuario/red;
- Modo Pérdida;
- software task;
- backup/restore.

## Definition of Done

Un frente se cierra cuando:
- implementación completa;
- tests;
- CI verde;
- documentación actualizada;
- riesgos conocidos explicitados;
- sin TODO crítico escondido.

El proyecto se declara producción únicamente tras Fases 1–7 y aceptación externa.
