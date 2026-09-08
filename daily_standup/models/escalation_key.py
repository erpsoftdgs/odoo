# -*- coding: utf-8 -*-
from odoo import models, fields


class EscalationKey(models.Model):
    _name = "escalation.key"
    _description = "Escalation Key"

    name = fields.Char(required=True)
    score = fields.Integer()
    color = fields.Integer()
