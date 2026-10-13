# Android MDM — YUDE Asset Guard

## Estado actual

Implementado:
- proyecto Kotlin compilable;
- enrolamiento HTTPS;
- identidad individual;
- heartbeat;
- WorkManager;
- reporte de Android ID, fabricante, modelo, versión, arquitectura y batería;
- DeviceAdminReceiver;
- detección Device Owner / Device Admin;
- recepción de Modo Pérdida desde backend.

## Laboratorio

En equipo recién restablecido:

```bash
adb shell dpm set-device-owner com.yude.assetguard/.YudeDeviceAdminReceiver
```

Luego:
1. abrir app;
2. configurar URL HTTPS;
3. usar código temporal;
4. enrolar;
5. validar heartbeat.

## Pendiente para producción

- almacenamiento de identidad mediante Android Keystore;
- firma release;
- APK/AAB productivo;
- QR provisioning;
- zero-touch si aplica;
- canal push para respuesta rápida;
- pruebas Doze/reboot/offline;
- matriz física por versiones Android reales.

## Límites

No se implementan:
- vigilancia silenciosa;
- bypass de permisos;
- lectura de comunicaciones;
- cámara/micrófono ocultos.
