# TEMPORARY REQUEST LOGGER FOR DEBUGGING

# FastAPI entrypoint; registers routers

"""
Application entry point

Phase 0 responsibilities:
- Create FastAPI app
- Load configuration
- Register routers
- Ensure app boots cleanly
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
import json

from app.routers import (
    health,
    whatsapp,
    transactions,
    summary
)
from app.services.eod_scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Gwiza WhatsApp Pay",
        version="0.1.0",
        lifespan=lifespan,
    )

    # --------------------------
    # Middleware: log all requests
    # --------------------------
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        body = await request.body()

        print("---- INCOMING REQUEST ----")
        print("PATH:", request.url.path)
        print("METHOD:", request.method)
        try:
            print("BODY:", json.loads(body))
        except:
            print("BODY (raw):", body)
        print("HEADERS:", dict(request.headers))

        response = await call_next(request)

        print("STATUS:", response.status_code)
        print("--------------------------")

        return response

    # --------------------------
    # Root health check
    # --------------------------
    @app.get("/")
    async def root():
        return {"message": "GwizaWTPPay is up and running babyyyyyyy"}

    # --------------------------
    # Routers
    # --------------------------
    app.include_router(health.router)
    app.include_router(whatsapp.router)
    app.include_router(transactions.router)
    app.include_router(summary.router)

    return app

# --------------------------
# Create app instance
# --------------------------
app = create_app()