# Despliegue inicial en Debian

## Requisitos

- Debian 12/13
- Docker Engine + Docker Compose
- HTTPS delante del API (Traefik, Nginx o Cloudflare Tunnel según política de la empresa)

## Instalación

```bash
git clone https://github.com/LORDMANUEL/rastyreadordelaptopsinterno.git
cd rastyreadordelaptopsinterno
cp .env.example .env
nano .env
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

Genere valores largos y aleatorios para `POSTGRES_PASSWORD`, `ENROLLMENT_TOKEN` y `ADMIN_TOKEN`.

Ejemplo:

```bash
openssl rand -base64 48
```

## Producción

No exponga PostgreSQL a Internet. Publique únicamente la API/panel mediante HTTPS. Restrinja quién conoce el token de enrolamiento y rótelo después de despliegues masivos.

El repositorio es público: nunca suba el archivo `.env`, certificados privados ni credenciales.


## Seguridad del contenedor

La imagen del API se ejecuta como el usuario no privilegiado `assetguard` (UID/GID 10001).

Docker Compose aplica:

- bind del API a `127.0.0.1:8000` por defecto;
- `no-new-privileges`;
- eliminación de capacidades Linux con `cap_drop: ALL`;
- healthcheck interno contra `/ready`.

Si Traefik o Nginx están en contenedores, prefiera conectarlos a una red Docker compartida y no publicar el puerto del API hacia Internet.

Solo cambie `API_BIND_ADDRESS=0.0.0.0` cuando exista una razón de red documentada y firewall/reverse proxy correctamente configurado.


## Verificación de despliegue

Después de levantar el stack:

```bash
docker compose ps
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/ready
docker compose exec backup sh /ops/backup-postgres.sh
ls -lh ./backups
```

Criterio de aceptación:

- PostgreSQL en estado healthy;
- API en estado healthy;
- `/ready` devuelve `database=ok`;
- el API no se ejecuta como root;
- el puerto está ligado a localhost salvo decisión explícita;
- se genera un `.dump` y su `.sha256`;
- el backup del host se incluye en una segunda copia externa.

## TLS / reverse proxy

Este repositorio deja el API ligado a localhost para que el TLS termine en el reverse proxy del servidor.

Producción requiere:

1. DNS del dominio apuntando al servidor;
2. certificado TLS válido;
3. reverse proxy hacia `http://127.0.0.1:8000`;
4. `FORWARDED_ALLOW_IPS` restringido al proxy;
5. firewall permitiendo únicamente los puertos públicos necesarios.

El certificado, dominio y reglas del proxy son datos del servidor real y no deben almacenarse en este repositorio.
