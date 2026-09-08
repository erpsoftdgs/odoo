# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    strike_goal_ids = fields.One2many('gamification.goal', 'user_id')
    strike_ids = fields.One2many('employee.strike.user', 'user_id')
