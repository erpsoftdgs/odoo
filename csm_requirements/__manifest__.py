{
    'name': 'CSM New Requirements',
    'version': '18.0.0.0.1',
    'author': 'erpSOFTapp',
    'category': 'Other',
    'description': """
This module enables ability to track all new business requirements from clients
    """,
    'depends': ["base", "mail", "hr", "csm_meeting"],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
        'views/csm_views.xml',
        'views/onboarding.xml'
    ],
    'auto_install': False,
    'installable': True,
}
