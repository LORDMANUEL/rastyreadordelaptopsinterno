# Backup y restauración de PostgreSQL

YUDE Asset Guard incluye un servicio `backup` en Docker Compose.

## Comportamiento

Por defecto:

- crea un backup cada 24 horas;
- usa formato custom de PostgreSQL;
- comprime el dump;
- genera `SHA256`;
- conserva 14 días;
- guarda los archivos en un directorio del host Debian (`./backups` por defecto).

Los valores pueden cambiarse en el archivo `.env` del servidor:

```env
BACKUP_HOST_DIR=./backups
BACKUP_RETENTION_DAYS=14
BACKUP_INTERVAL_SECONDS=86400
```

No se deben almacenar secretos reales en Git.

## Ejecutar un backup manual

```bash
docker compose exec backup /ops/backup-postgres.sh
```

## Listar backups

```bash
docker compose exec backup sh -c 'ls -lh /backups'
```

## Verificar checksum

```bash
docker compose exec backup sh -c 'cd /backups && sha256sum -c NOMBRE.dump.sha256'
```

## Restauración

La restauración es deliberadamente manual.

Detenga temporalmente el API antes de restaurar:

```bash
docker compose stop api
```

Ejecute:

```bash
docker compose run --rm backup /ops/restore-postgres.sh /backups/NOMBRE.dump
```

Luego:

```bash
docker compose start api
```

## Copia fuera del servidor

El directorio local facilita integrar los dumps con la política de backup del host, pero no protege frente a pérdida total del servidor.

Para producción debe existir una segunda copia:

- servidor distinto;
- almacenamiento S3 compatible;
- NAS;
- o medio cifrado fuera del host.

## Prueba de restore

El sistema no debe considerarse respaldado solo porque genera archivos.

Como mínimo una vez al mes:

1. crear backup;
2. copiarlo a un entorno de prueba;
3. verificar SHA-256;
4. restaurar;
5. levantar API;
6. comprobar inventario, usuarios, auditoría e historial;
7. registrar resultado de la prueba.
