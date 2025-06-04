from sqlite3 import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models_gdh import *
from app.repositories.compressor.unit_repository import CompressorUnitRepository



class CompressorUnitServise(CompressorUnitRepository):
    def __init__(self, session: AsyncSession):
        self.repository = CompressorUnitRepository(session)

    async def get_gdh_by_unit_id(self, id: int):
        result = await self.repository.get_read_data_by_id(id)
        return result
    
