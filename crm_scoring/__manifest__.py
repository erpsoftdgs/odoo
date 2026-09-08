# -*- coding: utf-8 -*-
{
    'name': "Sales Lead Scoring",

    'summary': """
       This module adds additional field to the sale module.""",

    'description': """
        This module adds additional field to the sale module.""",

    'author': 'erpSOFTapp',
    'website': 'http://www.erpsoftapp.com',

    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': 'Point of Sale',
    'version': '18.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'crm'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'qweb': [],
    # only loaded in demonstration mode
    'demo': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
