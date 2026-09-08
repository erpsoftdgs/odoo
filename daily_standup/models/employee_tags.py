# -*- coding: utf-8 -*-
from odoo import models, fields


class EmployeeTags(models.Model):
    _name = "employee.tags"
    _description = "Employee Tags"

    name = fields.Char(required=True)
    color = fields.Integer()
