from fastapi import FastAPI

from app.core.tenant import TenantMiddleware
from app.modules.authz.router import router as authz_router
from app.modules.health.router import router as health_router

app = FastAPI(title="Edmicro App API", version="0.1.0")
app.add_middleware(TenantMiddleware)
app.include_router(health_router)
app.include_router(authz_router)
