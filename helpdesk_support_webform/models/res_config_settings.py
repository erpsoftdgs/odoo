# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    helpdesk_default_team_id = fields.Many2one(
        'helpdesk.team',
        string="Default Helpdesk Team",
        config_parameter='helpdesk_support_webform.helpdesk_default_team_id'
    )
    # def set_values(self):
    #     res = super(ResConfigSettings, self).set_values()
    #     param = self.env['ir.config_parameter']
    #     default_team = self.helpdesk_default_team_id.id
    #     param.set_param(
    #         'helpdesk_support_webform.helpdesk_default_team_id', default_team)
    #     return res

    # def set_values(self):
    #    super().set_values()
    #    param = self.env['ir.config_parameter'].sudo()
    #
    #    param.set_param(
    #        'helpdesk_support_webform.helpdesk_default_team_id',
    #        self.helpdesk_default_team_id.id or False
    #    )

    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     param = self.env['ir.config_parameter'].sudo()
    #     default_team_id = int(param.get_param(
    #         'helpdesk_support_webform.helpdesk_default_team_id'))
    #     default_team = self.env['helpdesk.team'].browse(default_team_id)
    #     res.update(helpdesk_default_team_id=default_team_id)
    #     return res

    #@api.model
    #def get_values(self):
    #    res = super(ResConfigSettings, self).get_values()
    #    param = self.env['ir.config_parameter'].sudo()
    #
    #    default_team_id = param.get_param(
    #        'helpdesk_support_webform.helpdesk_default_team_id'
    #    )
    #
    #    default_team = self.env['helpdesk.team'].browse(
    #        int(default_team_id)
    #    ) if default_team_id else False
    #
    #    res.update(
    #        helpdesk_default_team_id=default_team  # ✅ recordset, not int
    #    )
    #    return res

class ResCompany(models.Model):
    _inherit = 'res.company'

    helpdesk_default_team_id = fields.Many2one(
        'helpdesk.team',
        string="Default Helpdesk Team"
    )
