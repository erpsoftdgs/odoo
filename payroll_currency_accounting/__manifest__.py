# coding: utf-8
{
    'name': 'Payroll Exchange Rate',
    'version': '18.0.0.0.1',
    'author': 'erpSOFTapp',
    'category': 'Payroll',
    'website': 'http://www.erpsoftapp.com',
    'description': """
This module enables salary rules to post translated currency journal entries
based on the current exchange rate.
    """,
    'depends': [
        "base",
        "hr",
        "hr_payroll",
        "account",
        "hr_contract",
        "hr_payroll_account",
    ],
    'license': 'LGPL-3',
    'data': [
        "pay_curr_exchange.xml",
        "pay_sal_rules.xml",
    ],
    'installable': True,
    'auto_install': False,
}
