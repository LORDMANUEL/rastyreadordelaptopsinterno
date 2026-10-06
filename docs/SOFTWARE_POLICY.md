# Política de software

Esta fase agrega catálogo, estado deseado y evaluación de cumplimiento.

## Catálogo

Administrador y Soporte pueden registrar:

- nombre de aplicación;
- fabricante;
- versión aprobada;
- política ALLOWED, REQUIRED o BLOCKED.

Auditoría tiene acceso de consulta.

## Política por equipo

Estados disponibles:

- REQUIRED: la aplicación debe estar presente;
- ABSENT: la aplicación debe estar ausente.

El servidor compara la política con el inventario reportado por el agente y muestra CUMPLE o NO CUMPLE.

## Alcance de esta fase

El módulo actual es de inventario y cumplimiento. No modifica aplicaciones en los equipos.

Una fase posterior de distribución de software deberá trabajar únicamente con paquetes corporativos previamente aprobados y verificables.
