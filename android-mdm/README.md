# YUDE Asset Guard - Android MDM

Cliente para tablets corporativas basado en Android Enterprise / Device Owner.

## Estado actual

El proyecto ya incluye:
- APK Android mínima compilable.
- DeviceAdminReceiver.
- detección de estado Device Owner / Device Admin.
- identificación básica del dispositivo.
- permisos de Internet y conectividad.

## Aprovisionamiento de prueba

En un dispositivo de laboratorio recién restablecido, sin cuentas configuradas, puede probarse Device Owner con ADB:

```bash
adb shell dpm set-device-owner com.yude.assetguard/.YudeDeviceAdminReceiver
```

Android impone restricciones deliberadas a Device Owner. No se intenta evadirlas.

## Siguiente fase

- enrolamiento HTTPS contra FastAPI;
- token individual por tablet;
- heartbeat con batería/red;
- políticas corporativas permitidas;
- modo pérdida;
- QR de provisioning;
- build APK firmado mediante GitHub Actions.

No se implementan funciones de vigilancia personal, captura silenciosa ni lectura de comunicaciones.
