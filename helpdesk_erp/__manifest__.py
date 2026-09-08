# -*- coding: utf-8 -*-
{
    'name': "Helpdesk Customisation",

    'summary': """
        Extend helpdesk module to support software projects""",

    'description': """
        Extend Helpdesk module to provide support for in house software projects management and tracking
    """,

    'author': "erpSOFTapp",
    'website': "http://www.erpsoftapp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tickets',
    "version": "18.0.0.0.1",

    # any module necessary for this one to work correctly
    'depends': ['base','helpdesk','helpdesk_timesheet'],

    # always loaded
    'data': [
'security/security.xml',
         'security/ir.model.access.csv',
        'views/views.xml',
        'views/ticket_views.xml',
        'views/team_views.xml',
        'views/pm_requests_view.xml',
        'views/helpdesk_sprint.xml',
        'data/helpdesk_data.xml',
        'views/client.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}