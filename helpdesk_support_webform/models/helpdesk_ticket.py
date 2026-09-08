# -*- coding: utf-8 -*-

import logging
from odoo import fields, models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def _default_team_id(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        team_id = int(get_param(
            'helpdesk_support_webform.helpdesk_default_team_id'))
        return team_id

    user_phone_number = fields.Char(string='Customer Phone No.')
    user_company_name = fields.Char(string='Company Name')
    actual_company_id = fields.Many2one('production.access.system', string='Actual Company Name')
    team_id = fields.Many2one(
        comodel_name='helpdesk.team', default=_default_team_id)
    resolution = fields.Text()
    target_completion = fields.Date(tracking=True)
    is_readonly = fields.Boolean(help="Used to determine if the target_completion date is readonly", compute="_compute_is_readonly")
    prd = fields.Many2one('production.access.request', string="PRD")
    is_client_helpdesk = fields.Boolean(compute='_compute_is_client_helpdesk')
    is_development = fields.Boolean(compute='_compute_is_development')
    on_issue_closed = fields.Boolean(compute="_compute_issue_closed")
    csr = fields.Many2one("csm.requirements", string="Customer Services Requirements")
    support_ticket_id = fields.Many2one("helpdesk.ticket")
    client_customisation_helpdesk = fields.Char()
    security_officer_id = fields.Many2one('res.partner', related="actual_company_id.security_officer_id")
    client_user_guides = fields.Char(related="actual_company_id.client_user_guides")
    security_matrix_erp = fields.Char(related="actual_company_id.security_matrix")

    def _compute_is_readonly(self):
        user = self.env.user

        group = self.env.ref("helpdesk_build.group_developer_helpdesks")

        for rec in self:
            rec.is_readonly = group not in user.groups_id

    def write(self, vals):
        _logger.info(vals)
        if vals.get('stage_id'):
            stage = self.env['helpdesk.stage'].browse(vals.get('stage_id'))
            _logger.info('stage: %s', stage.name)
            _logger.info('%s %s %s', stage, stage.name and stage.name.lower() == 'issue closed')
            if self.is_client_helpdesk and self.on_issue_closed and (stage and stage.name.lower() == 'issue closed'):
                _logger.info('Here')
                if not self.resolution and not vals.get('resolution'):
                    raise UserError(_('Resolution is required to close issue'))
                if not self.actual_company_id and not vals.get('actual_company_id'):
                    raise UserError(_('Actual Company Name is required to close issue'))

        return super(HelpdeskTicket, self).write(vals)

    @api.depends('stage_id')
    def _compute_issue_closed(self):
        for rec in self:
            rec.on_issue_closed = rec.stage_id.name.lower() == 'client contacted'

    @api.depends('team_id')
    def _compute_is_client_helpdesk(self):
        for rec in self:
            rec.is_client_helpdesk = bool(rec.team_id.client_helpdesk)

    @api.depends('team_id')
    def _compute_is_development(self):
        for rec in self:
            rec.is_development = bool(rec.team_id.development_mode)


class TicketType(models.Model):
    _inherit = 'helpdesk.tag'

    show_on_webform = fields.Boolean()
