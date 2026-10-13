# App Flow — YUDE Asset Guard

Estado: Baseline funcional
Versión: 1.0

## 1. Flujo administrativo

```text
Usuario TI
  -> Login HTTPS
  -> Sesión firmada
  -> Dashboard
  -> Selecciona activo
      -> Ver telemetría/historial
      -> Modo Pérdida
      -> Inventario software
      -> Política software
      -> Tareas de software
      -> Auditoría
```

## 2. Flujo de enrolamiento Windows

```text
Administrador crea código temporal
  -> install.ps1 recibe URL + código
  -> valida HTTPS
  -> instala servicio
  -> agente recopila identidad hardware
  -> POST /api/v1/enroll
  -> servidor consume código
  -> emite token individual
  -> agente elimina código temporal
  -> guarda token protegido
  -> heartbeat periódico
```

## 3. Flujo heartbeat

```text
Agente
  -> inventario/usuario/red
  -> POST /api/v1/heartbeat Bearer <device-token>
  -> servidor valida identidad/expiración
  -> actualiza dispositivo
  -> detecta red/usuario/offline-restored
  -> actualiza GeoIP si cambia IP
  -> rota token si corresponde
  -> responde frecuencia + estado Modo Pérdida
```

## 4. Flujo Modo Pérdida

```text
Admin/Soporte
  -> motivo obligatorio
  -> POST lost-mode
  -> audit event
  -> heartbeat pasa a 60s
  -> cada heartbeat genera observación
  -> panel muestra estado crítico
```

## 5. Flujo de inventario software Windows

```text
Agente Windows
  -> lee uninstall registry 64/32
  -> normaliza aplicaciones
  -> POST /api/v1/software-inventory
  -> servidor marca presentes/ausentes
  -> panel muestra inventario
```

## 6. Flujo de tarea de software Windows

```text
Admin/Soporte
  -> selecciona catálogo aprobado
  -> crea INSTALL o UNINSTALL
  -> servidor valida plataforma/metadatos
  -> agente consulta tareas
  -> reclama una tarea
  -> estado RUNNING + lease
  -> INSTALL:
       HTTPS download
       SHA-256
       validar MSI/OLE
       msiexec /i /qn /norestart
     UNINSTALL:
       validar ProductCode
       msiexec /x /qn /norestart
  -> agente reporta SUCCEEDED/FAILED
  -> servidor audita
```

No existe flujo de shell remoto.

## 7. Flujo Android actual

```text
Tablet corporativa reseteada
  -> escanea QR de provisioning
  -> Android descarga APK release por HTTPS y valida checksum
  -> app queda como Device Owner
  -> recibe server_url + código temporal
  -> enrola identidad individual
  -> token se guarda cifrado con Android Keystore
  -> WorkManager heartbeat
  -> backend
```

Pendiente de producción:
- validar QR/Device Owner en tablets físicas;
- usar keystore corporativo real para firma;
- validar reboot/Doze/pérdida-retorno de Internet/update;
- canal push para respuesta rápida.

## 8. Flujo backup/restore

```text
backup container
  -> pg_dump
  -> /backups/<timestamp>.dump
  -> SHA-256
  -> retención
  -> copia off-host externa

Restore:
  -> verificar checksum
  -> detener escrituras
  -> pg_restore
  -> /ready
  -> smoke tests
```
