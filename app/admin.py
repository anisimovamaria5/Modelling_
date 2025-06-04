from sqladmin import Admin, ModelView
from app.database import engine
from app.models.models_gdh import EqCompressorUnit, Field, Company, Dks


    
class CompanyAdmin(ModelView, model=Company):
    column_list = [Company.id, Company.name, Company.code]
    column_details_list = column_list + [Company.field]
    column_searchable_list = [Company.name]
    form_columns = column_list
        

class FieldAdmin(ModelView, model=Field):
    column_list = [Field.id, Field.name, Field.company, Field.code]
    column_details_list = column_list + [Field.dks]
    column_searchable_list = [Field.name]
    form_columns = [Field.name, Field.company, Field.name_prefix]

class DksAdmin(ModelView, model=Dks):
    column_list = [Dks.id, Dks.name, Dks.field, Dks.code]
    column_details_list = column_list + [Dks.eq_compressor_unit, Dks.name_prefix]
    column_searchable_list = [Dks.name]
    form_columns = [Dks.name, Dks.field, Dks.name_prefix, Dks.code]

class spchAdmin(ModelView, model=EqCompressorUnit):
    column_list = [EqCompressorUnit.id, EqCompressorUnit.name, EqCompressorUnit.dks]
    column_details_list = column_list 
    column_searchable_list = [EqCompressorUnit.name]
    form_columns = [EqCompressorUnit.name, EqCompressorUnit.dks]
    