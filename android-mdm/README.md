# YUDE Asset Guard — Android MDM

Cliente corporativo Android Enterprise / Device Owner.

## Implementado

- enrolamiento HTTPS;
- identidad individual;
- almacenamiento AES-GCM con Android Keystore;
- heartbeat + WorkManager;
- Device Admin/Device Owner;
- Android 12+ provisioning mode/compliance;
- auto-enrollment desde QR extras;
- generador de payload/QR;
- release signing por GitHub Secrets.

## CI

CI normal:
- debug APK;
- release build sin secretos para validar configuración;
- provisioning payload generator.

Release firmado:
- workflow Android Release;
- solo corre cuando existen los cuatro Secrets de firma.

## Provisioning

Consulte docs/ANDROID_MDM.md.

## Seguridad

No se versionan keystores ni credenciales.
No se implementan funciones de vigilancia personal ni evasión de controles Android.
