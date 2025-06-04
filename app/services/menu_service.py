from app.schemas.schemas import SubMenu

      
async def _build_tree(repo):
    companies = await repo.get_read_data()
    menu = []
    for company in companies: 
        company_node = SubMenu(
            id=company.id,
            name=company.name,
            code=company.code,
            children=[]
            )
        for field in company.field: 
            field_node = SubMenu(
                id=field.id,
                name=field.name,
                code=field.code,
                children=[]
            )
            for dks in field.dks: 
                dks_node = SubMenu(
                    name=dks.name,
                    code=dks.code,
                    children=None
                    )
                field_node.children.append(dks_node)
            company_node.children.append(field_node)
        menu.append(company_node)
    return menu