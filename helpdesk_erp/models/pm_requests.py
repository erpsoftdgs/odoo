# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import  datetime




class PMRequest(models.Model):
    """ PM chase activity is logged  """
    _name = "helpdesk.pm.requests"
    _description = "PM Requests"

    name = fields.Many2one('helpdesk.ticket' ,string ="Ticket", readonly =True)
    task_stage = fields.Char( string ="Ticket Stage" )
    date = fields.Date(string='Date', readonly =True)
    pm_user_id = fields.Many2one('res.users' , readonly =True)
    chased_user = fields.Many2one('res.users' , readonly =True , string="For User")
