from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from app.database import async_session_maker
from app.repositories.base_repository import BaseRepository
from app.repositories.compressor.unit_repository import CompressorUnitRepository

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

def get_model_repo(model):
    async def _get_repo(session: AsyncSession = Depends(get_db_session)):
        return BaseRepository(session, model)
    return _get_repo

def get_unit_repo():
    async def _get_repo(session: AsyncSession = Depends(get_db_session)):
        return CompressorUnitRepository(session)
    return _get_repo