from fastapi import FastAPI

from app.modules.health.router import router as health_router

app = FastAPI(title="Edmicro App API", version="0.1.0")
app.include_router(health_router)
