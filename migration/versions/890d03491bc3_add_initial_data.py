"""add_initial_data

Revision ID: 890d03491bc3
Revises: 76a92f19e748
Create Date: 2025-05-23 10:56:42.892583

"""
from typing import Sequence, Union

from alembic import op
import pandas as pd
import sqlalchemy as sa

from app.models.models_gdh import Company, Dks, EqCompressorUnit, Field


# revision identifiers, used by Alembic.
revision: str = '890d03491bc3'
down_revision: Union[str, None] = '76a92f19e748'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    try:
        df = pd.read_csv('media/Base_companies_new.csv')

        companies_data = df[['id', 'companyName', 'code']].drop_duplicates()
        for _, row in companies_data.iterrows():
            company = Company(
                id=row['id'],
                name=row['companyName'],
                code=row['code']
            )
            session.add(company)
        session.flush()

        fields_data = df[['fieldId', 'fieldName', 'fieldCode', 'id']].drop_duplicates()
        for _, row in fields_data.iterrows():
            field = Field(
                id=row['fieldId'],
                name=row['fieldName'],
                name_prefix=row['fieldCode'],
                company_id=row['id']
            )
            session.add(field)
        session.flush()
        
        dks_data = df[['dksId', 'dksName', 'dksCode', 'fieldId']].drop_duplicates()
        for _, row in dks_data.iterrows():
            dks = Dks(
                id=row['dksId'],
                name=row['dksName'],
                name_prefix=row['dksCode'],
                field_id=row['fieldId']
            )
            session.add(dks)
        session.flush()

        # spch_data = df[['spchId', 'spchName', 'dksId']].drop_duplicates()
        # for _, row in spch_data.iterrows():
        #     spch = EqCompressorUnit(
        #         id=row['spchId'],
        #         name=row['spchName'],
        #         dks_id=row['dksId']
        #     )
        #     session.add(spch)

        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def downgrade() -> None:
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    try:
        session.query(EqCompressorUnit).delete()
        session.query(Dks).delete()
        session.query(Field).delete()
        session.query(Company).delete()
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()