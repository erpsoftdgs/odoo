# -*- coding: utf-8 -*-
{
    "name": "Production Access Control",
    "summary": """
       Control access to client production systems""",
    "description": """
       This module gives ability to  control access
        to client production systems using approval workflows
    """,
    "author": "erpSOFTapp",
    "website": "http://www.erpsoftapp.com",
    "category": "Helpdesk",
    "version": "18.0.0.0.1",
    "depends": ["base", "helpdesk_erp"],
    "data": [
        "data/sequence.xml",
        'data/activitytype.xml',
        'data/subtype.xml',
        "security/security.xml",
        "views/views.xml",
        "views/menu.xml",
        "security/ir.model.access.csv"
    ],
    'external_dependencies': {
        'python': ['paramiko']
    },
    "demo": [],
}
