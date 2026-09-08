# -*- coding: utf-8 -*-



# class base(models.Model):
#     _name = 'base.base'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100

from odoo import models, api, fields, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError





