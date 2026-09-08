# -*- coding: utf-8 -*-

import datetime
from odoo import models, fields, api


class CountEmployeeBadges(models.AbstractModel):
    _inherit = "hr.employee.base"
    badges_count_current_year = fields.One2many('gamification.badge.user',
                                                string='Employee Badges2',
                                                compute="_compute_employee_badges_two")
    number_badges = fields.Integer("Number of Badges",
                                   compute="_compute_employee_badges_two",
                                   store=True)

    @api.depends('user_id.badge_ids.employee_id')
    def _compute_employee_badges_two(self):
        current_year = datetime.datetime.now().year
        # print("current year: ", current_year)

        for employee in self:
            badge_ids = self.env['gamification.badge.user'].search([
                '|', ('employee_id', '=', employee.id),
                '&', ('employee_id', '=', False),
                ('user_id', '=', employee.user_id.id)
            ])
            badge_ids_array = []
            for data in badge_ids:
                # print(data.create_date.year)
                if data.create_date.year == current_year:
                    # print(data.create_date.year)
                    badge_ids_array.append(current_year)
            employee.badges_count_current_year = badge_ids
            employee.number_badges = len(badge_ids_array)
