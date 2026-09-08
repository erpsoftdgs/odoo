# -*- coding: utf-8 -*-
from odoo import models, fields


class KeyPriorityTask(models.Model):
    _name = "key.priority.task"
    _description = "Key Priority Task"

    name = fields.Char(required=True)
    score = fields.Integer()
    color = fields.Integer()
