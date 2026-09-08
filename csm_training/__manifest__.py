{
    'name': 'CSM Client Training',
    'version': '18.0.0.0.1',
    'author': 'erpSOFTapp',
    'summary': 'tracks client trainings',
    'category': 'Other',
    'description': """
This module enables ability to tracks client trainings
    """,
    'depends': ["base", "helpdesk", "helpdesk_erp", "csm_requirements", "csm_meeting"],
    'demo': [],
    'data': ['security/ir.model.access.csv',
             'data/training_data.xml',
             'views/csm_views.xml', ],
    'auto_install': False,
    'installable': True,
}
