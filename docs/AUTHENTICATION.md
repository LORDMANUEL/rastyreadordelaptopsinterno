# Autenticación del panel web

El panel web ya no requiere escribir `ADMIN_TOKEN` en el navegador.

## Variables requeridas

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD_SALT=<hex>
ADMIN_PASSWORD_HASH=<scrypt hex>
SESSION_SECRET=<random>
SESSION_TTL_SECONDS=28800
```

Genere los valores directamente dentro del contenedor/entorno del servidor:

```bash
cd server
python -m app.hash_password
```

El comando solicita la contraseña sin imprimirla y devuelve únicamente:

- `ADMIN_PASSWORD_SALT`
- `ADMIN_PASSWORD_HASH`
- `SESSION_SECRET`

Copie esos valores al archivo `.env` del servidor.

## Sesiones

Al iniciar sesión correctamente:

- el servidor genera una sesión firmada con HMAC-SHA256;
- la cookie es `HttpOnly`;
- la cookie utiliza `Secure`;
- `SameSite=Strict`;
- no se almacena la contraseña en el navegador;
- no se almacena `ADMIN_TOKEN` en `localStorage` ni `sessionStorage`.

El TTL predeterminado es 8 horas.

## ADMIN_TOKEN

`ADMIN_TOKEN` se conserva para automatizaciones, pruebas y futuras integraciones API.

No debe utilizarse como contraseña del panel web ni exponerse en JavaScript.

## HTTPS

Como la cookie utiliza el atributo `Secure`, el acceso normal debe publicarse mediante HTTPS.

En producción:

```text
Browser
   |
 HTTPS
   v
Traefik / Nginx / Cloudflare
   |
   v
FastAPI
```

## Rotación

Para invalidar todas las sesiones web existentes, cambie `SESSION_SECRET` y reinicie el API.

Para cambiar la contraseña administrativa, vuelva a ejecutar:

```bash
python -m app.hash_password
```

y reemplace los valores en `.env`.
