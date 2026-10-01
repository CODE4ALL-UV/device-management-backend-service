"""El estado del sistema: si el backend está vivo y si llega a la base.

Son dos preguntas distintas a propósito:

- `/api/system/health` responde sin tocar la base. Es la que consulta Render
  para saber si el servicio sigue vivo. Neon se duerme cuando no se usa, y si
  este chequeo dependiera de ella, Render daría por caído un servidor sano.
- `/api/system/status` sí consulta la base, con un `SELECT 1`. Sirve para
  comprobar a mano, tras un despliegue, que la cadena de conexión es buena.
  Si Neon está dormida la despierta, así que puede tardar unos segundos.
"""

import time

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from neon_storage import engine

router = APIRouter(prefix="/api/system", tags=["Sistema"])


@router.get("/health")
def health():
    """El servicio está arrancado y responde."""
    return {"status": "ok"}


@router.get("/status")
def system_status(response: Response):
    """El servicio y su conexión con Neon."""
    started = time.perf_counter()

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        # El detalle va al log del servidor, no a la respuesta: el mensaje de
        # un fallo de conexión puede llevar el host de la base, y esta ruta es
        # pública.
        print(f"[status] La base de datos no responde: {exc}")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "degraded",
            "database": {"ok": False, "error": type(exc).__name__},
        }

    return {
        "status": "ok",
        "database": {
            "ok": True,
            "latency_ms": round((time.perf_counter() - started) * 1000),
        },
    }
