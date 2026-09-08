# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import UserError


class Performance(models.Model):
    _name = 'performance'
    _description = 'Performance'
    _order = "completed_date desc"

    active = fields.Boolean(default=True, tracking=True)

    sales_analyst_id = fields.Many2one('sales.analyst', string="Daily Standup", readonly=True)
    business_analyst_id = fields.Many2one('business.analyst', string="Daily Standup", readonly=True)
    finance_analyst_id = fields.Many2one('finance.analyst', string="Daily Standup", readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    department_id = fields.Many2one('hr.department', string="Department", readonly=True)
    completed_date = fields.Date(string="Completed Date", readonly=True)
    creation_date = fields.Date(string="Creation Date", readonly=True)
    approved_date = fields.Datetime(string="Approved Date", readonly=True)

    priority_score = fields.Float(string="Priority Task Score", readonly=True)
    time_estimation_score = fields.Float(string="Time Estimation Score", readonly=True)
    escalation_score = fields.Float(string="Escalation Score", readonly=True)
    total_score = fields.Float(string="Total Score", readonly=True)

    # Just for display title
    name = fields.Char(compute="_compute_name", store=False)

    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.employee_id.name or 'N/A'} - {rec.completed_date or ''}"

    def write(self, vals):
        if 'active' in vals:
            if not self.env.user.has_group('daily_standup.group_daily_standup_project_manager'):
                raise UserError(_("Only Project Managers can archive KPI records."))
        return super(Performance, self).write(vals)
