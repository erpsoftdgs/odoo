# -*- coding: utf-8 -*-
{
    'name': 'HR Payroll Staff Deductions',
    'summary': 'HR Employee Deduction functionality,',
    'description': """
    This Module Provides Staff Deductions functionality,
    Loan BI View to analyse Loan Analysis data
    """,
    'author': 'erpSOFTapp',
    'license': 'AGPL-3',
    'category': 'Contract',
    'version': '18.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_contract', 'hr_payroll'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'installable': True,
    'application': True,
}
