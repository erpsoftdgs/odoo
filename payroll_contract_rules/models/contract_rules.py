# -*- coding: utf-8 -*-
from odoo import models, fields
# import odoo.addons.decimal_precision as dp


class CustomerStatement(models.Model):
    _inherit = 'hr.contract'
    a_1 = fields.Float("Allowance 1")
    a_2 = fields.Float("Allowance 2")
    a_3 = fields.Float("Allowance 3")
    a_4 = fields.Float("Allowance 4")
    a_5 = fields.Float("Allowance 5")
    a_6 = fields.Float("Allowance 6")
    a_7 = fields.Float("Allowance 7")
    a_8 = fields.Float("Allowance 8")
    d_1 = fields.Float("Deduction 1")
    d_2 = fields.Float("Deduction 2")
    d_3 = fields.Float("Deduction 3")
    d_4 = fields.Float("Deduction 4")
    d_5 = fields.Float("Deduction 5")
    d_6 = fields.Float("Deduction 6")
    d_7 = fields.Float("Deduction 7")
    d_8 = fields.Float("Deduction 8")
