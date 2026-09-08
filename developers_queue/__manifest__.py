# -*- coding: utf-8 -*-
{
    "name": "Developer Queue",
    "summary": """
       Allow Developers access to see job queues""",
    "description": """
       This module gives ability for developers to access their job queues
    """,
    "author": "erpSOFTapp",
    "website": "http://www.erpsoftapp.com",
    "category": "Helpdesk",
    "version": "18.0.0.0.1",
    "depends": ["website", "portal", "helpdesk", "helpdesk_erp", "hr"],
    "data": [
        "views/views.xml",
        "views/menu.xml",
        "views/templates.xml",
        "security/ir.model.access.csv"
    ],
    "demo": [],
    'assets': {
        'web.assets_frontend': [
            'developers_queue/static/src/scss/**/*',
        ],
    },
}
