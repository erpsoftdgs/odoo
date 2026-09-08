# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TaskType(models.Model):
    _name = "task.type"
    _description = "Task Type"

    name = fields.Char(required=True)

    # ER 4.0 - 2.0.2: each Task Type needs a matching Activity Type
    # named "Daily Standup - <Task Type>", used when scheduling the
    # activity on Approved (see business_analyst._schedule_task_type_activity)
    activity_type_id = fields.Many2one(
        'mail.activity.type',
        string="Activity Type",
        readonly=True,
        copy=False,
        help="Auto-generated Activity Type ('Daily Standup - <Task Type>') "
             "used when scheduling the follow-up activity for this Task Type."
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._ensure_activity_type()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'name' in vals:
            for rec in self:
                rec._ensure_activity_type(update_name=True)
        return res

    def _ensure_activity_type(self, update_name=False):
        self.ensure_one()
        activity_name = "Daily Standup - %s" % (self.name or '')
        if self.activity_type_id:
            if update_name:
                self.activity_type_id.write({'name': activity_name})
        else:
            activity_type = self.env['mail.activity.type'].create({
                'name': activity_name,
                'category': 'default',
            })
            self.activity_type_id = activity_type.id