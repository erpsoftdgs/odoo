# -*- coding: utf-8 -*-
{
    'name': "Project Audit",

    'summary': """
        Project audit process""",

    'description': """
        Project audit process
    """,

    'author': "erpSOFTapp",
    'website': "https://www.erpsoftapp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Project',
    'version': '18.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['project', 'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'project_audit/static/src/css/custom.css'
        ]
    },
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'application': True,
}
