# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    strike_ids = fields.One2many(
        'employee.strike.user', string='Employee Strikes',
        compute='_compute_employee_strikes',
        help="All employee Strikes, linked to the employee either directly or \
        through the user"
    )
    has_strikes = fields.Boolean(compute='_compute_has_strikes')
    # necessary for correct dependencies of strike_ids and has_strikes
    direct_strike_ids = fields.One2many(
        'employee.strike.user', 'employee_id',
        help="Badges directly linked to the employee")

    @api.depends('direct_strike_ids', 'user_id.strike_ids.employee_id')
    def _compute_employee_strikes(self):
        for employee in self:
            strike_ids = self.env['employee.strike.user'].search([
                '|', ('employee_id', '=', employee.id),
                '&', ('employee_id', '=', False),
                ('user_id', '=', employee.user_id.id)
            ])
            employee.strike_ids = strike_ids

    @api.depends('strike_ids')
    def _compute_has_strikes(self):
        for employee in self:
            employee.has_strikes = bool(employee.strike_ids)
