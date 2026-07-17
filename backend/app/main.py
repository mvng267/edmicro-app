from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.tenant import TenantMiddleware
from app.modules.authz.router import router as authz_router
from app.modules.health.router import router as health_router
from app.modules.org.router import router as org_router

app = FastAPI(title="Edmicro App API", version="0.1.0")

# Dev: cho phép mọi subdomain *.localhost gọi API. Prod siết theo domain tenant (M1+).
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://([a-z0-9-]+\.)?localhost(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantMiddleware)
app.include_router(health_router)
app.include_router(authz_router)
app.include_router(org_router)
