# -*- coding: utf-8 -*-
{
    'name': "Sales Approval workflow",

    'summary': """
       This module enables the ability to have approval levels for sales""",

    'description': """
        This module enables the ability to have additional sales approval levels
    """,

    'author': 'erpSOFTapp',
    'website': 'http://www.erpsoftapp.com',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '18.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'sales_team'],

    # always loaded
    'data': [
        'security/flow_security.xml',
        'security/ir.model.access.csv',
        'data/sub_type.xml',

        'views/views.xml',

    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
