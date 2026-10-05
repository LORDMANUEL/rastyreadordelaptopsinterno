# Paso 04 - CI del agente Windows

Estado: VALIDADO LOCALMENTE

## Objetivo

Evitar que GitHub publique un agente Windows que solo compile parcialmente.

## Controles

- `go mod tidy` no debe dejar cambios sin confirmar;
- `gofmt -l` debe devolver lista vacía;
- `go vet ./...` para host Linux;
- `GOOS=windows GOARCH=amd64 go vet ./...` para los archivos Windows;
- build Windows x64 con `CGO_ENABLED=0`;
- empaquetado del kit solo si todas las verificaciones anteriores pasan.

## Validación local

```text
gofmt -l .                                    VACÍO
GOOS=windows GOARCH=amd64 go vet ./...        PASS
GOOS=windows GOARCH=amd64 go build            PASS
```
