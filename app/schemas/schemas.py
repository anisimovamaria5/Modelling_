from pydantic import BaseModel
from typing import List, Literal, Optional

class DataPoint(BaseModel):
    """
    Координаты для построения графика 
    """
    x: float
    y: float

class Dataset(BaseModel):
    """
    Схема датасета со значениями безразмерных параметров для кпд и коэффициента напора для графиков (линии и точки)
    """
    label: Literal['polytropic efficiency', 'head coefficient']
    title: str 
    kind:  Literal['points', 'line']
    data: List[DataPoint]

class CurveResponse(BaseModel):
    """
    Схема датасета с названиями СПЧ
    """
    datasets: List[Dataset]
    label: str


class FilterItem(BaseModel):
    """
    Схема для формирования json для моделей: недропользователь, месторождение и ДКС
    """
    id: int
    name: str
    code: str

class SubMenu(BaseModel):
    """
    Схема для формирования json вложенного меню
    """
    name: str
    code: str
    children: Optional[List["SubMenu"]] | None


class BuildGdh(BaseModel):
    """
    Схема датасета с координатами для построения ГДХ
    """
    datasets: List[DataPoint]
    label: str
