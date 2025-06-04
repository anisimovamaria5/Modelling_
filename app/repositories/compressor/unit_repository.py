from sqlite3 import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models_gdh import *
from sqlalchemy.orm import joinedload, selectinload, contains_eager

from app.repositories.base_repository import BaseRepository

class CompressorUnitRepository(BaseRepository[EqCompressorUnit]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, EqCompressorUnit)


    async def get_read_data_by_id(self, id):
        result = await self.session.execute(
            select(EqCompressorUnit)
            .options(selectinload(EqCompressorUnit.eq_compressor_perfomance_curve),
                     selectinload(EqCompressorUnit.eq_compressor_type)
                     .selectinload(EqCompressorType.eq_compressor_type_freq_nominal)
                     )
            .where(EqCompressorUnit.id == id)
        )
        return result.scalars().all()


    async def create_compressor_unit(self,
                                    sheet_name: str,
                                    dks_code: str,
                                    pressure_out: float,
                                    comp_ratio: float,
                                    freq_nominal: float,
                                    power: float,
                                    k_value: float,
                                    r_value: float,
                                    t_in: float,
                                    diam: float,
                                    perfomance_curves: list[dict]
                                    ):
        dks_id = await self.session.scalar(
                                    select(Dks.id)
                                    .where(Dks.code == dks_code)
                                    )    
          
        type_params = [
                    (EqCompressorTypePressureOut, pressure_out, 'press_out_id'),
                    (EqCompressorTypeCompRatio, comp_ratio, 'comp_ratio_id'),
                    (EqCompressorTypeFreqNomimal, freq_nominal, 'freq_nominal_id'),
                    (EqCompressorTypePower, power, 'power_id')
                    ]
        dct_result_id = {}     
        for model, param, id_param in type_params:
            repo_param = BaseRepository(self.session, model)
            type_param = await repo_param.create_if_not_exist(value=param)
            dct_result_id[id_param] = type_param

        repo_compressor = BaseRepository(self.session, EqCompressorType)
        compressor_type = await repo_compressor.create_if_not_exist(**dct_result_id)

        unit = EqCompressorUnit(
                            name=sheet_name,
                            dks_id=dks_id,
                            type_id=compressor_type,
                            k_value=k_value, 
                            r_value=r_value,
                            t_in=t_in,
                            diam=diam
                            )
        self.session.add(unit)
        await self.session.flush()


        for curve in perfomance_curves:
            perf_curve = EqCompressorPerfomanceCurve(
                            unit_id=unit.id,
                            head=curve['k_nap'],
                            non_dim_rate=curve['k_rash'],
                            kpd=curve['kpd'],
                            )
            self.session.add(perf_curve)
        
        await self.session.commit()
        return unit
            