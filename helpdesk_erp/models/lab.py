import gitlab
from odoo import models, api, _
from odoo.exceptions import UserError

GITLAB_URL_KEY = 'GITLAB_URL'
GITLAB_TOKEN_KEY = 'GITLAB_TOKEN'

class LabModel(models.AbstractModel):
    _name = 'lab.model'
    _description = 'Lab Model'

    def get_gitlab(self, env):
        gitlab_url = env['ir.config_parameter'].sudo().get_param(GITLAB_URL_KEY)
        gitlab_token = env['ir.config_parameter'].sudo().get_param(GITLAB_TOKEN_KEY)
        if not gitlab_url or not gitlab_token:
            raise UserError(_('Please make sure %s and %s is set in system parameters'%(GITLAB_URL_KEY, GITLAB_TOKEN_KEY)))
        return gitlab.Gitlab(gitlab_url,  private_token=gitlab_token)