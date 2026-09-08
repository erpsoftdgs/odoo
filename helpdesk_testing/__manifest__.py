{
    'name': 'Test Repository',
    'version': '18.0.0.0.1',
    'author': 'erpSOFTapp',
    'category': 'Helpdesk',
    'description': """
This module enables ability to house a central location for all test scripts
    """,
    'depends': ["base", "base_setup", "helpdesk_erp"],
    'demo': [],
    'data': ['data/data.xml', 'views/views.xml', 'security/ir.model.access.csv'],
    'auto_install': False,
    'installable': True,
}
