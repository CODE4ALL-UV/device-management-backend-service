# device-management-backend-service
Repositorio Back-end para el módulo Infraestructura y Dispositivos.

El estado del sistema. Son dos preguntas distintas a propósito:

| Ruta | Para qué |
|---|---|
| `GET /api/system/health` | Si el servicio está vivo. No toca la base: es la que consulta Render, y Neon dormida no debe hacerle creer que el servidor cayó. |
| `GET /api/system/status` | Si llega a Neon (`SELECT 1`). Para comprobar a mano tras un despliegue que la cadena de conexión es buena. |

No escribe ninguna tabla. Solo necesita `neon-storage`.

## Cómo lo monta el gateway

`device_management_service/routes.py` tiene `register(app)`, que añade las rutas de este
servicio a una aplicación de FastAPI. El gateway lo llama para cada servicio, y
`device_management_service/main.py` hace lo mismo para arrancarlo solo.

## Correrlo

Lo normal es correrlo dentro del gateway (repo `Back-end`), que monta todos
los servicios juntos. Para correrlo solo hace falta `neon-storage`
clonado al lado:

```powershell
$env:PYTHONPATH = "..\neon-storage-backend-service"
pip install -r requirements.txt -r ..\neon-storage-backend-service\requirements.txt
copy .env.example .env
uvicorn device_management_service.main:app --reload
```

## Pruebas

```bash
pytest tests
```

No tocan Neon: usan una base SQLite temporal. Buscan `neon-storage` en los
repos hermanos, así que funcionan igual con los repos
clonados uno al lado del otro que dentro de `services/` del gateway.
