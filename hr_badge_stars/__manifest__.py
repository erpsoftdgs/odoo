# -*- coding: utf-8 -*-
{
    'name': "Employee Kanban Stars",

    'summary': """
        Employee Kanban Stars""",

    'description': """
        Display Count of badges given to employee in a financial year in the kanban view
    """,

    'author': "erpSOFTapp",
    'website': "https://www.erpsoftapp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '18.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr', 'hr_gamification'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml',
    ],
    'installable': True,
    'application': True,
}
