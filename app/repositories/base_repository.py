from sqlite3 import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models_gdh import *
from typing import Generic, TypeVar, List
from app.database import Base

T = TypeVar('T', bound='Base')  # Для типизации класса

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model


    async def create_if_not_exist(self, **values):
        existing_id = (await self.session.execute(select(self.model.id).filter_by(**values))).scalar()

        if existing_id:
            return existing_id
        
        new_instance = self.model(**values)
        self.session.add(new_instance)
        await self.session.flush()
        return new_instance.id
        

    async def get_read_data(self) -> List[T]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()  
        

    async def get_read_data_by_code(self, filter_value: str) -> list[T]:
        result = await self.session.execute(
            select(self.model)
            .where(self.model.code.contains(filter_value)))
        return result.scalars().all()  


    async def update_data_by_id(self, **values):
        await self.session.execute(update(self.__class__)
                              .where(self.__class__.id == self.id)
                              .values(**values))
        await self.session.commit()


    async def update_data(self, **values):
        for key, value in values.items():
            setattr(self, key, value)
        await self.session.commit()


    async def delete_data_all(self, hard=False):
        if hard:
            result = await self.session.execute(delete(self.model))# Полное удаление из БД
        else:
            result = await self.session.execute(
                update(self.model)
                .where(self.model.is_active == True)
                .values(is_active=False)) # Мягкое удаление (флаг is_active=False)
        await self.session.commit()  

