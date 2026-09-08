# -*- coding: utf-8 -*-
{
    'name': "Client Sales Web Form",

    'summary': """
       This module creates a web form for CRM module.""",

    'description': """
        This module creates a web form for CRM module.""",

    'author': 'erpSOFTapp',
    'website': 'http://www.erpsoftapp.com',

    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': 'CRM',
    'version': '18.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'website', 'crm', 'crm_scoring'],

    # always loaded
    'data': [
        'data/data.xml',  # Load predefined data first
        'views/views.xml',  # Load views before reports
        'report/report.xml',  # Load reports after views
        'controllers/pages/registration_form.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'client_sales_webform/static/src/js/email.js',
        ],
    },

    'qweb': [],
    # only loaded in demonstration mode
    'demo': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
