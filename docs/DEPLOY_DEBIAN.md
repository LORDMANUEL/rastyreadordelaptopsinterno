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
