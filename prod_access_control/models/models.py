import base64
import logging
import os
import subprocess
import datetime
import socket
import tempfile
from urllib.parse import urlparse

import paramiko
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductionSystems(models.Model):
    _name = 'production.access.system'
    _inherit = ['mail.thread']
    _description = 'Production Access System'

    name = fields.Char(string='Client Name', required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    production_url = fields.Char(tracking=True)
    ssh_port = fields.Char(tracking=True, string='SSH Port')
    ssl_expiry_date = fields.Date(tracking=True, string='SSL Expiry Date')
    odoo_version_id = fields.Many2one('odoo.client.version')
    odoo_license_expiry_date = fields.Date(tracking=True)
    domain_expiry_date = fields.Date(tracking=True)
    use_pem = fields.Boolean()
    pem_file = fields.Binary()
    pem_location = fields.Char()
    odoo_saas = fields.Boolean()
    home_server = fields.Boolean()
    day = fields.Selection(selection=[
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ])
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    security_officer_id = fields.Many2one('res.partner', tracking=True)
    client_user_guides = fields.Char()
    security_matrix = fields.Char()
    support_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], default='active', required=True, tracking=True, string='Support Status')
    active = fields.Boolean(default=True)

    def get_pem_file_loc(self):
        if not self.pem_file:
            raise UserError(_('PEM file is empty'))
        fp = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
        fp.write(base64.decodebytes(self.pem_file))
        fp.close()
        self.write({'pem_location': fp.name})
        return fp.name

    def clear_pm_location(self):
        if self.pem_location and os.path.isfile(self.pem_location):
            os.remove(self.pem_location)


class ResCompany(models.Model):
    _inherit = 'res.company'

    grant_script_directory = fields.Char()
    extra_grant_script_directory = fields.Char()
    revoke_script_directory = fields.Char()
    extra_revoke_script_directory = fields.Char()


class ProductionScripts(models.TransientModel):
    _name = 'production.access.script'
    _inherit = 'res.config.settings'
    _description = 'Production Script'

    grant_script_directory = fields.Char(related='company_id.grant_script_directory', readonly=False)
    extra_grant_script_directory = fields.Char(related='company_id.extra_grant_script_directory', readonly=False)
    # company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    revoke_script_directory = fields.Char(related='company_id.revoke_script_directory', readonly=False)
    extra_revoke_script_directory = fields.Char(related='company_id.extra_revoke_script_directory', readonly=False)

    def set_values(self):
        res = super(ProductionScripts, self).set_values()
        select_type = self.env['ir.config_parameter'].sudo()

        select_type.set_param('prod_access_control.grant_script_directory', self.grant_script_directory)
        select_type.set_param('prod_access_control.extra_grant_script_directory', self.extra_grant_script_directory)
        select_type.set_param('prod_access_control.revoke_script_directory', self.revoke_script_directory)
        select_type.set_param('prod_access_control.extra_revoke_script_directory', self.extra_revoke_script_directory)
        return res

    @api.model
    def get_values(self):
        res = super(ProductionScripts, self).get_values()

        select_type = self.env['ir.config_parameter'].sudo()

        grant = select_type.get_param('prod_access_control.grant_script_directory')
        extra_grant = select_type.get_param('prod_access_control.extra_grant_script_directory')
        revoke = select_type.get_param('prod_access_control.revoke_script_directory')
        extra_revoke = select_type.get_param('prod_access_control.extra_revoke_script_directory')

        res.update({'grant_script_directory': grant,
                    'extra_grant_script_directory': extra_grant,
                    'revoke_script_directory': revoke,
                    'extra_revoke_script_directory': extra_revoke
                    })
        return res


class ProductionAccessApprover(models.Model):
    _name = 'production.access.approver'
    _inherit = ['mail.thread']
    _description = 'Production Access Approver'
    _rec_name = 'role'
    _sql_constraints = [
        ("unique_name", "unique(role)", "Role assigned to a user already"),
    ]

    name = fields.Many2one('res.users', string='User', required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    role = fields.Selection([('Technical Manager', 'Technical Manager'),
                             ('Production Access Manager', 'Production Access Manager'),
                             ('Project Manager', 'Project Manager')], required=True)


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    production_access_control = fields.Boolean()
    client_helpdesk = fields.Boolean()
    client_support_helpdesk = fields.Boolean()


class ProductionAccessRequest(models.Model):
    _name = 'production.access.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Production Access Request'

    def get_project_manager(self, role=None, get_id=True):
        if not role:
            role = 'Project Manager'
        approver = self.env['production.access.approver'].sudo(). \
            search([('role', '=', role), ('company_id', '=', self.env.user.company_id.id)],
                   limit=1)
        if approver:
            if get_id:
                return approver.name.id
            return approver.name
        return approver

    name = fields.Char(string='Prod. Reference', readonly=True)
    title = fields.Char(required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    prod_ticket_id = fields.Many2one('production.access.system', required=True, string='Client Name')
    assigned_to_id = fields.Many2one('res.users', required=True, default=lambda self: self.env.user.id,
                                     string='Assigned To', tracking=True)
    user_security = fields.Boolean()
    user_security_url = fields.Char()
    configuration = fields.Boolean()
    configuration_doc_url = fields.Char(string='Configuration Doc. URL')
    review_production_issue = fields.Boolean()
    other = fields.Boolean()
    data = fields.Boolean()
    data_config_url = fields.Char()
    describe = fields.Text()
    requested_by_id = fields.Many2one('res.users', readonly=True, default=lambda self: self.env.user.id, )
    team_lead_id = fields.Many2one('res.users', required=True)
    test_system = fields.Char()
    test_date = fields.Date()
    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', domain=['|', (
        'stage_id.name', 'ilike', 'Assigned'), ('stage_id.name', 'ilike', 'Client Contacted')])
    project_manager_id = fields.Many2one('res.users', default=get_project_manager, required=True)
    state = fields.Selection([('new', 'New'),
                              ('team_lead', 'Team Lead'),
                              ('project_manager', 'Project Manager'),
                              ('production_manager', 'Production Manager'),
                              ('technical', 'Technical'),
                              ('task_completed', 'Task Completed'),
                              ('access_revoked', 'Access Revoked'),
                              ('done', 'Done'),
                              ('cancelled', 'Cancelled'),
                              ], tracking=True, default='new', string='Status', copy=False)
    completion_date = fields.Date(readonly=True, copy=False)
    lock_field = fields.Boolean(default=False, copy=False)
    show_grant_access = fields.Boolean(default=False, copy=False)
    show_task_completed = fields.Boolean(default=False, copy=False)

    def confirm_request(self):
        self.create_activity(self.team_lead_id.id, 'team_lead', summary="Team Lead")
        self.send_email(self.team_lead_id)
        return self.write({'state': 'team_lead', 'assigned_to_id': self.team_lead_id.id,
                           'lock_field': True})

    def approve_team_lead(self):
        manager = self.get_project_manager(get_id=False)
        if manager:
            self.create_activity(manager.id, 'project_manager', "Project Manager")
            self.send_email(manager)
        self.write({'state': 'project_manager', })

    def cancel_request(self):
        self.write({'state': 'cancelled', })

    def approve_project_manager(self):
        manager = self.get_project_manager(role='Production Access Manager', get_id=False)
        if manager:
            self.send_email(manager)
            self.create_activity(manager.id, 'production_manager', summary='Production Access Manager')
        self.write({'state': 'production_manager', 'assigned_to_id': manager.id})

    def show_grant_access_button(self):
        self.write({'show_grant_access': True})

    def grant_access(self):
        if self.prod_ticket_id.odoo_saas is False:
            self.run_scipt()  # shhow in  production stage
        manager = self.get_project_manager(role='Technical Manager', get_id=False)
        self.send_email(manager)
        if manager:
            self.create_activity(manager.id, 'technical', 'Technical Manager')
        self.write({'state': 'technical', 'assigned_to_id': manager.id})

    def in_progress_for_technical(self):
        self.write({'show_task_completed': True})

    def task_completed(self):
        manager = self.get_project_manager(role='Production Access Manager', get_id=False)
        self.send_email(manager)
        if manager:
            self.create_activity(manager.id, 'production_manager', 'Production Access Manager')
        self.write({'state': 'task_completed', 'assigned_to_id': manager.id})

    def grant_task_completed(self):
        self.send_email(self.requested_by_id)
        self.write({'state': 'done', 'assigned_to_id': self.requested_by_id.id, 'completion_date': fields.Date.today()})
        if self.user_security:
            _logger.info('User security: %s. So closing ticket', self.user_security)
            # move ticket to closed
            issue_closed = self.env['helpdesk.stage'].search(
                [('name', 'ilike', 'Issue Closed')], limit=1)
            self.helpdesk_ticket_id.write({'stage_id': issue_closed.id})

    def send_email(self, user):
        patner_ids = []
        if user:
            patner_ids = [user.partner_id.id]
        body = _("Production Access Request %s is assigned to you") % self.name
        self.message_post(body=body, message_type='notification', partner_ids=patner_ids)

    def revoke_access(self):
        if self.prod_ticket_id.odoo_saas is False:
            self.run_revoke_script()
        self.write({'state': 'access_revoked'})

    def run_scipt(self):
        select_type = self.env['ir.config_parameter'].sudo()
        grant = select_type.get_param('prod_access_control.grant_script_directory')
        extra_grant = select_type.get_param('prod_access_control.extra_grant_script_directory')
        if not grant and not extra_grant:
            return
        if self.prod_ticket_id.home_server:
            self._execute_local([grant, extra_grant])
        else:
            self._execute_remote([grant, extra_grant])

    def run_revoke_script(self):
        select_type = self.env['ir.config_parameter'].sudo()

        revoke = select_type.get_param('prod_access_control.revoke_script_directory')
        extra_revoke = select_type.get_param('prod_access_control.extra_revoke_script_directory')
        if not revoke and not extra_revoke:
            return
        if self.prod_ticket_id.home_server:
            self._execute_local([revoke, extra_revoke])
        else:
            self._execute_remote([revoke, extra_revoke])

    def _execute_remote(self, exec_files):
        ssh = paramiko.SSHClient()
        k = None
        if self.prod_ticket_id.use_pem:
            k = paramiko.RSAKey.from_private_key_file(self.prod_ticket_id.get_pem_file_loc())
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        host = urlparse(self.prod_ticket_id.production_url).netloc
        try:
            ssh.connect(hostname=host, port=self.prod_ticket_id.ssh_port, username='odoo', timeout=10, pkey=k)
        except socket.gaierror:
            raise UserError(_('Invalid ssh host %s:%s') % (host, self.prod_ticket_id.ssh_port))
        except paramiko.ssh_exception.SSHException as e:
            self.prod_ticket_id.clear_pm_location()
            raise UserError(_(
                '%s - Please make sure the correct ssh key has been generated for the'
                ' current odoo user and the public key copied over to the remote server.') %
                (str(e)))
        except socket.timeout:
            self.prod_ticket_id.clear_pm_location()
            raise UserError(_(
                "Time out error please make sure %s is accessible on port %s and there is no firewall "
                "blocking ssh connection to the server.") %
                (host, self.prod_ticket_id.ssh_port))
        error = 0
        for exec_file in exec_files:
            if not exec_file:
                continue
            stdin, stdout, stderr = ssh.exec_command(exec_file)
            for line in stdout.read().splitlines():
                _logger.info(line)
            for line in stderr.read().splitlines():
                if 'no such file' in str(line).lower():
                    error += 1
                    if error == 2:
                        self.prod_ticket_id.clear_pm_location()
                        raise UserError(_('Script %s does not exist on remote server %s') % (exec_file, host))
                if 'permission denied' in str(line).lower():
                    self.prod_ticket_id.clear_pm_location()
                    raise UserError(
                        _('Permission denied while running script %s on remote server %s') % (exec_file, host))
                _logger.error(line)
        self.prod_ticket_id.clear_pm_location()
        ssh.close()

    def _execute_local(self, exec_files):
        error = 0
        for exec_file in exec_files:
            if not exec_file:
                continue
            
            try:
                process = subprocess.Popen(exec_file, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
            except OSError as e:
                if 'no such file' in str(e).lower():
                    error += 1
                    if error == 2:
                        raise UserError(_('Script %s does not exist on the home server') % (exec_file))
                if 'permission denied' in str(e).lower():
                    raise UserError(
                        _('Permission denied while running script %s on the home server %s') % (exec_file))
                _logger.error(e)
            

    @api.model
    def create(self, vals):
        if not vals.get('user_security') and not vals.get('configuration') \
            and not vals.get('review_production_issue') and not vals.get('other') \
                and not vals.get('data'):
            raise UserError(_('Please select one of User Security, Data, Configuration, Review production Issue, Other'))
        vals['name'] = self.env['ir.sequence']. \
            next_by_code('production.access.request')
        res = super(ProductionAccessRequest, self).create(vals)

        return res

    def create_activity(self, user_id, state, summary=''):
        self.ensure_one()
        activity_type_id = self.env.ref("prod_access_control.mail_activity_data_%s_approval" % (state)).id
        now_datetime = datetime.datetime.now()
        end_of_day_datetime = now_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env.ref('prod_access_control.model_%s' % (self._name.replace('.', '_'))).id,
            'res_id': self.id,
            'user_id': user_id,
            'activity_type_id': activity_type_id,
            'summary': "%s approval / refusal required" % (summary),
            'date_deadline': end_of_day_datetime,
        })
