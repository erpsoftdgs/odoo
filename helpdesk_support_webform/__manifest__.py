# -*- coding: utf-8 -*-
{
    'name': "Support Ticket Webform",

    'summary': """ This module gives ability for public users to log a support ticket
    via a webform and the details of the ticket will be mapped to the helpdesk module
    and appear in a designated Helpdesk Team.""",

    'description': """
    """,
    'author': 'erpSOFTapp',
    'website': 'http://www.erpsoftapp.com',
    'license': 'AGPL-3',

    'version': '18.0.0.0.1',


    # any module necessary for this one to work correctly
    'depends': ['base', 'website', 'helpdesk', 'mail', 'prod_access_control', 'helpdesk_erp', 'helpdesk_sale', 'csm_requirements', 'google_recaptcha'],

    # always loaded
    'data': [
        'data/mail_template.xml',
        'security/ir.model.access.csv',
        # 'views/assets.xml',
        'views/res_config_settings_views.xml',
        'views/helpdesk_ticket_views.xml',
        'views/helpdesk_webform.xml'
    ],

    'images': [
        'static/description/icon.png',
        'static/src/img/erpsoftapp.png'
    ],

    'assets': {
        'web.assets_frontend': [
            'helpdesk_support_webform/static/src/js/**/*',
            #'helpdesk_support_webform/static/src/js/add_attachment.js',
        ],
    },

}
