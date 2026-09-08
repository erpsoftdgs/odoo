# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, _
from markupsafe import Markup

_logger = logging.getLogger(__name__)

# Color mapping for audit trail clarity
COLOR_MAP = {
    0: "No Color", 1: "Red", 2: "Orange", 3: "Yellow", 4: "Cyan", 
    5: "Purple", 6: "Almond", 7: "Teal", 8: "Blue", 9: "Raspberry", 
    10: "Green", 11: "Violet",
}

HEX_COLOR_MAP = {
    0: "#FFFFFF", 1: "#FF0000", 2: "#FFA500", 3: "#FFFF00", 4: "#00FFFF",
    5: "#800080", 6: "#FFEBCD", 7: "#008080", 8: "#0000FF", 9: "#E30B5D",
    10: "#008000", 11: "#8F00FF",
}


class KeyPriorityTask(models.Model):
    _name = "non.compliance"
    _description = "Non Compliance"

    name = fields.Char(required=True)
    score = fields.Integer()
    color = fields.Integer()


class NonComplianceWizard(models.TransientModel):
    _name = 'non.compliance.wizard'
    _description = 'Non-Compliance Selection Wizard'

    non_compliance_id = fields.Many2one('non.compliance', string="Non-Compliance Entry", required=True)
    res_id = fields.Integer(string="Resource ID")
    res_model = fields.Char(string="Resource Model")

    def action_confirm(self):
        """Log audit trail and create a penalty entry in Performance KPI table"""
        self.ensure_one()
        nc = self.non_compliance_id
        record = self.env[self.res_model].browse(self.res_id)

        # log_msg = _("Non-Compliance Logged: %s (Color Code: %s)") % (nc.name, nc.color)
        # record.message_post(body=log_msg)
        color_name = COLOR_MAP.get(nc.color, _("Unknown"))
        color_hex = HEX_COLOR_MAP.get(nc.color, "#000000")

        # Constructed HTML log message for the audit trail (chatter)
        log_msg = Markup(
            "<b>%s</b> %s <br/>"
            "<b>%s</b> <span style='display:inline-block; width:12px; height:12px; background-color: %s; border:1px solid #ccc; margin-left:5px; vertical-align:middle;'></span>"
        ) % (
            _("Non-Compliance:"), nc.name,
            _("Color:"), color_hex
        )

        record.message_post(body=log_msg)

        # All integer fields are 0 except Total Score which takes the score from NC entry
        vals = {
            'employee_id': record.employee_name.id,
            'department_id': record.department_id.id,
            'completed_date': fields.Date.today(),
            'creation_date': record.creation_date,
            'total_score': nc.score,
            'priority_score': 0,
            'time_estimation_score': 0,
            'escalation_score': 0,
        }

        if self.res_model == 'business.analyst':
            vals['business_analyst_id'] = record.id
        elif self.res_model == 'sales.analyst':
            vals['sales_analyst_id'] = record.id
        elif self.res_model == 'finance.analyst':
            vals['finance_analyst_id'] = record.id

        self.env['performance'].create(vals)
        return {'type': 'ir.actions.act_window_close'}
