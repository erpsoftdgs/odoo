from odoo import models, fields, api, _
from odoo.exceptions import UserError
import gitlab
from  .lab import LabModel


class  OdooCLient(models.Model, LabModel):

    _name = 'odoo.client.version'
    _description = 'Odoo Version'

    name = fields.Char()
    gitlab_group_id = fields.Char(string='Gitlab Group ID')

