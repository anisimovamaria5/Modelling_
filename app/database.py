"""Модуль с инициализацией ORM БД"""

from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# DATABASE_URL = settings.get_db_url()
DATABASE_URL = "sqlite+aiosqlite:///test_dks.db"

engine = create_async_engine(url=DATABASE_URL, echo=True)  # движок SQLAlchemy

async_session_maker = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)  # объект генерирующий сессии подключения к БД

class Base(DeclarativeBase):
    pass





