# Android MDM — YUDE Asset Guard

## Estado de código

Implementado:
- Kotlin + target SDK 35;
- enrolamiento HTTPS;
- token individual por tablet;
- token cifrado con AES-GCM y clave en Android Keystore;
- migración automática desde token legacy plano;
- heartbeat manual y WorkManager;
- reporte de Android ID, fabricante, modelo, versión, arquitectura y batería;
- DeviceAdminReceiver;
- Device Owner base;
- Android 12+ GET_PROVISIONING_MODE;
- ADMIN_POLICY_COMPLIANCE;
- enrolamiento automático desde extras del provisioning;
- generador reproducible de payload/QR;
- configuración de release signing mediante secretos;
- workflow Android Release.

## Laboratorio con ADB

Dispositivo recién restablecido y sin cuentas:

```bash
adb shell dpm set-device-owner com.yude.assetguard/.YudeDeviceAdminReceiver
```

Luego abra la app y use URL HTTPS + código temporal.

## QR provisioning

Requisitos:
- APK release accesible por HTTPS;
- archivo APK local idéntico al publicado;
- URL HTTPS del backend;
- código temporal de enrolamiento.

Instalar generador QR:

```bash
python -m pip install -r ops/requirements-android-qr.txt
```

Generar:

```bash
python ops/generate-android-provisioning-qr.py \
  --apk app-release.apk \
  --apk-url https://downloads.example.com/app-release.apk \
  --server-url https://assets.example.com \
  --enrollment-token CODIGO_TEMPORAL \
  --json-output provisioning.json \
  --qr-output provisioning.png
```

El QR contiene:
- componente DPC;
- ubicación HTTPS del APK;
- checksum SHA-256 del APK;
- server_url;
- código temporal.

Use códigos de vida corta porque quedan embebidos en el QR.

## Release signing

Secrets requeridos en GitHub:

- ANDROID_KEYSTORE_BASE64
- ANDROID_KEYSTORE_PASSWORD
- ANDROID_KEY_ALIAS
- ANDROID_KEY_PASSWORD

Workflow:
- .github/workflows/android-release.yml

El keystore nunca debe versionarse.

## Estado pendiente externo

Código Android de producción: cerrado salvo canal push rápido.

Requiere validación real:
- tablet reseteada;
- QR provisioning;
- Device Owner;
- reboot;
- Doze;
- pérdida/retorno de Internet;
- actualización de APK;
- firma con keystore corporativo real.

## Respuesta rápida

WorkManager continúa siendo el canal periódico.
Para Modo Pérdida casi inmediato sigue pendiente integrar FCM o canal corporativo equivalente.

## Límites

No se implementan vigilancia silenciosa, bypass de permisos, lectura de comunicaciones, cámara/micrófono ocultos ni extracción de datos personales.
