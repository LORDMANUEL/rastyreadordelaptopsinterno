# Gestión empresarial de activos y Leasing-ready

## Alcance

YUDE Asset Guard mantiene una ficha empresarial genérica por dispositivo.

Campos:
- asset tag;
- sucursal;
- departamento;
- responsable;
- estado;
- condición física;
- tipo de propiedad;
- contrato de lease;
- proveedor;
- fecha de adquisición;
- fecha de asignación;
- costo;
- observaciones;
- última auditoría.

## Valores controlados

Estado:
- ACTIVE
- IN_REPAIR
- STORAGE
- RETURNED
- RETIRED

Condición:
- GOOD
- FAIR
- POOR
- DAMAGED

Propiedad:
- OWNED
- LEASED
- OTHER

## Exportes

Activos:
- GET /api/v1/exports/assets.xlsx
- GET /api/v1/exports/assets.pdf

Auditoría:
- GET /api/v1/exports/audit.xlsx
- GET /api/v1/exports/audit.pdf

Roles:
- activos: ADMINISTRADOR, SOPORTE, AUDITORIA;
- auditoría: ADMINISTRADOR, AUDITORIA.

XLSX contiene la ficha completa.
PDF de activos utiliza un subconjunto operacional para mantener legibilidad.

## Leasing

El esquema permite registrar información general de activos arrendados y exportarla.

Esto NO constituye certificación de cumplimiento contractual con Banco Atlántida u otro arrendador.

Para un formato oficial se debe recibir:
1. plantilla/campos oficiales;
2. periodicidad;
3. formato de entrega;
4. reglas obligatorias;
5. evidencia requerida.

Después se crea un mapper/export específico sin alterar el modelo base.

## Auditoría

Toda modificación de ficha usa PATCH /api/v1/devices/{id} y genera DEVICE_UPDATED con actor y cambios.

## UI

Admin y Soporte pueden editar la ficha.
Auditoría solo consulta.
Los tres roles pueden exportar activos.
Solo Admin/Auditoría exportan el log global de auditoría.
