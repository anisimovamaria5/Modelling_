"""Модуль с эндпойтами-обработчиками запросов от клиентов"""
import logging
from typing import Literal, List
from fastapi import APIRouter, Depends, UploadFile, File
from DKS_math.shared import BaseGDH, get_df_by_excel, use_pydantic_model
from app.repositories.base_repository import BaseRepository
from app.repositories.compressor.unit_repository import CompressorUnitRepository
from app.services.compressor_unit_service import CompressorUnitServise
from app.services.menu_service import _build_tree
from app.dependencies import get_db_session, get_model_repo, get_unit_repo
from app.middlewares import handle_errors
from app.models.models_gdh import Company, Dks, EqCompressorPerfomanceCurve, EqCompressorType, EqCompressorTypeCompRatio, EqCompressorTypeFreqNomimal, EqCompressorTypePower, EqCompressorTypePressureOut, EqCompressorUnit, Field
from app.schemas.schemas import BuildGdh, CurveResponse, FilterItem, SubMenu
from io import BytesIO


router = APIRouter(prefix='/api/v1')
datafile_logger = logging.getLogger('datafile')


@router.post("/upload/{filetype}/preview",
            response_model = List[CurveResponse] | None,
            operation_id = "upload",
            name = "upload"
            )
@handle_errors
async def upload_excel_file(
    filetype: Literal['normal','flowrate'],
    deg: int = 4,
    k_value: float = 1.31,
    press_conditonal: float = 0.101325,
    temp_conditonal: float = 283,
    file: UploadFile = File(...),
    ):
    """
    Эндпойнт формирования базы ГДХ\n
    \tРасчитываются безразмерные парметры (коэффициент расхода, коэффициент напора и кпд) для построения безразмерных ГДХ.
    
    """
    file_content = await file.read()
    excel_data = BytesIO(file_content)
    dct_df = get_df_by_excel(
        excel_data,
        deg=deg,
        k_value=k_value,
        press_conditonal=press_conditonal,
        temp_conditonal=temp_conditonal
        )
    curves = use_pydantic_model(dct_df)
    return curves


@router.post("/save/{filetype}/commit",
            operation_id = "save",
            name = "save"
            )
@handle_errors
async def save_excel_file(
    filetype: Literal['normal','flowrate'],
    sheet_name:str,
    dks_code:str,
    deg: int = 4,
    k_value: float = 1.31,
    press_conditonal: float = 0.101325,
    temp_conditonal: float = 283,
    file: UploadFile = File(...),
    # repo: CompressorUnitRepository = Depends(get_unit_repo)
    session_db = Depends(get_db_session)
    ):
    """
    Эндпойнт сохранения ГДХ в БД\n

    """
    file_content = await file.read()
    excel_data = BytesIO(file_content)
    dct_df = get_df_by_excel(
        excel_data,
        deg=deg,
        k_value=k_value,
        press_conditonal=press_conditonal,
        temp_conditonal=temp_conditonal
        )
    df = dct_df[sheet_name]
    perfomance_curves = [
                        {
                        'k_nap' : df['k_nap'][i],
                        'k_rash' : df['k_rash'][i],
                        'kpd' : df['kpd'][i],
                        }
                        for i in range(len(df['k_nap']))
                        ]
    repo = CompressorUnitRepository(session_db)
    return await repo.create_compressor_unit(
            sheet_name=sheet_name,
            dks_code=dks_code,
            pressure_out=df['p_title'][0],
            comp_ratio=df['stepen'][0],
            freq_nominal=df['fnom'][0],
            power=df['mgth'][0],
            k_value=df['k'][0],
            r_value=df['R'][0],
            t_in=df['temp'][0],
            diam=df['diam'][0],
            perfomance_curves=perfomance_curves
            )


@router.delete("/delete/",
            operation_id="delete",
            name="delete"
            )
@handle_errors
async def delete_data(
    repo: BaseRepository = Depends(get_model_repo(EqCompressorPerfomanceCurve))
    ):
    """
    Эндпойнт удаления\n

    """
    return await repo.delete_data_all(hard=True)


@router.get("/company/",
            response_model = List[FilterItem],
            operation_id="company",
            name="company"
            )
@handle_errors
async def get_all_companies(
    repo: BaseRepository = Depends(get_model_repo(Company))
    ):
    """
    Эндпойнт получения списка всех компаний из базы данных\n

    """
    return await repo.get_read_data()


@router.get("/company/{company_code}/field/",
            response_model = List[FilterItem],
            operation_id="field",
            name="field"
            )
@handle_errors
async def get_all_field(
    company_code: str,
    repo: BaseRepository = Depends(get_model_repo(Field))
    ):
    """
    Эндпойнт получения списка месторождений по id недропользователя из базы данных\n

    """
    return await repo.get_read_data_by_code(company_code)
    

@router.get("/company/field/{field_code}/dks/",
            response_model = List[FilterItem],
            operation_id="dks",
            name="dks"
            )
@handle_errors
async def get_all_dks(
    field_code: str,
    repo: BaseRepository = Depends(get_model_repo(Dks))
    ):
    """
    Эндпойнт получения списка ДКС по id месторождения из базы данных\n

    """
    return await repo.get_read_data_by_code(field_code)


@router.get("/company_tree/",
            response_model = List[SubMenu],
            operation_id="company_tree",
            name="company_tree"
            )
@handle_errors
async def get_bread_crumbs(
    repo: BaseRepository = Depends(get_model_repo(Company))
    ):
    """
    Эндпойнт получения вложенного меню\n

    """
    return await _build_tree(repo)


@router.post("/build_gdh/",
            response_model = List[BuildGdh],
            operation_id="build_gdh",
            name="build_gdh"
            )
@handle_errors
async def get_gdh_by_id(
    id: int,
    session_db = Depends(get_db_session)
    ):
    """
    Эндпойнт построения ГДХ\n

    """
    repo = CompressorUnitServise(session_db)
    unit_comp_data = await repo.get_gdh_by_unit_id(id)
    param = BaseGDH.read_dict(unit_comp_data[0]) 
    res = param.get_summry()
    return res[0] + res[1] 