from sqlalchemy import select
from app.models.models_gdh import Dks, EqCompressorPerfomanceCurve, EqCompressorType, EqCompressorTypeCompRatio, EqCompressorTypeFreqNomimal, EqCompressorTypePower, EqCompressorTypePressureOut, EqCompressorUnit
from app.repositories.compressor.unit_repository import CompressotUnitRepository


async def add_data_compressor_unit(session, df, dks_code, sheet_name):
    repo = CompressotUnitRepository(session)

    dks_id = await session.scalar(select(Dks.id)
                                            .where(Dks.code == dks_code))     
    new_instance =  await repo.create_data(name=sheet_name,
                                            dks_id=dks_id
                                            )
    
    dct_result_id = {}     

    models_param = [
                    (EqCompressorTypePressureOut, 'p_title', 'press_out_id'),
                    (EqCompressorTypeCompRatio, 'stepen', 'comp_ratio_id'),
                    (EqCompressorTypeFreqNomimal, 'fnom', 'freq_nominal_id'),
                    (EqCompressorTypePower, 'mgth', 'power_id')
                    ]
    for model, param, id_param in models_param:
        new_data = await model.create_data(session, value=df[param][0])
        dct_result_id[id_param] = new_data
    if dct_result_id:
        compressor_type = await EqCompressorType.create_data(session,**dct_result_id)
        
        compressor_param = await (await session.get(EqCompressorUnit, new_instance)).update_data_by_id(session, 
                                                                                                    type_id=compressor_type,
                                                                                                    k_value=df['k'][0],
                                                                                                    r_value=df['R'][0],
                                                                                                    t_in=df['temp'][0]
                                                                                                    )                                                                                                                                                                                                                       
        for i in range(len(df['k_nap'])):
            new_data = await EqCompressorPerfomanceCurve.create_data(session, 
                                                                    head=df['k_nap'][i],
                                                                    non_dim_rate=df['k_rash'][i],
                                                                    kpd=df['kpd'][i],
                                                                    unit_id=new_instance
                                                                    )            
        await session.commit()
        return new_data
    return None
