# YUDE Asset Guard

Plataforma interna para inventario, telemetría y recuperación de laptops/tablets corporativas.

> Diseñada para activos propiedad o bajo custodia de la empresa. No implementa keylogging, captura silenciosa de cámara/micrófono, lectura de mensajes ni vigilancia personal.

## Arquitectura

- **Servidor:** Python 3.12 + FastAPI + PostgreSQL
- **Panel web:** HTML/JS inicial servido por FastAPI (React/TypeScript en siguiente iteración)
- **Agente Windows:** Go, ejecutable único y preparado para servicio de Windows
- **Android MDM:** Kotlin/Android Enterprise, pensado para tablets corporativas
- **Despliegue:** Debian + Docker Compose

## Funciones del MVP

- Alta/enrolamiento de dispositivos.
- Heartbeat autenticado.
- Inventario básico de hardware/SO.
- IP LAN/pública reportada por servidor.
- Usuario conectado, hostname, serial/UUID cuando el SO lo permita.
- Estado online/offline.
- Asignación de sucursal, responsable y etiqueta de activo.
- Modo pérdida administrado desde servidor.
- Auditoría de eventos.
- Panel web de consulta.
- Sin almacenamiento de contraseñas del usuario final.

## Privacidad y límites

El sistema está orientado a laptops/tablets corporativas con política interna de uso y aviso de monitoreo. La geolocalización, cuando se implemente, debe usar APIs oficiales del sistema operativo y permisos/políticas corporativas. La ubicación basada en IP es aproximada.

## Estructura

```text
server/         API FastAPI + panel
agent-go/       agente Windows
android-mdm/    cliente Android Enterprise / Device Owner
docs/           arquitectura, despliegue y políticas
```

## Desarrollo

La configuración se realiza mediante variables de entorno. Copie `.env.example` a `.env` únicamente en el servidor y nunca suba secretos al repositorio.

## Estado

MVP técnico funcional con backend, agente Windows, Android, panel web, historial y CI.

El proyecto aún no debe considerarse producción final. Los bloqueantes restantes y el criterio de aceptación están documentados en:

- `docs/PROJECT_COMPLETION.md`
- `docs/DEPLOY_DEBIAN.md`
- `docs/AUTHENTICATION.md`
- `docs/ANDROID_MDM.md`

Estado estimado actual:

- MVP técnico: ~70%.
- Producción empresarial: ~45-50%.
