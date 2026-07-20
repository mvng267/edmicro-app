from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.tenant import TenantMiddleware
from app.modules.assignment.router import router as assignment_router
from app.modules.authz.router import router as authz_router
from app.modules.content.router import router as content_router
from app.modules.health.router import router as health_router
from app.modules.org.import_router import router as org_import_router
from app.modules.org.router import router as org_router
from app.modules.org.users_router import router as org_users_router
from app.modules.practice.router import router as practice_router
from app.modules.report.router import router as report_router

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
app.include_router(org_users_router)
app.include_router(org_import_router)
app.include_router(content_router)
app.include_router(practice_router)
app.include_router(assignment_router)
app.include_router(report_router)
