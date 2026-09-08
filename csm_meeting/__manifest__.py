# -*- coding: utf-8 -*-
{
    'name': "CSM",
    'summary': "Summary",
    'description': "Description",
    'author': 'erpSOFTapp',
    'website': 'http://www.erpsoftapp.com',
    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': 'Helpdesk',
    'version': '18.0.1.0.1',
    # any module necessary for this one to work correctly
    'depends': ['contacts', 'helpdesk', 'prod_access_control'],
    # always loaded,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],

}
