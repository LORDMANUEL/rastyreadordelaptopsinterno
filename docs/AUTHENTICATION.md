# Autenticación y autorización

## Usuarios humanos

Las cuentas viven en user_accounts.

Roles:
- ADMINISTRADOR;
- SOPORTE;
- AUDITORIA.

Las credenciales se derivan con scrypt y se almacenan como salt + digest.

Administración local:

```bash
docker compose exec api python -m app.manage_accounts set admin ADMINISTRADOR
docker compose exec api python -m app.manage_accounts set soporte SOPORTE
docker compose exec api python -m app.manage_accounts set auditoria AUDITORIA
docker compose exec api python -m app.manage_accounts list
```

## Sesiones

- HMAC firmado con SESSION_SECRET;
- cookie HttpOnly;
- Secure;
- SameSite=Strict;
- TTL configurable;
- rol/cuenta activa revalidado en cada request.

## ADMIN_TOKEN

Se conserva para automatización/integración técnica y pruebas.
No se usa como contraseña del panel.

## Dispositivos

Cada equipo tiene identidad técnica independiente:
- token aleatorio;
- hash almacenado en servidor;
- expiración;
- rotación automática;
- revocación.

## Enrolamiento

El flujo normal usa códigos temporales:
- expiración;
- límite de usos;
- sucursal opcional;
- plataforma opcional;
- revocación;
- auditoría.

## HTTPS

Producción requiere HTTPS delante de FastAPI.
Windows rechaza server_url sin HTTPS.
