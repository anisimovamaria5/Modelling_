from sqlalchemy import Column, String, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base
from app.mixin.mixin import FullCodeMixin

class EqCompressorTypePressureOut(Base):
    __tablename__ = 'EQ_COMPRESSOR_TYPE_PRESSURE_OUT'
    __table_args__ = {'comment':'Таблица номинальных значений выходных давлений'}

    id = Column(Integer, primary_key=True)
    value = Column(Float)

    eq_compressor_type = relationship('EqCompressorType', 
                                      back_populates='eq_compressor_type_pressure_out',
                                      cascade="all, delete-orphan", 
                                      lazy="selectin"
                                      )


class EqCompressorTypeCompRatio(Base):
    __tablename__ = 'EQ_COMPRESSOR_TYPE_COMP_RATIO'
    __table_args__ = {'comment':'Таблица номинальных значений степеней сжатия'}

    id = Column(Integer, primary_key=True)
    value = Column(Float)

    eq_compressor_type = relationship('EqCompressorType', 
                                    back_populates='eq_compressor_type_comp_ratio',
                                    cascade="all, delete-orphan", 
                                    lazy="selectin"
                                    )


class EqCompressorTypeFreqNomimal(Base):
    __tablename__ = 'EQ_COMPRESSOR_TYPE_FREQ_NOMINAL'
    __table_args__ = {'comment':'Таблица номинальных значений частот'}


    id = Column(Integer, primary_key=True)
    value = Column(Float)    

    eq_compressor_type = relationship('EqCompressorType', 
                                      back_populates='eq_compressor_type_freq_nominal',
                                      cascade="all, delete-orphan", 
                                      lazy="selectin"
                                      )


class EqCompressorTypePower(Base):
    __tablename__ = 'EQ_COMPRESSOR_TYPE_POWER'
    __table_args__ = {'comment':'Таблица номинальных значений мощностей'}


    id = Column(Integer, primary_key=True)
    value = Column(Float)      

    eq_compressor_type = relationship('EqCompressorType', 
                                      back_populates='eq_compressor_type_power',
                                      cascade="all, delete-orphan", 
                                      lazy="selectin"
                                      )
    

class EqCompressorType(Base):
    __tablename__ = 'EQ_COMPRESSOR_TYPE'
    __table_args__ = {'comment':'Таблица номиналов СПЧ'}


    id = Column(Integer, primary_key=True)

    press_out_id = Column(Integer, ForeignKey('EQ_COMPRESSOR_TYPE_PRESSURE_OUT.id'))
    comp_ratio_id = Column(Integer, ForeignKey('EQ_COMPRESSOR_TYPE_COMP_RATIO.id'))
    freq_nominal_id = Column(Integer, ForeignKey('EQ_COMPRESSOR_TYPE_FREQ_NOMINAL.id'))
    power_id = Column(Integer, ForeignKey('EQ_COMPRESSOR_TYPE_POWER.id'))

    eq_compressor_type_pressure_out = relationship('EqCompressorTypePressureOut', 
                                      back_populates='eq_compressor_type',
                                      
                                      )    
    eq_compressor_type_comp_ratio = relationship('EqCompressorTypeCompRatio', 
                                      back_populates='eq_compressor_type'
                                      )    
    eq_compressor_type_freq_nominal = relationship('EqCompressorTypeFreqNomimal', 
                                    back_populates='eq_compressor_type'
                                    )    
    eq_compressor_type_power = relationship('EqCompressorTypePower', 
                                    back_populates='eq_compressor_type'
                                    )     
    eq_compressor_unit = relationship('EqCompressorUnit', 
                                back_populates='eq_compressor_type',
                                cascade="all, delete-orphan", 
                                lazy="selectin"
                                )

class UOM(Base):
    __tablename__ = 'UOM'
    __table_args__ = {'comment':'Таблица размерностей'}


    id = Column(Integer, primary_key=True)
    uom_code = Column(String, comment='Код размерности')      

    
class EqCompressorPerfomanceCurve(Base):
    __tablename__ = 'EQ_COMPRESSOR_PERFORMANCE_CURVE'
    __table_args__ = {'comment':'Таблица безразмерных параметров'}


    id = Column(Integer, primary_key=True)
    head = Column(Float, comment='Коэффициент напора')
    non_dim_rate = Column(Float, comment='Коэффициент расхода')
    kpd = Column(Float, comment='Кпд')

    unit_id = Column(Integer, ForeignKey('EQ_COMPRESSOR_UNIT.id'))

    eq_compressor_unit = relationship('EqCompressorUnit',
                         back_populates='eq_compressor_perfomance_curve',
                         uselist=True
                         )
  


class Company(Base):
    __tablename__ = 'COMPANY'
    __table_args__ = {'comment':'Таблица недропользователей'}

    id = Column(Integer, primary_key=True)
    name = Column(String)

    field = relationship('Field',
                         back_populates='company',
                         cascade="all, delete-orphan", 
                         lazy="selectin"
                         )
    code = Column(String)
    def __str__(self):
        return f'{self.name}'


class Field(FullCodeMixin, Base):
    __tablename__ = 'FIELD'
    __table_args__ = {'comment':'Таблица месторождений'}

    id = Column(Integer, primary_key=True)
    name = Column(String, comment='Название месторождения') 

    company_id = Column(Integer, ForeignKey('COMPANY.id'))   

    company = relationship('Company', 
                            back_populates='field'
                            )
    dks = relationship('Dks',
                         back_populates='field',
                         cascade="all, delete-orphan", 
                         lazy="selectin"
                         )

    name_prefix = Column(String, comment='Префикс имени') 

    computed_field_dependencies = ('company_id', 'name_prefix') 
    
    @property
    def parent_id(self): 
        return self.company_id

    parent_class = Company

    def __str__(self):
        return f'{self.name}'
    

class Dks(FullCodeMixin, Base):
    __tablename__ = 'DKS'
    __table_args__ = {'comment':'Таблица ДКС'}

    id = Column(Integer, primary_key=True)
    name = Column(String)

    field_id = Column(Integer, ForeignKey('FIELD.id'))

    field = relationship('Field',
                         back_populates='dks', 
                         lazy="selectin"
                         )
    eq_compressor_unit = relationship('EqCompressorUnit', 
                                back_populates='dks',
                                cascade="all, delete-orphan", 
                                lazy="selectin"
                                )        
    
    name_prefix = Column(String, comment='Префикс имени') 

    computed_field_dependencies = ('field_id', 'name_prefix') 

    @property
    def parent_id(self): 
        return self.field_id

    parent_class = Field

    def __str__(self):
        return f'{self.name}'
    

class EqCompressorUnit(Base):
    __tablename__ = 'EQ_COMPRESSOR_UNIT'
    __table_args__ = {'comment':'Таблица - сущность ГДХ/компрессор'}

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, comment='Уникальное имя ГДХ')
    k_value = Column(Float, comment='Коэф-т политропы, д.ед')
    r_value = Column(Float, comment='Постоянная Больцмана поделеная на молярную массу')
    t_in = Column(Float, comment='Температура, К')
    diam = Column(Float, comment='Диаметр')

    type_id = Column(Integer, ForeignKey('EQ_COMPRESSOR_TYPE.id'), unique=True)
    dks_id = Column(Integer, ForeignKey('DKS.id'))

    eq_compressor_perfomance_curve = relationship('EqCompressorPerfomanceCurve',
                        back_populates='eq_compressor_unit',
                         cascade="all, delete-orphan", 
                         lazy="selectin"
                         )
    dks = relationship('Dks',
                         back_populates='eq_compressor_unit'
                         )
    eq_compressor_type = relationship('EqCompressorType',
                         back_populates='eq_compressor_unit'
                         ) 
    

    def __str__(self):
        return f'{self.name}'   
