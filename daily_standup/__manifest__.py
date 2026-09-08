# -*- coding: utf-8 -*-
{
    "name": "Daily Standup",
    "version": "1.0",
    "summary": "Manage daily standup reports and track priority tasks.",
    "website": "http://www.erpsoftapp.com",
    "author": "erpSOFTapp",
    "description": """
Enables employees to create and track daily standup reports, prioritize tasks,
and improve team collaboration.
    """,
    "category": "Productivity",
    "depends": ["base", "mail", "hr", "project", "hr_gantt"],
    "data": [
        "security/security_groups.xml",
        "security/ir.model.access.csv",
        "views/sales_analyst_views.xml",
        "views/business_analyst_views.xml",
        "views/finance_analyst_views.xml",
        "views/non_compliance_views.xml",
        "views/performance_views.xml",
        "views/daily_standup_analysis_views.xml",
        "views/escalation_key_views.xml",
        "views/task_type.xml",
        "views/key_priority_task_views.xml",
        "views/time_escalation_key_views.xml",
        "views/employee_tags_views.xml",
        "views/business_analyst_wizard_views.xml",
        "views/confirm_duplicate_views.xml",
        "views/menuitem_views.xml",
        "views/sales_analyst_wizard_views.xml",
    ],
    # 'post_load': 'post_load',
    "demo": [],
    "auto_install": False,
    "installable": True,
    "application": True,
    "license": "LGPL-3"
}
