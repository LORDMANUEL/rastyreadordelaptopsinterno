# Traceability Matrix — YUDE Asset Guard

Fecha: 2026-10-13

Leyenda:
- CUMPLE: implementado y cubierto por código/pruebas/CI.
- PARCIAL: existe base funcional pero falta cierre productivo.
- EXTERNO: depende de hardware, certificados, DNS o configuración fuera del repositorio.
- PENDIENTE: no implementado aún.

| Req | Fuente | Implementación principal | Evidencia/prueba | Estado |
|---|---|---|---|---|
| FR-001 | PRD | enrollment_codes + /enroll | tests enrolamiento | CUMPLE |
| FR-002 | PRD/TRD | devices.token_hash | tests auth device | CUMPLE |
| FR-003 | PRD/TRD | auth lifecycle | tests rotation/revoke | CUMPLE |
| FR-004 | PRD | /heartbeat + agentes | API tests/CI | CUMPLE |
| FR-005 | PRD | inventory_windows.go | Go build/vet | CUMPLE |
| FR-006 | PRD | firstLANIP + SSID + request.client | tests/CI | CUMPLE |
| FR-007 | PRD | inventory_windows.go | Go build/vet | CUMPLE |
| FR-008 | PRD | network_geo.py | backend tests | CUMPLE |
| FR-009 | PRD | device_observations | API tests | CUMPLE |
| FR-010 | PRD | offline monitor | tests + operations summary | CUMPLE |
| FR-011 | PRD | lost-mode endpoint/UI | API tests | CUMPLE |
| FR-012 | PRD | software inventory | tests + Go CI | CUMPLE |
| FR-013 | PRD | software_catalog | migrations/tests | CUMPLE |
| FR-014 | PRD/TRD | software tasks + MSI executor | tests + Go CI | CUMPLE EN CÓDIGO |
| FR-015 | PRD/UI | static panel | CI/import/manual browser | CUMPLE |
| FR-016 | PRD | user_accounts/RBAC | test_rbac.py | CUMPLE |
| FR-017 | PRD | audit_events | API tests | CUMPLE |
| FR-018 | PRD | Android API/Worker + SecureStore | Android debug/release CI | CUMPLE |
| FR-019 | PRD | DeviceOwner + provisioning compliance | Android release CI | CUMPLE EN CÓDIGO / EXTERNO FÍSICO |
| FR-020 | PRD | QR provisioning generator | CI payload test | CUMPLE EN CÓDIGO / EXTERNO FÍSICO |
| FR-021 | PRD | Authenticode | certificado externo | EXTERNO |
| FR-022 | PRD | secret-backed Android release workflow | release config CI | CUMPLE EN CÓDIGO / REQUIERE SECRETS |
| FR-023 | PRD | export endpoints + UI | API tests | CUMPLE |
| FR-024 | PRD | enterprise asset fields | migration/API tests | CUMPLE GENERICO / MAPEADO OFICIAL EXTERNO |
| NFR-001 | TRD | HTTPS Windows enforcement | Go code/CI | CUMPLE |
| NFR-002 | TRD | Docker USER assetguard | CI image inspect | CUMPLE |
| NFR-003 | TRD | Compose DB private | compose smoke test | CUMPLE |
| NFR-004 | TRD | http_security.py | test_http_security.py | CUMPLE |
| NFR-005 | TRD | /health /ready | compose smoke test | CUMPLE |
| NFR-006 | TRD | backup service/scripts | CI smoke/checksum | CUMPLE |
| NFR-007 | TRD | restore docs/script | documentation | CUMPLE EN REPO |
| NFR-008 | TRD | agent.log rotation | Go CI | CUMPLE |
| NFR-009 | TRD | GitHub Actions | main CI | CUMPLE |
| NFR-010 | TRD | repo private/protected | GitHub settings | EXTERNO |
| NFR-011 | TRD | artifact signing | cert/keystore | EXTERNO/PENDIENTE |
| NFR-012 | PRD | pilot hardware | acceptance execution | EXTERNO |

## Resultado

Documentación de producto/arquitectura: CUMPLE.
Backend core: CUMPLE.
Windows software path: CUMPLE EN CÓDIGO.
Android Enterprise productivo: PARCIAL.
Activos/Leasing/exportes: PENDIENTE.
Release/piloto: EXTERNO/PENDIENTE.

No declarar 100% producción mientras existan estados PARCIAL/EXTERNO/PENDIENTE críticos.
