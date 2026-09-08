# -*- coding: utf-8 -*-
from odoo import models, fields


class TimeEscalationKey(models.Model):
    _name = "time.escalation.key"
    _description = "Time Escalation Key"

    name = fields.Char(required=True)
    score = fields.Integer()
    color = fields.Integer()
