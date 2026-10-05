# Paso 03 - Red y batería Windows

Estado: VALIDADO LOCALMENTE

## Alcance

- IP LAN IPv4 activa.
- SSID de Wi-Fi cuando exista una interfaz WLAN conectada.
- porcentaje de batería cuando Windows exponga `Win32_Battery`.

## Correcciones de robustez

- descarta loopback y direcciones link-local para la IP LAN;
- no falla si `netsh wlan show interfaces` no devuelve Wi-Fi;
- valida que la línea SSID tenga el formato esperado antes de dividirla;
- descarta porcentajes de batería fuera del rango 0-100;
- equipos de escritorio sin batería reportan `null`.

## Validación local

```text
go test ./...                                  PASS
GOOS=windows GOARCH=amd64 go vet ./...         PASS
GOOS=windows GOARCH=amd64 go build             PASS
```

## Pendiente de prueba física

- portátil conectada por Wi-Fi;
- portátil conectada por Ethernet;
- equipo sin batería;
- equipo con VPN/adaptadores virtuales.
