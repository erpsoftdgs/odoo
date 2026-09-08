# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import  datetime




class HelpdeskSprint(models.Model):
    """ Helpdesk Sprint is logged  """
    _name = "helpdesk.sprint"
    _inherit = ['mail.thread']
    _description = "Helpdesk Sprint"

    name = fields.Char(string ="Sprint Number")
    sprint_start_date = fields.Date( required=True )
    sprint_end_date = fields.Date(required=True )
    ticket_count = fields.Integer(compute='_compute_ticket_count')
    objectives = fields.Text()
    scrum_meeting_note = fields.Text()
    state = fields.Selection(
        [('draft', 'Draft'), ('submit', 'Submitted'), ('confirm', 'Confirmed'),
         ('cancelled', 'Cancelled')],
        default='draft',
        string="Status", track_visibility="onchange")

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('helpdesk.sprint')
        return super(HelpdeskSprint, self).create(vals)

    def _get_sprint_tickets(self):
        tickets = self.env['helpdesk.ticket'].search(
            [('sprint_date', '>=', self.sprint_start_date), ('sprint_date', '<=', self.sprint_end_date)])
        return tickets


    @api.depends('sprint_start_date', 'sprint_end_date')
    def _compute_ticket_count(self):
        for sprint in self:
            tickets = sprint._get_sprint_tickets()
            sprint.ticket_count = len(tickets.ids)

    def open_sprint_items(self):
        tickets = self._get_sprint_tickets()
        action = {
            'name': 'Helpdesk Ticket',
            'type': 'ir.actions.act_window',
           
            'view_mode': 'form',
            'res_model': 'helpdesk.ticket',
            'context': {},
        }

        if len(tickets.ids) > 1:
            action['domain'] = "[('id', 'in', " + str(tickets.ids) + ")]"
            action['view_mode'] = "list,form"
        else:

            action['res_id'] = tickets.id  or False
        print(action)
        return action

    def cancel_sprint_log(self):
        self.write({'state':'cancelled'})

    def submit_sprint_log(self):
        self.write({'state':'submit'})

    def approve_sprint_log(self):
        self.write({'state':'confirm'})

    def draft_sprint_log(self):
        self.write({'state':'draft'})
