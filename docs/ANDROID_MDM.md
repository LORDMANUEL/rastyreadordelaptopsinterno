# Aprovisionamiento Android MDM

YUDE Asset Guard para Android está diseñado para tablets corporativas mediante Android Enterprise / Device Owner.

## Prueba de laboratorio con ADB

El dispositivo debe estar recién restablecido y sin cuentas configuradas.

1. Instalar el APK debug.
2. Ejecutar:

```bash
adb shell dpm set-device-owner com.yude.assetguard/.YudeDeviceAdminReceiver
```

3. Abrir YUDE Asset Guard.
4. Ingresar la URL HTTPS del servidor.
5. Ingresar un token temporal de enrolamiento.
6. Pulsar **Enrolar tablet**.

La app recibe y conserva un token individual del dispositivo.

## Heartbeat

La aplicación dispone de:

- heartbeat manual para pruebas;
- heartbeat periódico mediante WorkManager;
- reporte de Android ID, fabricante, modelo, versión Android, arquitectura y batería;
- recepción del estado de Modo Pérdida desde el backend.

Android limita WorkManager a intervalos periódicos mínimos establecidos por el sistema. Para una futura respuesta de Modo Pérdida casi inmediata se implementará FCM o un canal corporativo equivalente, sin evasión de controles del sistema operativo.

## Producción

Para una flota real debe utilizarse provisioning Android Enterprise mediante QR/zero-touch o el mecanismo permitido por el fabricante y la política de la empresa.
