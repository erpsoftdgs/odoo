# -*- coding: utf-8 -*-
{
    'name': "Helpdesk Ticket Type",
    'summary': "This module creates a new config page, Ticket Type and adds Ticket Type to Helpdesk Tickets",
    'author': "erpSOFTapp",  # author
    'category': 'Adminstration',
    'license': 'LGPL-3',
    'website': 'http://www.erpsoftapp.com',
    'version': '18.0.0.0.1',
    'depends': ['helpdesk'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
