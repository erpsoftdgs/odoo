# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SalesCompany(models.Model):
    _inherit = 'res.company'
    skip_workflow = fields.Boolean('Additional Sales Approval Levels',
                                   help="This would install the Sales Approval workflow module for erxtra 2 approval "
                                        "levels.")


class SalesApprovalConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    skip_workflow = fields.Boolean(related='company_id.skip_workflow', string='Additional Sales Approval Levels',
                                   help="This would install the Sales Approval module for erxtra 2 approval levels.",
                                   readonly=False)
