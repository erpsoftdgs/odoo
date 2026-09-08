# -*- coding: utf-8 -*-
{
    'name': 'Payroll Contract Rules',
    'version': '18.0.0.0.1',
    'author': 'erpSOFTapp',
    'license': 'AGPL-3',
    'category': 'HR',
    'website': 'https://www.erpsoftapp.com',
    'description': """his module enables the ability to create additional payroll salary
    rules for allowances and deduction specific to each employee""",
    'depends': ["hr", "hr_contract"],
    'demo': [],
    'data': ['views/contract_rules.xml', ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
