from starlette.types import ASGIApp, Receive, Scope, Send


class TenantMiddleware:
    """Đọc X-Tenant-Slug (frontend đặt từ subdomain) và gắn vào request state."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = dict(scope["headers"])
            slug = headers.get(b"x-tenant-slug", b"").decode() or None
            scope.setdefault("state", {})["tenant_slug"] = slug
        await self.app(scope, receive, send)
