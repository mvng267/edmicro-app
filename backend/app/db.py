from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def set_tenant(session: AsyncSession, tenant_id: str | None) -> None:
    """Đặt app.tenant_id cho transaction hiện tại — RLS dùng để lọc.

    Dùng set_config(..., true) (LOCAL) để chỉ áp trong transaction.
    tenant_id=None (vai trò platform) -> đặt chuỗi rỗng, RLS coi như không khớp tenant nào.
    """
    await session.execute(
        text("SELECT set_config('app.tenant_id', :tid, true)"),
        {"tid": tenant_id or ""},
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        async with session.begin():
            yield session
