"""Lo que este microservicio aporta al API Gateway.

El gateway (repo Back-end) llama a `register(app)` de cada servicio, y el
`main.py` de este paquete hace lo mismo para arrancarlo solo. Así las rutas se
declaran una sola vez, se arranque como se arranque.
"""

from fastapi import FastAPI

from device_management_service.presentation.api.system_routes import router as system_router


def register(app: FastAPI) -> None:
    app.include_router(system_router)
