# -*- coding: utf-8 -*-
{
    'name': "Employee Strikes",

    'summary': """
       Ability to create and assign strikes to employees""",

    'description': """
        Long description of module's purpose
    """,

    'author': "erpSOFTapp",
    'website': "http://www.erpsoftapp.com",

    'category': 'Human Resources',
    'version': '18.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_gamification', 'gamification'],


    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/strike_user_wizard_views.xml',
        'views/strike.xml',
        'views/hr_employee_views.xml',
        'views/mail_templates.xml',
    ],
    'installable': True,
    'application': True,
}
