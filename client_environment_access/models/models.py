import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class EnvironmentAccess(models.Model):
    _name = 'environment.access'
    _description = 'base model for client/erpsoftapp environment access models'

    server_id = fields.Char('Server ID', readonly=True, compute='_compute_server_id', store=True)
    name = fields.Char('Client')
    odoo_version = fields.Selection([('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'), ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20')])
    server = fields.Char()
    status = fields.Selection(selection=[('online', 'Online'), ('offline',
                              'Offline'), ('decommissioned', 'Decommissioned')],
                              string='Server Status', default='online')
    erpsoftapp_env = fields.Boolean(default=False)

    @api.depends('name')
    def _compute_server_id(self):
        if not self.name:
            self.name = self.server
        if not self.server_id and self.id and self.name:
            self.server_id = self.name[0:3].upper() + str(self.id).zfill(3)


class ClientEnvironment(models.Model):
    _name = 'client.environment.access'
    _inherit = ['mail.thread', 'environment.access']
    _description = 'Client Environments'

    client = fields.Boolean(default=False)
    demo = fields.Boolean(default=False)
    erpsoftapp_env = fields.Boolean(default=False)
    test_env = fields.Boolean(default=False)
    erpsoftapp_prod = fields.Boolean(default=False)
    # prod_url = fields.Char(compute='_compute_prod_url', inverse='_inverse_prod_url')
    # type = fields.Selection(selection=[
    #     ('client', 'Client Environment'),
    #     ('demo', 'Client DEMOs'),
    #     ('erp', 'erpSOFTapp Environment'),
    #     ('prod', 'erpSOFTapp Production'),
    #     ('test', 'Test Environment'),
    # ])
    prod_status = fields.Selection(selection=[('online', 'Active'), ('offline',
                                                                     'Offline'), ('decommissioned', 'Decommissioned')],
                                   string='Server Status', default='online')
    db_ids = fields.One2many('db.line', 'environment_id', string='Database')
    demo_db_ids = fields.One2many('db.line', 'environment_id')
    erp_db_ids = fields.One2many('db.line', 'environment_id')
    master_password = fields.Char()
    password = fields.Char()
    username = fields.Char()
    comment = fields.Char()
    date_granted = fields.Date()


class DBLine(models.Model):
    _name = 'db.line'
    _description = 'DB Lines'

    name = fields.Char('DB Name')
    environment_id = fields.Many2one('client.environment.access')
    server = fields.Char(related='environment_id.server')
    demo = fields.Boolean(related='environment_id.demo')
    erpsoftapp_env = fields.Boolean(related='environment_id.erpsoftapp_env')
    password_policy = fields.Boolean()
    username = fields.Char()
    password = fields.Char()
    is_helpdesk_user = fields.Boolean(compute='_compute_is_helpdesk_user')
    user_deactivation = fields.Boolean()
    url = fields.Char(compute='_compute_url', store=True)
    server_status = fields.Selection(
        selection=[('online', 'Online'), ('offline', 'Offline'), ('decommissioned', 'Decommissioned')])
    responsible_team = fields.Selection(selection=[('finance', 'Finance Analyst'), ('business', 'Business Analyst'), (
        'technical', 'Technical Analyst'), ('cust_service', 'Customer Service'), ('helpdesk', 'Helpdesk')])
    comment = fields.Char()

    @api.depends('name', 'server')
    def _compute_url(self):
        for line in self:
            line.url = '{}/web?db={}'.format(line.server, line.name)

    def _compute_is_helpdesk_user(self):
        for line in self:
            line.is_helpdesk_user = self.env.user.has_group('helpdesk.group_helpdesk_user') and \
                not self.env.user.has_group('helpdesk_erp.group_helpdesk_project_owner') and \
                not self.env.user.has_group('helpdesk_erp.group_technical_helpdesks') and \
                not self.env.user.has_group('prod_access_control.group_production_helpdesk')

    def write(self, values):
        msg = "<p>DB {} Updated</p><ul>".format(self.name)
        if 'password_policy' in values:
            msg += "<li>Password Policy: {} -> {}</li>".format(self.password_policy,
                                                               values['password_policy'])
        if 'user_deactivation' in values:
            msg += "<li>User Deactivation: {} -> {}</li>".format(self.user_deactivation,
                                                                 values['user_deactivation'])
        msg += "</ul>"
        self.environment_id.message_post(body=msg)
        result = super(DBLine, self).write(values)
        return result


class ClientService(models.Model):
    _name = 'client.service'
    _description = 'Client Services'
    _inherit = 'mail.thread'

    name = fields.Char(tracking=True)
    description = fields.Char(tracking=True)
    email = fields.Char('Login / Email', tracking=True)
    url = fields.Char(tracking=True)
    password = fields.Char(tracking=True)
