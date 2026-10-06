# YUDE Asset Guard - Roadmap de cierre a producción

Fecha de revisión: 2026-10-06

## Estado actual

El proyecto ya tiene un MVP funcional y validado por CI en tres frentes:

- backend FastAPI/PostgreSQL con migraciones;
- agente Windows Go compilable como servicio Windows x64;
- aplicación Android Kotlin compilable como APK debug.

También están operativos:

- enrolamiento de dispositivos;
- heartbeat autenticado;
- inventario Windows;
- IP LAN/pública;
- SSID;
- batería;
- BitLocker;
- TPM;
- antivirus registrado;
- asignación de activo/sucursal/responsable;
- Modo Pérdida;
- historial de red/usuario;
- panel web;
- login web con cookie HttpOnly/Secure;
- auditoría básica;
- Docker Compose;
- CI para server/Windows/Android;
- kit Windows con EXE, scripts y SHA-256;
- APK debug con SHA-256.

## Criterio de terminado

El proyecto se considera terminado para producción cuando:

1. ningún secreto corporativo vive en Git;
2. el repositorio y los artefactos tienen el nivel de acceso correcto;
3. usuarios y permisos se administran por roles;
4. enrolamiento no depende de un token global permanente;
5. Windows y Android han sido probados en hardware real;
6. binarios de producción están firmados;
7. Android utiliza provisioning empresarial soportado;
8. backend está detrás de HTTPS con proxy confiable;
9. existen backups, restauración probada y observabilidad;
10. existe un proceso de release reproducible;
11. existe prueba piloto y aceptación documentada.

---

# P0 - Bloqueantes antes de producción

## P0.1 Repositorio privado

Estado actual: el repositorio es PUBLIC.

Antes de almacenar información adicional específica de infraestructura, nombres internos, URLs corporativas, políticas o certificados, el repositorio debe ser privado o migrarse a una organización/repositorio privado.

No incluir nunca:

- .env;
- certificados/llaves privadas;
- tokens;
- contraseñas;
- IPs internas sensibles;
- información de empleados;
- contratos de leasing reales.

## P0.2 RBAC real

Actualmente existe un administrador web único.

Falta implementar:

- tabla de usuarios;
- tabla/enum de roles;
- SUPERADMIN;
- TI;
- AUDITORIA;
- RRHH;
- CONSULTA;
- permisos por endpoint;
- alta/baja de usuarios;
- cambio de contraseña;
- bloqueo/deshabilitación;
- auditoría de login y cambios administrativos.

## P0.3 Enrolamiento seguro

Actualmente existe un ENROLLMENT_TOKEN global.

Debe reemplazarse por códigos de enrolamiento:

- de un solo uso o número limitado de usos;
- con fecha de expiración;
- opcionalmente ligados a sucursal;
- opcionalmente ligados a plataforma;
- revocables;
- auditados.

El token global debe quedar solo como bootstrap de emergencia o eliminarse.

## P0.4 Protección del backend

Falta:

- rate limiting de login/enrolamiento;
- límites de tamaño de request;
- headers de seguridad;
- política explícita de proxy confiable;
- readiness check de PostgreSQL;
- manejo uniforme de errores;
- request/correlation ID;
- protección CSRF para acciones administrativas con cookie;
- paginación de endpoints de listas;
- política de retención de auditoría/historial.

## P0.5 Prueba física Windows

El build x64 pasa CI, pero falta una prueba documentada en Windows real:

- instalar servicio;
- reiniciar Windows;
- comprobar inicio automático;
- comprobar heartbeat;
- comprobar usuario interactivo;
- Wi-Fi;
- Ethernet;
- VPN;
- portátil con batería;
- desktop sin batería;
- BitLocker on/off;
- TPM presente/ausente;
- ESET/Defender;
- actualización/reinstalación;
- desinstalación;
- pérdida temporal de Internet;
- recuperación tras reinicio.

## P0.6 Android Enterprise de producción

El APK actual es funcional como cliente/enrolamiento, pero todavía es una base MDM.

Falta:

- Device Owner validado en dispositivo real;
- QR provisioning;
- configuración administrada;
- política de bloqueo soportada;
- kiosk/lock task solo si se requiere;
- canal de señal rápida para Modo Pérdida (FCM o equivalente);
- manejo de Doze;
- almacenamiento seguro del token;
- firma release;
- proceso de actualización;
- pruebas por versión Android utilizada en la empresa.

No implementar vigilancia silenciosa ni evasión de permisos.

## P0.7 Firma de artefactos

Windows:

- certificado de firma de código;
- Authenticode;
- verificación de firma durante despliegue.

Android:

- keystore de producción;
- signing en GitHub Actions mediante Secrets;
- APK/AAB release;
- nunca subir keystore al repositorio.

## P0.8 Despliegue Debian endurecido

Falta cerrar un despliegue de referencia:

- Debian;
- Docker Compose;
- PostgreSQL no expuesto públicamente;
- Traefik o Nginx;
- HTTPS;
- red Docker interna;
- firewall;
- variables en .env solo en servidor;
- proxy headers configurados de forma restrictiva;
- health/readiness;
- restart policies;
- volúmenes persistentes.

---

# P1 - Necesario para operación empresarial

## P1.1 Backups y restauración

Debe existir:

- backup automático PostgreSQL;
- retención;
- cifrado;
- copia fuera del servidor;
- procedimiento de restore;
- prueba periódica de restore.

## P1.2 Observabilidad

Agregar:

- logs JSON;
- rotación;
- request ID;
- métricas;
- estado de agentes;
- contador online/offline;
- alertas por offline prolongado;
- alertas por fallo repetido de enrolamiento;
- monitor de PostgreSQL;
- health checks del contenedor.

## P1.3 Gestión de activos

Completar ficha corporativa:

- asset tag;
- serial;
- UUID;
- marca/modelo;
- sucursal;
- departamento;
- responsable;
- fecha de asignación;
- estado;
- propiedad/lease;
- contrato;
- proveedor;
- fecha adquisición;
- costo si aplica;
- observaciones;
- fecha última auditoría.

## P1.4 Leasing Atlántida

Todavía falta recibir/confirmar el formato oficial requerido.

Una vez confirmado:

- campos del contrato;
- número de activo;
- serial;
- responsable;
- ubicación;
- condición física;
- última conexión;
- última auditoría;
- exportación Excel/PDF;
- evidencia para auditoría.

No afirmar cumplimiento contractual hasta validar los requisitos oficiales.

## P1.5 Panel administrativo

El panel actual funciona, pero falta UX final:

- filtros;
- búsqueda;
- paginación;
- ficha detallada;
- historial visual;
- filtros SPS/TGU/CBA;
- responsable;
- plataforma;
- estado online/offline;
- compliance;
- exportación CSV/XLSX;
- auditoría;
- gestión de usuarios;
- gestión de enrolamientos.

## P1.6 Retención y privacidad

Definir por política:

- qué telemetría se recopila;
- propósito;
- quién puede verla;
- cuánto tiempo se conserva;
- qué sucede al devolver/baja del activo;
- procedimiento Modo Pérdida;
- activación/desactivación;
- acceso de Auditoría/TI/RRHH.

---

# P2 - Madurez y mantenimiento

## P2.1 Release pipeline

Agregar:

- versionado semántico;
- tag Git;
- GitHub Release;
- changelog;
- EXE release;
- APK release;
- checksums;
- firmas;
- notas de actualización.

## P2.2 Actualización del agente

Diseñar actualización segura:

- manifiesto de versión;
- checksum;
- firma;
- descarga HTTPS;
- rollback;
- canal stable/test.

No implementar auto-update sin validación criptográfica.

## P2.3 Compatibilidad

Validar:

- Windows 10;
- Windows 11;
- x64;
- eventualmente ARM64 si existe hardware;
- Android mínimo real de la flota;
- diferentes fabricantes de tablets.

## P2.4 Pruebas adicionales

Backend:

- auth;
- roles;
- rate limits;
- enrolamientos expirados;
- concurrencia;
- paginación;
- migrations upgrade/downgrade.

Windows:

- unit tests de parsing;
- tests de config;
- HTTP mock;
- retry/backoff;
- servicio.

Android:

- unit tests;
- instrumentation tests;
- Worker;
- almacenamiento seguro;
- provisioning.

## P2.5 Documentación final

Debe existir:

- arquitectura;
- instalación Debian;
- instalación Windows;
- Android provisioning;
- operación diaria;
- recuperación de desastre;
- backup/restore;
- actualización;
- seguridad;
- troubleshooting;
- matriz de roles;
- checklist piloto;
- checklist producción.

---

# Orden recomendado de ejecución

1. Hacer privado el repositorio.
2. RBAC + usuarios.
3. Enrolamientos temporales/one-time.
4. Hardening API y proxy.
5. Windows: prueba física + firma.
6. Android Enterprise real + firma.
7. Deployment Debian/TLS.
8. Backup/restore.
9. Observabilidad/alertas.
10. Ficha de activos + Leasing.
11. UX/exportes.
12. Release pipeline.
13. Piloto controlado.
14. Cierre de aceptación.

---

# Estado estimado

## MVP técnico

Aproximadamente 70% completo.

## Producción empresarial

Aproximadamente 45-50% completo.

La diferencia está principalmente en seguridad operacional, distribución firmada, Android Enterprise, RBAC, despliegue, backups, observabilidad y pruebas físicas.

---

# Definición de aceptación del piloto

Piloto mínimo recomendado:

- 3 laptops Windows;
- 1 desktop Windows;
- 2 tablets Android;
- al menos dos sucursales;
- Wi-Fi y Ethernet;
- reinicio de equipos;
- pérdida de Internet;
- cambio de usuario;
- Modo Pérdida;
- re-enrolamiento;
- actualización de agente;
- restore de base de datos;
- exportación de auditoría.

El proyecto no debe declararse producción final hasta completar y documentar este piloto.
