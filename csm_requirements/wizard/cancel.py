from odoo import models, fields


class ClarificationWizard(models.TransientModel):
    _name = 'cancel.reason'

    title = fields.Selection([('change', 'Client Rejected Change'),
                              ('notpay', 'Client does not want to pay'),
                              ('progress', 'Client does not want to progress')], string="Cancellation Reason")

    cancel_id = fields.Many2one('csm.requirements', string='Cancel Reason ', readonly=True,
                                default=lambda self: self.env['csm.requirements'].browse(
                                    self._context.get('active_id')))

    def send(self):
        if self.cancel_id:
            self.cancel_id.reason = self.title  # Correct assignment
            self.cancel_id.state = 'cancel'

        # cancel_id.reason = self.title
        # cancel_id.state = 'cancel'
