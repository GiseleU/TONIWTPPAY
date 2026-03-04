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
    payments,
    reports,
)

def create_app() -> FastAPI:
    app = FastAPI(
        title="Gwiza WhatsApp Pay",
        version="0.1.0",
    )


    @app.get("/")
    async def root():
        return {"message": "GwizaWTPPay is up and running babyyyyyyy"}
    
    
    # ---- Routers ----
    app.include_router(health.router)
    app.include_router(webhooks.router)
    app.include_router(orders.router)
    app.include_router(seller_commands.router)
    app.include_router(payments.router)
    app.include_router(reports.router)

    return app


app = create_app()
