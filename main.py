"""
Here the FastAPI application initialization.

Attributes:
    app (FastAPI): The main FastAPI application instance used to define routes,
        middlewares, and other application configurations.
"""

from apps.egypt_national_id.routes import router as egypt_national_id_router
from apps.clients.routes import router as clients_router
from core.app import app

app.include_router(egypt_national_id_router)
app.include_router(clients_router)
