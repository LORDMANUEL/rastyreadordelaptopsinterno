# Backend Schema — YUDE Asset Guard

Estado: Baseline de esquema
Fuente de verdad: modelos SQLAlchemy + Alembic

## devices

PK: id UUID-string.

Campos principales:
- hostname, serial, platform;
- os_version, architecture, agent_version;
- token_hash;
- auth_issued_at, auth_expires_at, auth_revoked_at, auth_generation;
- asset_tag, branch, assigned_to;
- username, lan_ip, public_ip, wifi_ssid;
- geo_country_code/name, region, city, accuracy, updated_at;
- manufacturer, model, hardware_uuid;
- battery_percent, bitlocker_status, tpm_status, antivirus_status;
- lost_mode, offline_since;
- created_at, last_seen.

## audit_events

- id;
- event_type;
- device_id nullable;
- actor;
- detail;
- created_at.

Propósito: trazabilidad de acciones humanas/sistema/agente.

## device_observations

- id;
- device_id;
- reason;
- username;
- lan_ip/public_ip/wifi_ssid;
- geolocalización aproximada;
- batería;
- created_at.

## user_accounts

- id;
- username unique;
- auth_salt;
- auth_digest;
- role;
- is_active;
- created_at/updated_at/last_login.

Roles válidos:
- ADMINISTRADOR;
- SOPORTE;
- AUDITORIA.

## enrollment_codes

- id;
- code_hash unique;
- label;
- branch;
- platform;
- expires_at;
- max_uses/use_count;
- created_by;
- created_at/last_used_at/revoked_at.

## installed_applications

Unique: device_id + app_key.

- id;
- device_id;
- app_key;
- name/version/publisher/source;
- is_present;
- first_seen/last_seen.

## software_catalog

- id;
- name;
- publisher;
- approved_version;
- policy: ALLOWED | REQUIRED | BLOCKED;
- package_url;
- package_sha256;
- product_code;
- created_by;
- created_at/updated_at.

## device_software_assignments

Unique: device_id + catalog_id.

- id;
- device_id;
- catalog_id;
- desired_state: REQUIRED | ABSENT;
- assigned_by;
- assigned_at.

## device_software_tasks

- id;
- device_id;
- catalog_id;
- action: INSTALL | UNINSTALL;
- status: PENDING | RUNNING | SUCCEEDED | FAILED;
- attempts;
- created_by;
- created_at;
- started_at;
- lease_expires_at;
- completed_at;
- result_detail.

## Integridad lógica

Aunque varios vínculos son UUID-string sin FK física en el modelo actual, la API valida existencia/propiedad antes de crear o completar relaciones.

Deuda recomendada futura:
- evaluar FKs explícitas con ON DELETE controlado cuando la política de retención esté cerrada.

## Migraciones

Secuencia actual:
- 0001 initial;
- 0002 extended inventory;
- 0003 device observations;
- 0004 user accounts;
- 0005 auth lifecycle;
- 0006 network geolocation;
- 0007 software inventory;
- 0008 enrollment codes;
- 0009 software policy catalog;
- 0010 offline observability;
- 0011 software task queue;
- 0012 Windows software execution.

## Retención

Pendiente de política empresarial final:
- audit_events;
- device_observations;
- software task results.

No eliminar automáticamente datos auditables hasta acordar retención.
