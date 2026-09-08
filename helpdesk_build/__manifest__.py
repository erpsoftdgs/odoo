# -*- coding: utf-8 -*-
{
    "name": "System Build",
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
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/views.xml",
        "views/menu.xml",
        "wizard/next_environment_views.xml",
    ],
    "demo": [],
}
