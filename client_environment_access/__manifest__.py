# -*- coding: utf-8 -*-
{
    "name": "Client Environment Access",
    "summary": """
       Control access to client environment systems""",
    "description": """
       This module gives ability to  control access
        to client environments data
    """,
    "author": "erpSOFTapp",
    "website": "http://www.erpsoftapp.com",
    "category": "Helpdesk",
    "version": "18.0.0.0.1",
    "depends": ["base", "helpdesk_erp", "prod_access_control"],
    "data": [
        "views/views.xml",
        "views/menu.xml",
        "security/ir.model.access.csv"
    ],
    "demo": [],
}
