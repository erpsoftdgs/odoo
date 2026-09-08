from odoo import models, fields

class ISOApprovers(models.Model):

    _name = 'iso.approver'
    _description = 'ISO Approver'
    _sql_constraints = [
        ('name_department', 'unique (department)', "Department already exists !"),
    ]
    department = fields.Many2one('hr.department', required=True)
    team_lead = fields.Many2one('res.users', required=True)
    project_manager = fields.Many2one('res.users', required=True)
    quality_manager = fields.Many2one('res.users', required=True)
    compliance_manager = fields.Many2one('res.users', required=True)
    auditor = fields.Many2one('res.users', required=True)
    executive_board = fields.Many2one('res.users', required=True)
