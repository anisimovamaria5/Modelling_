from app.models.models_gdh import *
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import object_session
from sqlalchemy import event
from sqlalchemy import Column, String

class FullCodeMixin:

    computed_field_dependencies = ()

    parent_class = None
    name_prefix = None

    @property
    def parent_id(self): 
        raise NotImplementedError

    def _calculate_code(self) -> str:
        raise NotImplementedError

    @declared_attr
    def code(cls):
        return Column(String, nullable=True)

    @classmethod
    def __declare_last__(cls):
        """Регистрируем обработчики событий"""
        @event.listens_for(cls, 'before_insert')
        def before_insert(mapper, connection, target):
            """Вычисляем код перед вставкой"""
            target._calculate_code()
        
        @event.listens_for(cls, 'before_update')
        def before_update(mapper, connection, target):
            # Проверяем, изменились ли зависимые поля
            if any(
                getattr(target.history, attr, None).has_changes() 
                    for attr in target.computed_field_dependencies 
                if hasattr(target, attr)
                ):
                target._calculate_code()

    def _calculate_code(self):        
        curr_session = object_session(self)        
        self.parent = curr_session.get(self.parent_class, self.parent_id)
        parent_code = getattr(self.parent, 'code', '')
        self.code = f"{parent_code}_{self.name_prefix}".strip('_')
        return self.code