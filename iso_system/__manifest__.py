# -*- coding: utf-8 -*-
{
    'name': "ISO",

    'summary': """
       Standardise your processes using ISO System""",

    'description': """
       This module helps you standardise your processes using ISO System  
    """,

    'author': 'erpSOFTapp',
    'website': 'http://www.erpsoftapp.com',

    'category': 'ISO',
    'version': '18.0.0.0.1',

    'depends': ['base', 'hr'],
    'uninstall_hook': 'uninstall_hook',
    'post_init_hook': 'post_init_hook',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/activitytype.xml',
        'views/views.xml',
        'views/resolution.xml',
        'views/reviews.xml',
        'views/audit.xml',
        'views/training.xml',
         'views/menu.xml',


    ],
    'demo': [

    ],


}
