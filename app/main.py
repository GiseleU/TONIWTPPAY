# FastAPI entrypoint; registers routers

"""
Application entry point

Phase 0 responsibilities:
- Create FastAPI app
- Load configuration
- Register routers
- Ensure app boots cleanly
"""

from fastapi import FastAPI

from app.api.routes import (
    health,
    webhooks,
    orders,
    seller_commands,
)

def create_app() -> FastAPI:
    app = FastAPI(
        title="Gwiza WhatsApp Pay",
        version="0.1.0",
    )

    # ---- Routers ----
    app.include_router(health.router)
    app.include_router(webhooks.router)
    app.include_router(orders.router)
    app.include_router(seller_commands.router)

    return app


app = create_app()