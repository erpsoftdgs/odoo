import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SystemEnvironment(models.Model):
    _name = 'system.environment'
    _description = 'System Environment'

    name = fields.Char('Environment', required=True)
    description = fields.Char()
    build_sequence = fields.Integer()
    change_control = fields.Boolean()
    enforce_sequence = fields.Boolean()


class BuildModule(models.Model):
    _name = 'build.module'
    _description = 'Build Module'

    name = fields.Char('Module Name', required=True)


class BuildApprover(models.Model):
    _name = 'build.approver'
    _description = 'Build Approvers'

    name = fields.Many2one('hr.department', required=True, string='Department')
    team_lead = fields.Many2one('hr.employee', required=True)
    customer_service_manager = fields.Many2one('hr.employee', required=True)


class ReleaseApprover(models.Model):
    _name = 'release.approver'
    _description = 'Release Approvers'

    name = fields.Selection(string='Role', selection=[('tech', 'Technical Manager'),
                            ('cs', 'Customer Service Manager'), ('qm', 'Quality Manager')], required=True)
    user = fields.Many2one('hr.employee', required=True)


class ReleaseStage(models.Model):
    _name = 'release.stage'
    _description = 'Release Stages'

    name = fields.Char('Release Stage', required=True)


class BuildCompany(models.Model):
    _name = 'build.company'
    _description = 'Company in multicompany build'

    name = fields.Char('Company Name', required=True)
    build_id = fields.Many2one('system.build')
    sequence = fields.Integer()
    build_status = fields.Selection(related='build_id.status')


class BuildLine(models.Model):
    _name = 'build.line'
    _description = 'Build Lines'

    build_company_id = fields.Many2one('build.company', copy=True)
    build_id = fields.Many2one('system.build')
    build_type = fields.Selection(related='build_id.build_type')
    build_status = fields.Selection(related='build_id.status')
    build_copied = fields.Boolean(related='build_id.copied')
    change_control = fields.Boolean(related='build_id.environment_id.change_control')
    module_id = fields.Many2one('build.module', required=True)
    task = fields.Char(required=True)
    description = fields.Char()
    department_id = fields.Many2one('hr.department')
    owner_id = fields.Many2one('hr.employee', required=True)
    completed = fields.Boolean(tracking=True, copy=False)
    date = fields.Datetime(readonly=True, copy=False)
    document_url = fields.Char(required=True, copy=False, default='N/A')
    line_type = fields.Char(default='build')
    approved = fields.Boolean(tracking=True)
    user_is_owner = fields.Boolean(compute='_compute_user_is_owner')
    is_team_lead = fields.Boolean(compute='_compute_user_is_team_lead')
    comment = fields.Char()
    sequence = fields.Integer()

    @api.model
    def create(self, vals):
        # print(vals)
        if vals.get('completed') is True:
            # print('completed')
            self._onchange_completed(vals)
        return super(BuildLine, self).create(vals)

    def write(self, vals):
        # print(vals)
        if vals.get('completed') is not None:
            self._onchange_completed(vals)
        return super(BuildLine, self).write(vals)

    @api.depends('owner_id')
    def _compute_user_is_owner(self):
        for rec in self:
            rec.user_is_owner = self.env.user.id == rec.owner_id.user_id.id

    # @api.depends()
    def _compute_user_is_team_lead(self):
        for rec in self:
            rec.is_team_lead = False
            emp = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
            approver_doc = self.env['build.approver'].search([('name', '=', rec.department_id.id)])
            _logger.info("Employee record: %s, Approver record found: %s", emp, approver_doc)
            if emp and approver_doc:
                if emp.id == approver_doc.team_lead.id:
                    rec.is_team_lead = True

    # @api.onchange('completed')
    def _onchange_completed(self, vals):
        build = self.build_id
        user_is_owner = self.user_is_owner
        is_new_line = False
        if vals.get('build_id') and vals.get('owner_id'):
            # creation
            is_new_line = True
            build = self.env['system.build'].browse(vals.get('build_id'))
            user_is_owner = vals.get('owner_id') == self.env.user.id
        # check user is owner
        if (user_is_owner and build) or is_new_line:
            enforce_sequence = build.environment_id.enforce_sequence
            # check that previous line is completed if enforce sequence
            if enforce_sequence and build.copied is False:
                lines = self.env['build.line'].search(
                    [('build_id', '=', build.id), ('id', '!=', self.id)])
                if lines:
                    previous_line = lines[-1]
                    if not previous_line.completed:
                        ValidationError(_('The previous line must first be completed.'))
                else:
                    pass
            # set date
            self.date = fields.Datetime.now()
            msg = "<ul><li>{} - Completed: {} <span class='fa fa-long-arrow-right' role='img' aria-label='Changed'\
                 title='Changed'></span> {}</li></ul>".format(
                self.task or vals.get('task'), self.completed or False, vals.get('completed'))
            build.message_post(body=msg)

    def action_change_control(self):
        self.build_id.write({'status': 'change'})

    def action_approve(self):
        self.write({'approved': True})
        msg = "<p>{} - Approved</p>".format(self.task)
        self.build_id.message_post(body=msg)
        if self.build_status == 'change':
            self.build_id.write({'status': 'progress'})


class TeamLeadCheck(models.Model):
    _name = 'team.lead.check'
    _description = 'Team Lead Check'
    _inherit = 'build.line'

    document_url = fields.Char(required=False)
    line_type = fields.Char(default='check')


class Configuration(models.Model):
    _name = 'build.config'
    _description = 'Configurations'
    _inherit = 'build.line'

    line_type = fields.Char(default='config')


class SystemBuild(models.Model):
    _name = 'system.build'
    _description = 'System Build'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Reference', required=True, compute='_compute_reference', store=True)
    environment_id = fields.Many2one('system.environment', required=True, string='System Environment Build')
    change_control = fields.Boolean(related='environment_id.change_control')
    customer_id = fields.Many2one('project.project')
    build_company_ids = fields.One2many('build.company', 'build_id', string='Company')
    build_type = fields.Selection(selection=[('standard', 'Standard'), ('multi', 'Multicompany')], default='standard')
    start_date = fields.Datetime(readonly=True, default=lambda r: fields.datetime.now(), copy=False)
    stage = fields.Many2one('release.stage', required=True, string='Build Status')
    status = fields.Selection(selection=[('draft', 'Draft'), ('change', 'Change Control'), ('progress', 'In Progress'),
                              ('audit', 'Audit'), ('done', 'Done')], default='draft', tracking=True, copy=False)
    # stage_name = fields.Char(related='stage.name')
    line_ids = fields.One2many('build.line', 'build_id', string='Build Lines', copy=True)
    multi_line_ids = fields.One2many('build.line', 'build_id', string='Build Lines', copy=True)
    team_lead_check_ids = fields.One2many('team.lead.check', 'build_id', copy=True)
    multi_team_lead_check_ids = fields.One2many('team.lead.check', 'build_id', copy=True)
    configuration_ids = fields.One2many('build.config', 'build_id')
    multi_configuration_ids = fields.One2many('build.config', 'build_id')
    # Project Info
    title = fields.Char(copy=False)
    manager_id = fields.Many2one('hr.employee', string='Project Manager', copy=False)
    client_project_manager = fields.Char(copy=False)
    version_number = fields.Integer(copy=False)
    version = fields.Integer(copy=False)
    confidentiality = fields.Char(copy=False)
    project_status = fields.Selection(selection=[('draft', 'Draft'),
                                                 ('pending', 'Pending Approval'),
                                                 ('approved', 'Approved')], copy=False)
    date = fields.Date(copy=False)
    history_date = fields.Date()
    signature = fields.Char()
    author_id = fields.Many2one('hr.employee')
    ncr = fields.Char(string="NCR")
    section = fields.Float()
    show = fields.Boolean(compute="_compute_approval_level")
    copied = fields.Boolean(default=False)

    # managers approvals
    tech_manager_approved = fields.Boolean(default=False)
    cs_manager_approved = fields.Boolean(default=False)
    quality_manager_approved = fields.Boolean(default=False)

    @api.depends('tech_manager_approved', 'cs_manager_approved', 'quality_manager_approved')
    def _compute_approval_level(self):
        for rec in self:
            if rec.status == "audit":
                if (self.env.user.has_group('helpdesk_build.group_developer_helpdesks')
                        and not rec.cs_manager_approved) or \
                    (self.env.user.has_group('helpdesk_build.group_helpdesk_quality_manager')
                     and not rec.quality_manager_approved) or \
                        (self.env.user.has_group('helpdesk_build.group_helpdesk_tech_manager')
                         and not rec.tech_manager_approved):
                    _logger.info("show approval btn for tech manager")
                    rec.show = True
                else:
                    rec.show = False
            else:
                rec.show = False

    @api.depends('environment_id')
    def _compute_reference(self):
        for rec in self:
            if rec.environment_id:
                rec.name = f'{rec.environment_id.name[:3]}{rec.environment_id.build_sequence}'

    @api.model
    def create(self, vals):
        env = self.env['system.environment'].browse(vals.get('environment_id'))
        vals['name'] = f'{env.name[:3]}{env.build_sequence}'
        return super(SystemBuild, self).create(vals)

    # @api.model
    # def unlink(self):
    #     _logger.info("Unlink %s %s", self.copied, self)
    #     if self.copied is True:
    #         raise ValidationError("Cannot be deleted at the moment")
    #     return super(SystemBuild, self).unlink()

    def action_submit(self):
        self.write({'status': 'progress'})

    def action_audit(self):
        self.write({'status': 'audit'})

    def action_approve(self):
        if self.env.user.has_group('helpdesk_build.group_developer_helpdesks'):
            self.cs_manager_approved = True
            _logger.info("cs approval done")
        if self.env.user.has_group('helpdesk_build.group_helpdesk_quality_manager'):
            self.quality_manager_approved = True
            _logger.info("qty approval done")
        if self.env.user.has_group('helpdesk_build.group_helpdesk_tech_manager'):
            self.tech_manager_approved = True
            _logger.info("tech approval done")

        if self.cs_manager_approved and self.quality_manager_approved and self.tech_manager_approved:
            self.status = "done"

    def action_next_system_environment(self):
        res = self.env.ref('helpdesk_build.next_environment_wizard_view_form')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Select next environment to build'),
            'res_model': 'next.environment.wizard',
            'target': 'new',
            'view_id': res.id,
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_build_id': self.id}
        }
