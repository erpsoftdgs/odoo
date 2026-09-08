# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo import models, fields, _


class BusinessAnalystWizard(models.TransientModel):
    _name = 'business.analyst.wizard'
    _description = 'Business Analyst Wizard'

    date = fields.Date(required=True)

    def action_confirm_business_analyst(self):
        """
        Perform duplication of selected Business
        Analyst records upon confirmation.
        """
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return {'type': 'ir.actions.act_window_close'}
            # Return a consistent action

        records = self.env['business.analyst'].browse(active_ids)

        # Check if all records have the same creation_date
        creation_dates = records.mapped('creation_date')
        if len(set(creation_dates)) > 1:
            raise ValidationError(_("Please select records with "
                                    "the same creation date."))

        for record in records:
            if record.state != 'approved':
                raise ValidationError(_("Only approved records "
                                        "can be duplicated."))

            # record.copy({'creation_date': self.date, 'state': 'approved'})
            record.copy({'creation_date': self.date,})

        return {'type': 'ir.actions.act_window_close'}
