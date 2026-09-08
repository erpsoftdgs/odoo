# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import ValidationError


class ConfirmDuplicate(models.TransientModel):
    _name = 'confirm.duplicate'
    _description = 'Confirm Duplicate Wizard'

    date = fields.Date(string='Date-', required=True)

    def action_confirm(self):
        """
        Perform duplication of selected records upon confirmation.

        Raises:
            ValidationError: If records have multiple creation
            dates or are not in 'approved' state.
        Returns:
            dict: Action to close the current window
            or no action if no records are selected.
        """
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            # Return the action to close the window
            # even if no records are selected
            return {'type': 'ir.actions.act_window_close'}

        # Fetch records to duplicate
        records = self.env['finance.analyst'].browse(active_ids)

        # Ensure all records have the same creation date
        creation_dates = records.mapped('creation_date')
        if len(set(creation_dates)) > 1:
            raise ValidationError(_("All selected records "
                                    "must share the same creation date."))

        # Check and duplicate records
        for record in records:
            if record.state != 'approved':
                raise ValidationError(_("Only "
                                        "records in the 'approved' "
                                        "state can be duplicated."))

            record.copy({'creation_date': self.date,})

        return {'type': 'ir.actions.act_window_close'}
