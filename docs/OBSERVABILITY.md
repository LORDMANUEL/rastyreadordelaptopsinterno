# Observabilidad de dispositivos

YUDE Asset Guard mantiene un estado operativo simple y auditable.

## Online / Offline

Un equipo se considera offline cuando su último heartbeat supera `HEARTBEAT_OFFLINE_SECONDS` (600 segundos por defecto).

El servidor ejecuta un monitor interno cada 60 segundos.

Cuando un equipo cruza el umbral:

- establece `offline_since`;
- registra `DEVICE_OFFLINE`;
- no vuelve a registrar el mismo evento mientras continúe offline.

Cuando el equipo vuelve a enviar heartbeat:

- registra `DEVICE_ONLINE_RESTORED`;
- incluye la duración aproximada del periodo offline;
- limpia `offline_since`.

## Resumen operativo

Endpoint:

```text
GET /api/v1/operations/summary
```

Disponible para:

- ADMINISTRADOR;
- SOPORTE;
- AUDITORIA.

Devuelve:

- total;
- online;
- offline;
- Modo Pérdida;
- distribución por plataforma;
- fecha de generación.

## Panel

La ficha del activo muestra `Offline desde` cuando el dispositivo está marcado fuera de línea.

## Escalado

El monitor actual es apropiado para una instancia API y una flota pequeña/mediana.

Si en el futuro se ejecutan múltiples workers/replicas del API, el monitor deberá moverse a un scheduler único (por ejemplo un worker dedicado o un job externo) para evitar trabajo duplicado.
