# coding: utf-8
from odoo import fields, models


class TicketType(models.Model):
    _name = "ticket.type.customization"
    _rec_name = "ticket_type"
    _order = 'sequence'

    ticket_type = fields.Char(string="Ticket Type")
    webform_show = fields.Boolean(string="Show on Webform")
    sequence = fields.Integer(string="Sequence", default=10)


class TicketDropDown(models.Model):
    _inherit = 'helpdesk.ticket'

    ticket_type_id = fields.Many2one(
        'ticket.type.customization', string='Ticket Type')
