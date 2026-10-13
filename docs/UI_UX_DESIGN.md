# UI/UX Design — YUDE Asset Guard

Estado: Baseline de diseño
Versión: 1.0

## 1. Principios

- Priorizar operación rápida de TI.
- Mostrar estado crítico sin navegar múltiples pantallas.
- No confundir ubicación IP aproximada con GPS.
- Diferenciar claramente lectura, acción y acción destructiva.
- Aplicar RBAC también visualmente, no solo en backend.
- Confirmar acciones sensibles mediante motivo.

## 2. Arquitectura de información

### Vista 1 — Login
Elementos:
- usuario;
- contraseña;
- error de autenticación;
- sin exposición de ADMIN_TOKEN.

### Vista 2 — Dashboard
Tarjetas:
- total de equipos;
- online;
- offline;
- Modo Pérdida.

Tabla principal:
- activo;
- equipo;
- usuario;
- sucursal;
- plataforma;
- IP pública;
- último contacto;
- estado.

### Vista 3 — Detalle de activo
Bloques:
- identidad: asset tag, hostname, serial, UUID;
- hardware: fabricante, modelo, arquitectura;
- seguridad: BitLocker, TPM, antivirus;
- red: LAN, IP pública, SSID;
- ubicación de red aproximada + precisión;
- batería;
- identidad técnica del agente;
- estado offline;
- historial;
- aplicaciones;
- política de software.

Acciones:
- Modo Pérdida;
- revocar identidad técnica;
- actualizar;
- tareas de software cuando corresponda.

## 3. Matriz de visibilidad por rol

| Elemento | Admin | Soporte | Auditoría |
|---|---:|---:|---:|
| Dashboard | Sí | Sí | Sí |
| Detalle activo | Sí | Sí | Sí |
| Historial | Sí | Sí | Sí |
| Inventario software | Sí | Sí | Sí |
| Modo Pérdida | Sí | Sí | No |
| Revocar identidad | Sí | No | No |
| Auditoría global | Sí | No | Sí |
| Crear tarea software | Sí | Sí | No |

## 4. Estados visuales

- ONLINE: indicador positivo.
- OFFLINE: indicador de atención.
- PÉRDIDA: indicador crítico.
- CUMPLE: política satisfecha.
- NO CUMPLE: política no satisfecha.
- RUNNING: tarea en ejecución.
- FAILED: tarea fallida.
- SUCCEEDED: tarea terminada.

## 5. Reglas UX críticas

1. Acciones sensibles solicitan motivo.
2. Auditoría nunca ve controles de escritura.
3. La geolocalización IP siempre muestra precisión estimada.
4. No mostrar tokens de dispositivo.
5. No almacenar credenciales humanas en localStorage/sessionStorage.
6. No permitir comandos libres en administración de software.
7. Errores de API deben mostrar mensaje operacional sin revelar secretos.

## 6. Responsive

El panel actual soporta escritorio y layouts reducidos mediante CSS responsive.

Criterio mínimo:
- 1366x768: operación completa;
- 1024px: tarjetas y detalle en dos columnas;
- <=620px: una columna.

## 7. Estado de implementación

| Área | Estado |
|---|---|
| Login | CUMPLE |
| Dashboard | CUMPLE |
| Tabla dispositivos | CUMPLE |
| Detalle activo | CUMPLE |
| Historial | CUMPLE |
| Inventario software | CUMPLE |
| Política software | CUMPLE |
| RBAC visual | CUMPLE |
| Administración completa de usuarios en UI | PENDIENTE |
| Gestión visual completa del catálogo/tareas | PARCIAL |
| Exportes | PENDIENTE |
| Diseño Android final | PARCIAL |

## 8. Deuda aceptada

El panel es HTML/JS servido por FastAPI. No se requiere migrar a React para declarar el producto funcional. Una migración futura solo se justificará por complejidad/escala, no como requisito de cierre.
