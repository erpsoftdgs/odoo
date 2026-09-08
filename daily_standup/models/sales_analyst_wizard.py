# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo import models, fields, _


class SalesAnalystWizard(models.TransientModel):
    _name = 'sales.analyst.wizard'
    _description = 'Sales Analyst Wizard'

    date = fields.Date(required=True)

    def action_confirm_sales_analyst(self):
        """
        Perform duplication of selected Sales Analyst records.
        """
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return {'type': 'ir.actions.act_window_close'}

        records = self.env['sales.analyst'].browse(active_ids)

        creation_dates = records.mapped('creation_date')
        if len(set(creation_dates)) > 1:
            raise ValidationError(_("Please select records with the same creation date."))

        for record in records:
            if record.state != 'approved':
                raise ValidationError(_("Only approved records can be duplicated."))

            record.copy({'creation_date': self.date,})

        return {'type': 'ir.actions.act_window_close'}
