# Ejecución remota de software en Windows

YUDE Asset Guard permite ejecutar tareas de instalación y desinstalación **únicamente** desde el catálogo aprobado.

## Alcance soportado

Actualmente:

- plataforma: Windows;
- formato: MSI;
- instalación: `msiexec /i ... /qn /norestart`;
- desinstalación: `msiexec /x {ProductCode} /qn /norestart`;
- una tarea por ciclo del agente;
- máximo 3 intentos;
- lease de ejecución de 15 minutos.

No existe shell remoto ni campo de comandos arbitrarios.

## Metadatos del catálogo

Para instalar:

- `package_url`: URL HTTPS;
- `package_sha256`: SHA-256 del MSI.

Para desinstalar:

- `product_code`: ProductCode MSI con formato GUID entre llaves.

Ejemplo conceptual:

```json
{
  "name": "Aplicación corporativa",
  "publisher": "Proveedor",
  "approved_version": "1.0.0",
  "policy": "ALLOWED",
  "package_url": "https://servidor.example/app.msi",
  "package_sha256": "<64 caracteres hex>",
  "product_code": "{00000000-0000-0000-0000-000000000000}"
}
```

## Flujo

1. Administrador o Soporte crea una tarea para un dispositivo Windows.
2. El agente consulta sus tareas pendientes después de un heartbeat válido.
3. El agente reclama una tarea.
4. El servidor cambia la tarea a `RUNNING`, incrementa intentos y asigna lease.
5. Para INSTALL:
   - exige HTTPS;
   - limita el MSI a 1 GiB;
   - impide redirecciones a HTTP;
   - verifica SHA-256;
   - valida cabecera MSI/OLE;
   - ejecuta msiexec en modo silencioso.
6. Para UNINSTALL:
   - valida el ProductCode;
   - ejecuta msiexec en modo silencioso.
7. El agente reporta `SUCCEEDED` o `FAILED`.
8. El servidor registra auditoría.

Los códigos MSI 3010 y 1641 se consideran ejecución exitosa con reinicio requerido.

## Recuperación

Si el agente reclama una tarea y no reporta resultado:

- el lease expira;
- la tarea vuelve a `PENDING` mientras no alcance el máximo de intentos;
- después de 3 intentos expira como `FAILED`.

Esto evita tareas bloqueadas indefinidamente.

## Seguridad

El agente no acepta:

- HTTP;
- credenciales embebidas en URL;
- ejecutables EXE arbitrarios;
- scripts PowerShell enviados por servidor;
- argumentos personalizados;
- shell remoto.

Para ampliar formatos en el futuro se debe agregar un ejecutor explícito por tipo de paquete y pruebas específicas.
