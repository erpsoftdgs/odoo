# -*- coding: utf-8 -*-

{
    'name': 'Custom Odoo Screens',
    'summary': """
        This module gives the ability to create
        custom displays on different Odoo screens
    """,
    'author': 'erpSOFTapp',
    'website': 'https://www.erpsoftapp.com/',
    'category': 'Uncategorized',
    'version': '18.0.0.0.1',
    'depends': ['web_enterprise', 'web', 'base_setup', 'base',],

    'data': [
        'template/assets.xml',
        'template/webclient_templates.xml',
    ],

    "assets": {
        "web._assets_primary_variables": [
            "esa_screen_colors/static/src/scss/colors.scss",
        ],
        "web.assets_backend": [
            'esa_screen_colors/static/src/js/web_home_menu.js',
            "esa_screen_colors/static/src/scss/layout.scss",
        ],
        "web.assets_common": [
            "esa_screen_colors/static/src/scss/tip.scss",
        ],
    },
    'installable': True,
    'application': True,
}
