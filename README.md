# device-management-backend-service · Infraestructura y dispositivos

Este es el microservicio de **infraestructura y dispositivos** de Code4All. Su
trabajo es decir **si el sistema está funcionando**: si el backend está
arrancado y si llega a la base de datos de Neon.

Parece poco, pero resuelve un problema real del despliegue en Render: para
saber si un servicio sigue vivo, Render le pregunta cada cierto tiempo a una
ruta. Si esa ruta dependiera de la base y Neon estuviera dormida (se duerme
cuando no se usa), Render creería que el servidor se cayó y lo reiniciaría sin
motivo. Por eso aquí hay dos preguntas separadas a propósito.

> **Sobre el nombre:** en el diseño de la arquitectura este recuadro se llama
> «Infraestructura y dispositivos», pero hoy no gestiona ningún dispositivo ni
> periférico. Lo que tiene que ver con hardware vive en otros servicios: el
> teclado Braille en
> [accessibility](https://github.com/CODE4ALL-UV/accessibility-backend-service)
> y la cámara de señas en
> [multimodal-interaction](https://github.com/CODE4ALL-UV/multimodal-interaction-backend-service).
> Las preferencias de accesibilidad de cada estudiante se manejan en la app.

## Las rutas

Las dos son públicas: no piden token.

### `GET /api/system/health` — ¿está vivo?

```json
{ "status": "ok" }
```

Responde al instante y **no toca la base**. Es la ruta que consulta Render
(`healthCheckPath` en el `render.yaml` del gateway). Si responde, el servidor
está arrancado y atendiendo peticiones; no dice nada de Neon.

### `GET /api/system/status` — ¿llega a la base?

Abre una conexión con la base, ejecuta `SELECT 1` y mide cuánto tardó.

Si todo va bien, responde 200:

```json
{ "status": "ok", "database": { "ok": true, "latency_ms": 42 } }
```

Si la base no responde, responde **503**:

```json
{ "status": "degraded", "database": { "ok": false, "error": "OperationalError" } }
```

En `error` solo va el **tipo** del error, nunca el mensaje completo. El mensaje
de un fallo de conexión puede llevar el host de Neon, y como la ruta es
pública, no conviene mostrarlo. El detalle completo queda en el log del
servidor (`[status] La base de datos no responde: ...`).

Sirve para comprobar a mano, después de un despliegue, que la cadena de
conexión está bien. Si Neon estaba dormida, esta ruta la despierta, así que la
primera vez puede tardar unos segundos (y eso se ve en `latency_ms`).

## Cómo se usan en el despliegue

Después de desplegar el gateway en Render se revisan las dos:

```
https://code4all-gateway.onrender.com/api/system/health   → {"status": "ok"}
https://code4all-gateway.onrender.com/api/system/status   → "database": {"ok": true, ...}
```

Si `health` responde y `status` da 503, el servidor está bien pero la
`DATABASE_URL` está mal o Neon no responde.

## Cómo lo monta el gateway

Todos los servicios de Code4All siguen el mismo contrato:
`device_management_service/routes.py` tiene una función `register(app)` que
añade las rutas de este servicio a una aplicación de FastAPI. El
[gateway](https://github.com/CODE4ALL-UV/Back-end) trae este repositorio como
submódulo en `services/` y llama a esa función al arrancar.
`device_management_service/main.py` hace lo mismo para correrlo solo.

No lee ni escribe ninguna tabla. Solo usa la conexión (`engine`) de
[neon-storage](https://github.com/CODE4ALL-UV/neon-storage-backend-service).

## Estructura

```
device_management_service/
├── routes.py                  register(app): lo único que llama el gateway
├── main.py                    arranque independiente (lee el .env)
└── presentation/api/
    └── system_routes.py       /api/system/health y /api/system/status
tests/
├── conftest.py
└── test_system_routes.py
```

## Variables de entorno

| Variable | Para qué | ¿Obligatoria? |
|---|---|---|
| `DATABASE_URL` | La cadena de conexión de Neon. | Sí |

Ojo: `DATABASE_URL` hace falta **incluso para `/health`**. neon-storage la lee
en cuanto se importa, y sin ella el servicio no arranca. Lo que no hace falta
es que Neon esté despierta: la conexión solo se abre en `/status`.

## Correrlo

Lo normal es correrlo dentro del gateway (repo `Back-end`), que monta todos
los servicios juntos. Para correrlo solo hace falta `neon-storage` clonado al
lado:

```powershell
$env:PYTHONPATH = "..\neon-storage-backend-service"
pip install -r requirements.txt -r ..\neon-storage-backend-service\requirements.txt
copy .env.example .env
uvicorn device_management_service.main:app --reload
```

## Pruebas

```powershell
pytest tests
```

No tocan Neon: `conftest.py` fuerza una base SQLite temporal y busca
`neon-storage` en los repos hermanos, así que funcionan igual con los repos
clonados uno al lado del otro que dentro de `services/` del gateway.

`test_system_routes.py` comprueba tres cosas:

- `/health` responde `{"status": "ok"}` sin necesitar la base.
- `/status` llega a la base y responde `ok: true`.
- Cuando la base falla, `/status` responde 503 con el tipo de error y **sin**
  filtrar el host de la base en la respuesta.

En GitHub, cada push o pull request a `main` corre las pruebas con cobertura y
la sube a Codacy (`.github/workflows/codacy-coverage.yml`).

## Cosas a tener en cuenta

- `/health` no informa de la versión ni del commit desplegado.
- `/status` no tiene un tiempo de espera propio: si Neon tarda en despertar,
  la respuesta tarda lo mismo.
- Las rutas solo responden a `GET`. Un monitor que pregunte con `HEAD` recibe
  405.

## Los repositorios de Code4All

| Parte | Repositorio |
|---|---|
| App (Flutter) | [Front-end](https://github.com/CODE4ALL-UV/Front-end) |
| API Gateway | [Back-end](https://github.com/CODE4ALL-UV/Back-end) |
| Gestión de usuarios | [user-management-backend-service](https://github.com/CODE4ALL-UV/user-management-backend-service) |
| Curso y contenidos de Python | [course-content-backend-service](https://github.com/CODE4ALL-UV/course-content-backend-service) |
| Ejercicios y evaluación | [assessment-backend-service](https://github.com/CODE4ALL-UV/assessment-backend-service) |
| Progreso y seguimiento | [progress-tracking-backend-service](https://github.com/CODE4ALL-UV/progress-tracking-backend-service) |
| Accesibilidad y adaptación | [accessibility-backend-service](https://github.com/CODE4ALL-UV/accessibility-backend-service) |
| Interacción multimodal | [multimodal-interaction-backend-service](https://github.com/CODE4ALL-UV/multimodal-interaction-backend-service) |
| **Infraestructura y dispositivos** | **este repositorio** |
| Capa de datos compartida (Neon) | [neon-storage-backend-service](https://github.com/CODE4ALL-UV/neon-storage-backend-service) |
