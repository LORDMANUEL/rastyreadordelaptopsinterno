# Enrolamiento temporal de dispositivos

YUDE Asset Guard usa códigos temporales de bootstrap para registrar equipos nuevos.

## Flujo

1. TI crea un código temporal en el servidor.
2. El código puede limitarse por plataforma, sucursal, duración y cantidad de usos.
3. El instalador Windows o Android lo utiliza una sola vez para registrar el equipo.
4. El servidor entrega una identidad técnica individual del dispositivo.
5. El agente elimina el código temporal de su configuración y continúa con su identidad propia.
6. La identidad del dispositivo rota automáticamente de acuerdo con la política configurada.

El usuario final no necesita escribir ni administrar códigos.

## Crear un código

Desde el servidor:

```bash
docker compose exec api python -m app.manage_enrollment_codes create \
  --label "Lote SPS" \
  --branch SPS \
  --platform windows \
  --expires-minutes 60 \
  --max-uses 10 \
  --created-by admin
```

El comando muestra el valor del código solo al crearlo. En base de datos se guarda únicamente su hash.

## Listar códigos

```bash
docker compose exec api python -m app.manage_enrollment_codes list
```

## Revocar un código

```bash
docker compose exec api python -m app.manage_enrollment_codes revoke <ID>
```

## Windows

El parámetro histórico del instalador sigue llamándose `EnrollmentToken` por compatibilidad, pero debe recibir el código temporal:

```powershell
.\install.ps1 -ServerUrl "https://assets.example.com" -EnrollmentToken "CODIGO_TEMPORAL"
```

Después del enrolamiento, el agente reemplaza ese valor por su identidad técnica individual.

## Compatibilidad temporal

El token global queda deshabilitado por defecto:

```env
ALLOW_LEGACY_ENROLLMENT_TOKEN=false
```

Solo para migración o pruebas controladas puede habilitarse explícitamente:

```env
ALLOW_LEGACY_ENROLLMENT_TOKEN=true
ENROLLMENT_TOKEN=<valor temporal de compatibilidad>
```

No debe usarse este modo como configuración normal de producción.
