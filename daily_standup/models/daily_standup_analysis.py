# -*- coding: utf-8 -*-
from odoo import models, fields


class DailyStandupAnalysis(models.Model):
    _name = "daily.standup.analysis"
    _description = "Daily Standup Analysis"

    sales_analyst_id = fields.Many2one('sales.analyst', string="Daily Standup", readonly=True)
    business_analyst_id = fields.Many2one('business.analyst', string="Daily Standup", readonly=True)
    finance_analyst_id = fields.Many2one('finance.analyst', string="Daily Standup", readonly=True)

    employee_name = fields.Many2one('hr.employee',
                                    string="Employee")
    project_id = fields.Many2one('project.project',
                                 string="Project")
    task_id = fields.Many2one(
        'project.task',
        string="Task",
        domain="[('project_id', '=', project_id)]"
    )
    completion_date = fields.Date()
    priority_task_key_id = fields.Many2one('key.priority.task',
                                           string="Key Priority Task")
    percentage_completion = fields.Float()
