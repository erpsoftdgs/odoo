# -*- coding: utf-8 -*-
import gitlab
import time
import os
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime

logger = logging.getLogger(__name__)
from .lab import LabModel

TICKET_PRIORITY = [
    ('0', 'All'),
    ('1', 'Low priority'),
    ('2', 'High priority'),
    ('3', 'Urgent'),
]


class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    lock_fields = fields.Boolean()


class HelpdeskTeam(models.Model, LabModel):
    _inherit = 'helpdesk.team'

    default_manager = fields.Many2one('res.users', help='Task gets assigned to this user automatically ',
                                      string='Technical Manager')
    release_manager = fields.Many2one('res.users', help='Release Task gets assigned to this user automatically ',
                                      string='Release Manager')
    spec_reviewer = fields.Many2one('res.users',
                                    help='Specification review task gets assigned to this user automatically ',
                                    string='Specification reviewer')
    development_mode = fields.Boolean(help='Activate development features of the helpdesk')
    gitlab_project_id = fields.Integer(string='Gitlab Project ID')
    gitlab_project_url = fields.Char()
    client_test_url = fields.Char()
    client_test_port = fields.Char()
    client_version = fields.Many2one('odoo.client.version')
    escalate_days = fields.Integer(string='Escalate Time (Days)')
    escalation_manager_one = fields.Many2one('res.users',
                                             help='First escalation gets assigned to this user automatically ',
                                             string='Escalation Manager 1')
    escalation_manager_two = fields.Many2one('res.users',
                                             help='Second escalation gets assigned to this user automatically ',
                                             string='Escalation Manager 2')

    def _escalate_tickets(self):

        teams = self.env['helpdesk.team'].sudo().search([('development_mode', '=', True), ('escalate_days', '>', 0)])
        for team in teams:
            spec_in_review_stage = self.env['helpdesk.ticket'].sudo().search(
                [('stage_id.sequence', '=', 1), ('team_id', '=', team.id)])
            spec_in_review_stage.escalate_spec_in_review()
            test_tickets = self.env['helpdesk.ticket'].sudo().search(
                [('stage_id.sequence', '=', 7), ('team_id', '=', team.id)])
            test_tickets.escalate_spec_in_test()
            test_tickets = self.env['helpdesk.ticket'].sudo().search(
                [('stage_id.sequence', '=', 4), ('team_id', '=', team.id)])
            test_tickets.escalate_spec_in_cr_rework()

    def create_gitlab_project(self):
        if not self.client_version:
            raise UserError(_('The client version must be specified to create a repository'))
        lab = self.get_gitlab(self.env)
        try:
            file_p = os.path.join(os.path.dirname(os.path.abspath(__file__)))
            fil = os.path.join(file_p, '../data/base.tar.gz')
            project = lab.projects.import_project(
                file=open(fil, 'rb'), name='%s Addons' % self.name,
                path='%s-addons' % self.name.lower().replace(' ', '-'), namespace=self.client_version.gitlab_group_id,
                overwrite=True, override_params={'description': '%s Addons' % (self.name)})
            project_import = lab.projects.get(project['id'], lazy=True).imports.get()
            while project_import.import_status != 'finished':
                time.sleep(1)
                project_import.refresh()
            project = lab.projects.get(project['id'])
            project.variables.create({'key': 'TEST_CLIENT', 'value': self.client_test_url})
            project.variables.create({'key': 'TEST_PORT', 'value': self.client_test_port})
            self.gitlab_project_id = int(project.id)
            self.gitlab_project_url = str(project.web_url)
            self.write({'gitlab_project_id': project.id})
            self.write({'gitlab_project_url': project.web_url})
            # raise UserError(_('Repository Created'))
        except gitlab.exceptions.GitlabCreateError as e:
            raise UserError(_(str(e)))


class HelpdesTick(models.Model, LabModel):
    _inherit = 'helpdesk.ticket'

    _sql_constraints = [('technical_name_unique', 'unique(technical_name)', 'Technical name already exist!')]

    @api.onchange('team_id', 'parent_ticket')
    def _get_child_ticket_domain(self):

        return {'domain': {'apply_parent_ticket': [('parent_ticket', '=', True), ('team_id', '=', self.team_id.id)]}}

    spec_written_by = fields.Many2one('res.users', string="Spec. Written By")
    odoo_supported_version = fields.Selection(
        [('11', 'Odoo 11'), ('12', 'Odoo 12'), ('13', 'Odoo 13'), ('14', 'Odoo 14'), ('15', 'Odoo 15'), ('16', 'Odoo 16'), ('17', 'Odoo 17'), ('18', 'Odoo 18'), ('19', 'Odoo 19'), ('20', 'Odoo 20')])
    summary = fields.Char()
    remote_project_id = fields.Integer()
    remote_short_commit = fields.Char()
    spec_drive_url_link = fields.Char(string="Spec. Url")
    bpmn_spec_url = fields.Char(string="BPMN Spec. Url", required=False)
    tested_by_user = fields.Many2one('res.users', string="Tested By")
    final_team_lead_approval_by = fields.Many2one('res.users', string="Final Test Approval By")
    team_lead_approval_date = fields.Date(string="Final Approval Date")
    manager_approval_by = fields.Many2one('res.users', string="Manager Approval By")
    cleint_approved = fields.Boolean(string="Client Approved")
    pm_priority = fields.Selection(TICKET_PRIORITY, string='PM Priority', default='0')
    project_owner = fields.Many2one('res.users', readonly=True)
    team_lead = fields.Many2one('res.users')
    spec_approval_date = fields.Date(readonly=True)
    spec_rev_assigned_date = fields.Date(readonly=True)
    review_cr_assigned_date = fields.Date(readonly=True)
    test_stage_assigned_date = fields.Date(readonly=True)
    # spec_writer_spec_rev_assigned_date = fields.Date(readonly=True)
    development_mode = fields.Boolean(related='team_id.development_mode', readonly=True)

    expected_allocated_days = fields.Integer(default=0)
    treat_urgent = fields.Boolean()

    sprint_date = fields.Date(track_visibility='onchange')  # compute='_compute_sprint_date', store=True)
    sprint_type = fields.Selection([('sprint_a', 'Sprint A'),
                                    ('sprint_b', 'Sprint B')], default='')
    lock_stage = fields.Boolean(compute='_compute_lock_stage')

    parent_ticket = fields.Boolean(default=True)
    apply_parent_ticket = fields.Many2one('helpdesk.ticket')

    child_ticket_count = fields.Integer(compute='_compute_child_ticket_count', default=0)

    approval_requested = fields.Boolean(default=False)
    push_for_lead_review = fields.Boolean()

    current_dev_status = fields.Selection([('review', 'Review & Analysis'), ('developing', 'Implementation'),
                                           ('testing', 'Testing'), ('completed', 'Completed')], default='review',
                                          string='Dev. Status', readonly=True, track_visibilty='onchange')
    expected_completion_date = fields.Date()
    linked_module = fields.Many2one('module.repository')
    developer = fields.Many2one('res.users')
    tester = fields.Many2one('res.users')
    technical_name = fields.Char()
    remote_developer = fields.Many2one('hr.employee')

    new_spec_approval = fields.Selection([('spec_approved', 'Approved'), ('spec_rejected', 'Not Approved')], default='',
                                         track_visibilty='onchange')
    current_test_server = fields.Char()
    current_db = fields.Char()
    br_code = fields.Char(string="BR Code")

    tech_issue = fields.Char(string="Tech. Issue")
    spec_test_url_link = fields.Char(string="Spec. Test Url")
    issue_sheet_url_link = fields.Char(string="Spec. Issue Url")

    user_guide = fields.Char()
    configuration_document = fields.Char()
    production_release_note = fields.Char(string='Release Note')
    security_matrix = fields.Char()

    stage_name = fields.Char(related='stage_id.name', readonly=True)
    stage_sequence = fields.Integer(related='stage_id.sequence', readonly=True)
    test_users = fields.Char()

    release_note = fields.Text()

    def escalate_spec_in_review(self):
        # check in correct stage before executing

        for rec in self:
            if rec.stage_id.sequence != 1:
                continue
            if (rec.user_id == rec.team_lead or rec.user_id == rec.spec_written_by) and rec.spec_rev_assigned_date:
                datediff = fields.date.today() - rec.spec_rev_assigned_date
                self.escalate_to_manager(datediff)

    def escalate_spec_in_test(self):
        for rec in self:
            if rec.stage_id.sequence != 7:
                continue
            tags = rec.tag_ids.mapped('name')
            if 'Testing Passed' not in tags and rec.test_stage_assigned_date:
                datediff = fields.date.today() - rec.test_stage_assigned_date
                self.escalate_to_manager(datediff)

    def escalate_spec_in_cr_rework(self):
        for rec in self:
            if rec.stage_id.sequence != 4 or not rec.review_cr_assigned_date:
                continue
            datediff = fields.date.today() - rec.review_cr_assigned_date
            self.escalate_to_manager(datediff, manager_one=self.team_id.release_manager,
                                     manager_two=self.team_id.escalation_manager_one)

    def escalate_to_manager(self, datediff, manager_one=None, manager_two=None):
        days = datediff.days
        manager_two_days = self.team_id.escalate_days + 2
        if days == self.team_id.escalate_days + 1:  # Only escalate a day after escalation day
            # escalate to first manager
            manager_one = manager_one or self.team_id.escalation_manager_one
            self.escalation_manager_activity(manager_one)
        elif days == manager_two_days + 1:
            manager_two = manager_two or self.team_id.escalation_manager_two
            self.escalation_manager_activity(manager_two, "2")

    def _compute_lock_stage(self):
        for rec in self:
            if rec.stage_id.lock_fields:
                if self.env.user.has_group("helpdesk_erp.group_developer_helpdesks"):
                    rec.lock_stage = False
                elif self.env.user.has_group("helpdesk_erp.group_technical_helpdesks"):
                    rec.lock_stage = False
                elif self.env.user.has_group("helpdesk_erp.group_release_manager_helpdesks"):
                    rec.lock_stage = False
                elif self.env.user.has_group("helpdesk.group_helpdesk_manager"):
                    rec.lock_stage = False
                else:
                    rec.lock_stage = True
            else:
                rec.lock_stage = False

    @api.depends('sprint_type')
    def _compute_sprint_date(self):
        for rec in self:
            rec.sprint_date = fields.Date.context_today(rec)

    def open_child_tickets(self):
        ticket_ids = self.env['helpdesk.ticket'].search([['apply_parent_ticket', '=', self.id]])
        action = {
            'name': 'Helpdesk Ticket',
            'type': 'ir.actions.act_window',

            'view_mode': 'tree,form',
            'res_model': 'helpdesk.ticket',
            # 'view_id': record.picking_id.id,
            'domain': "[('id', 'in', " + str(ticket_ids.ids) + ")]",
            'context': {},

        }

        return action

    @api.depends('apply_parent_ticket')
    def _compute_child_ticket_count(self):
        for rec in self:
            rec.child_ticket_count = self.env['helpdesk.ticket'].search_count([['apply_parent_ticket', '=', rec.id]])

    def get_ticket_next_stage(self, stage_id, team_id=None):
        team_id = team_id or self.team_id
        stage = self.env['helpdesk.stage'].search([('sequence', '=', stage_id), ('team_ids.id', '=', team_id.id)],
                                                  limit=1)
        if not stage:
            self.message_post(
                body='Cannot get %s stage for client %s. Please move manually ' % (stage_id, team_id.name))
        return stage

    def button_spec_approved(self):
        self.new_spec_approval = 'spec_approved'
        self.spec_approval_date = fields.date.today()
        self.project_owner = self.env.user
        if not self.spec_written_by:
            raise UserError(_('Please put in the  spec. writter of this module ! '))
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env.ref('helpdesk.model_helpdesk_ticket').id,
            'res_id': self.id,
            'user_id': self.spec_written_by.id,
            'activity_type_id': self.env.ref("helpdesk_erp.mail_activity_specification_delivery").id,
            'summary': "Specification Delivery",
            'date_deadline': datetime.datetime.now() + datetime.timedelta(days=5),
        })

    def button_spec_rejected(self):
        self.new_spec_approval = 'spec_rejected'
        self.spec_approval_date = fields.date.today()
        self.project_owner = self.env.user
        self.approval_requested = False
        self.push_for_lead_review = False

    def request_approval(self):
        # print(self.env.user.id)
        self.write({'user_id': self.team_id.spec_reviewer.id, 'approval_requested': True})

    def submit(self):
        # print(self.env.user.id)
        self.write({'user_id': self.team_lead.id})

    def reviewed(self):
        # print(self.env.user.id)
        self.write({'user_id': self.spec_written_by.id})
        if not self.spec_written_by:
            raise UserError(_('Please put in the  spec. writter of this module ! '))
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env.ref('helpdesk.model_helpdesk_ticket').id,
            'res_id': self.id,
            'user_id': self.spec_written_by.id,
            'activity_type_id': self.env.ref("helpdesk_erp.mail_activity_specification_update_required").id,
            'summary': "Specification Update Required",
            'date_deadline': datetime.datetime.now() + datetime.timedelta(days=1),
        })

    def in_review_reviewed(self):
        # print(self.env.user.id)
        self.write({'user_id': self.team_lead.id})

    def in_review_submit(self):
        # print(self.env.user.id)
        self.write({'user_id': self.team_id.spec_reviewer.id})

    def return_back_for_fix(self):
        for rec in self:
            rec.user_id = rec.spec_written_by

            next_stage = self.get_ticket_next_stage(0, rec.team_id)
            rec.stage_id = next_stage.id if next_stage else rec.stage_id
            rec.new_spec_approval = 'spec_rejected'
            rec.approval_requested = False
            rec.push_for_lead_review = False

    def push_lead_review(self):
        for rec in self:
            rec.user_id = rec.team_lead
            rec.push_for_lead_review = True

    def push_to_review(self):

        for rec in self:
            if not rec.ticket_type_id.name == 'Issue' and not rec.br_code:
                raise UserError(_('Please make sure the BR Code is filled when ticket is not an issue!'))
            if not rec.spec_written_by or not rec.spec_drive_url_link or not rec.summary:
                raise UserError(_('Please make sure the specification summary, owner and link to document is filled !'))
            rec.user_id = rec.team_id.spec_reviewer
            next_stage = self.get_ticket_next_stage(1, rec.team_id)
            rec.spec_rev_assigned_date = fields.date.today()
            rec.stage_id = next_stage.id if next_stage else rec.stage_id

    def add_to_job_queue(self):
        if not self.env.user.has_group("helpdesk_erp.group_technical_helpdesks"):
            raise UserError(_('Only Technical users can add ticket to Job Queue!'))
        for rec in self:
            if not rec.sprint_type:
                raise UserError(_('Please select a sprint for this ticket!'))
            if not rec.spec_written_by:
                raise UserError(_('Please make sure the specification  owner is filled !'))
            if rec.expected_allocated_days == 0:
                raise UserError(_('Allocated days for module cannot be 0 !'))
            if rec.user_id.id == self.env.user.id:
                raise UserError(_('Please re-assign to a new user !'))

            next_stage = self.get_ticket_next_stage(2, rec.team_id)

            rec.stage_id = next_stage.id if next_stage else rec.stage_id
            self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('helpdesk.model_helpdesk_ticket').id,
                'res_id': rec.id,
                'user_id': rec.spec_written_by.id,
                'activity_type_id': self.env.ref("helpdesk_erp.mail_activity_test_script_remainder").id,
                'summary': "Test script required for approved specification",
                'date_deadline': datetime.datetime.now() + datetime.timedelta(days=5),
            })

    def start_development(self):
        if not self.env.user.has_group("helpdesk_erp.group_technical_helpdesks"):
            raise UserError(_('Only Technical users can start Development!'))
        for rec in self:
            if not rec.tester:
                raise UserError(_('Please put in the tester of this module ! '))
            if not rec.linked_module:
                raise UserError(_('Please create a module in the repo and link to this ticket ! '))
            if not rec.expected_completion_date or not rec.developer:
                raise UserError(
                    _('Please input when module is going to be completed and assign yourself as the developer !'))
            next_stage = self.get_ticket_next_stage(3, rec.team_id)
            rec.stage_id = next_stage.id if next_stage else rec.stage_id
            rec.current_dev_status = 'developing'
            rec.linked_module.state = 'in_development'

    def start_development_testing(self):
        if not self.env.user.has_group("helpdesk_erp.group_technical_helpdesks"):
            raise UserError(_('Only Technical users can start Development Testing!'))
        for rec in self:
            if not rec.spec_test_url_link:
                raise UserError(
                    _('Specification test link has to be present please contact spec owner @%s !' % (
                        rec.spec_written_by.name)))
            if not rec.linked_module:
                raise UserError(_('Please create a module in the repo and link to this ticket ! '))
            if not rec.technical_name:
                raise UserError(_('Please input the module technical name you used during development ! '))
            # if rec.linked_module:
            #    raise UserError(
            #       _('Please specify all the models and modules this module depends on in the modules repo! '))
            next_stage = self.get_ticket_next_stage(5, rec.team_id)
            rec.stage_id = next_stage.id if next_stage else rec.stage_id
            self.message_subscribe(partner_ids=rec.tester.mapped('partner_id').ids)
            rec.current_dev_status = 'testing'

    def complete_development(self, force=False):
        for rec in self:
            if not force:
                if not self.env.user.has_group("helpdesk_erp.group_technical_helpdesks"):
                    raise UserError(_('Only Technical users can start Complete Development!'))

                if not rec.linked_module:
                    raise UserError(_('Please create a module in the repo and link to this ticket ! '))
                rec.linked_module.state = 'completed'
            else:
                logger.info('Completing forced development')
                self.message_subscribe(partner_ids=rec.tester.mapped('partner_id').ids)
                self.message_post(
                    body='Module completed by developer and automatically moved to test server please upgrade & install module and push to test ')
            rec.current_dev_status = 'completed'
            rec.linked_module.state = 'completed'
            next_stage = self.get_ticket_next_stage(6, rec.team_id)
            rec.stage_id = next_stage.id if next_stage else rec.stage_id
            rec.user_id = rec.team_id.default_manager

    # def development_completed(self):
    def push_for_test(self):
        for rec in self:
            if not rec.current_test_server or not rec.current_db:
                raise UserError(
                    _('Please make sure test information are present ! '))
            rec.user_id = rec.spec_written_by
            next_stage = self.get_ticket_next_stage(7, rec.team_id)
            rec.stage_id = next_stage.id if next_stage else rec.stage_id
            rec.test_stage_assigned_date = fields.date.today()
            if self.spec_written_by.id:
                self.env['mail.activity'].sudo().create({
                    'res_model_id': self.env.ref('helpdesk.model_helpdesk_ticket').id,
                    'res_id': rec.id,
                    'user_id': self
                        .spec_written_by.id,
                    'activity_type_id': self.env.ref("helpdesk_erp.mail_activity_specification_testing_required").id,
                    'summary': "Testing Required For This Module",
                    'date_deadline': datetime.datetime.now() + datetime.timedelta(days=1),
                })

    def test_failed(self):
        for rec in self:
            if not rec.issue_sheet_url_link or not rec.tested_by_user:
                raise UserError(
                    _('Please make sure issue sheet is specified and test user is specified ! '))

            next_stage = self.get_ticket_next_stage(4, rec.team_id)
            rec.stage_id = next_stage.id if next_stage else rec.stage_id
            rec.current_dev_status = 'developing'
            rec.user_id = rec.developer
            rec.review_cr_assigned_date = fields.date.today()
            if rec.tag_ids.filtered(lambda r: r.name.lower() == 'remote'):
                lab = self.get_gitlab(self.env)
                project = lab.projects.get(rec.remote_project_id)
                project.issues.create({'title': 'There is an issue with your project',
                                       'description': 'Please check document  %s' % (rec.issue_sheet_url_link)})

    def test_completed(self):
        for rec in self:
            if not rec.production_release_note or not rec.user_guide or not rec.configuration_document:
                raise UserError(
                    _('Please fill the production release information! '))
            if not rec.tested_by_user:
                raise UserError(
                    _('Please make sure issue sheet is specified and test user is specified ! '))

            next_stage = self.get_ticket_next_stage(8, rec.team_id)
            rec.stage_id = next_stage.id if next_stage else rec.stage_id
            rec.final_team_lead_approval_by = self.env.user
            rec.team_lead_approval_date = fields.date.today()
            rec.user_id = rec.team_id.release_manager
            if rec.tag_ids.filtered(lambda r: r.name.lower() == 'remote'):
                lab = self.get_gitlab(self.env)
                project = lab.projects.get(rec.remote_project_id)
                for issue in project.issues.list():
                    issue.state_event = 'close'
                    issue.save()

    def move_to_production(self):
        for rec in self:
            rec.linked_module.in_production = True
            rec.linked_module.released_date = fields.date.today()
            rec.linked_module.state = 'released'
            next_stage = self.get_ticket_next_stage(9, rec.team_id)
            rec.stage_id = next_stage.id if next_stage else rec.stage_id

    def get_or_create_trigger(self, project):
        trigger_decription = 'client_test_trigger_id'
        for t in project.triggers.list():
            if t.description == trigger_decription:
                return t
        return project.triggers.create({'description': trigger_decription})

    def merge_remote_module(self):
        for rec in self:
            team_id = rec.team_id
            lab = self.get_gitlab(self.env)
            if not rec.remote_project_id or rec.remote_project_id == 0:
                raise UserError(
                    _('Remote project id must be present  !'))

            project = lab.projects.get(rec.remote_project_id)
            trigger = self.get_or_create_trigger(project=project)
            logger.info('Triggering main pipeline for tickect %s on project %s' % (rec.technical_name, project.name))
            pipeline = project.trigger_pipeline('master', trigger.token,
                                                variables={"TEST_PORT": team_id.client_test_port,
                                                           "TEST_CLIENT": team_id.client_test_url,
                                                           'MODULE': rec.technical_name,
                                                           'COMMIT': rec.remote_short_commit})
            while pipeline.finished_at is None:
                pipeline.refresh()
                time.sleep(1)
            logger.info('Pipeline completed')
            rec.complete_development(force=True)

    def pm_chase_activity(self):

        for rec in self:
            # self.env['mail.activity'].sudo().search([('res_id','=', rec.id),('res_model_id','=',self.env.ref('helpdesk.model_helpdesk_ticket').id)]).unlink()
            self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('helpdesk.model_helpdesk_ticket').id,
                'res_id': rec.id,
                'user_id': rec.user_id.id,
                'activity_type_id': self.env.ref("helpdesk_erp.mail_activity_pm_reminder").id,
                'summary': "Task Completion Reminder",
                'date_deadline': datetime.datetime.now(),
            })
            self.env['helpdesk.pm.requests'].sudo().create({
                'name': rec.id,
                'chased_user': rec.user_id.id,
                'task_stage': rec.stage_id.name,
                'pm_user_id': self.env.user.id,
                'date': datetime.datetime.now(),
            })

    def escalation_manager_activity(self, user_id, manager_name="1"):

        for rec in self:
            # self.env['mail.activity'].sudo().search([('res_id','=', rec.id),('res_model_id','=',self.env.ref('helpdesk.model_helpdesk_ticket').id)]).unlink()
            self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('helpdesk.model_helpdesk_ticket').id,
                'res_id': rec.id,
                'user_id': user_id.id,
                'activity_type_id': self.env.ref("helpdesk_erp.mail_activity_escalation_manager").id,
                'summary': "Ticket Escalation %s (Assigned User %s)" % (manager_name, rec.user_id.name),
                'date_deadline': datetime.datetime.now(),
            })


class ModulesModel(models.Model):
    _name = 'module.model'
    _description = 'Models'

    name = fields.Char()
    _sql_constraints = [
        ('technical_name_uniq',
         'unique(name)',
         _('model name already existed!')),
    ]
    documentation = fields.Text()


class ModuleRpository(models.Model):
    _name = 'module.repository'
    _description = 'Module Repository'
    _inherit = ['mail.thread']

    _sql_constraints = [
        ('technical_name_uniq',
         'unique(technical_name)',
         _('Module technical name must be unique!')),
    ]

    name = fields.Char(require=True)
    technical_name = fields.Char()
    in_production = fields.Boolean(default=False)
    app_store = fields.Boolean()
    models_affected = fields.Many2many('module.model')
    functionality_ids = fields.Many2many('helpdesk.functionality.tags')
    dependencies = fields.Many2many('module.repository', 'modules_repository_rel', 'modules_column_rel')
    developer = fields.Many2one('hr.employee', required=True)
    client = fields.Many2one('res.partner', required=True)
    released_date = fields.Date()
    release_code = fields.Char()
    odoo_supported_version = fields.Selection(
        [('11', 'Odoo 11'), ('12', 'Odoo 12'), ('13', 'Odoo 13'), ('14', 'Odoo 14'), ('15', 'Odoo 15'), ('16', 'Odoo 16'), ('17', 'Odoo 17'), ('18', 'Odoo 18'), ('19', 'Odoo 19'), ('20', 'Odoo 20')] )
    summary = fields.Char()
    change_request_ids = fields.One2many('module.change.requests', 'helpdesk_ticket_id', string='Change Requests')
    state = fields.Selection([('not_developed', 'Not Developed'),
                              ('in_development', 'In Development'),
                              ('completed', 'Completed'),
                              ('released', 'Released'),
                              ('deprecated', 'Deprecated'),
                              ], string='Status', track_visibilty='onchange', default='not_developed')

    @api.onchange('in_production')
    def _change_state_production(self):
        for rec in self:
            if rec.in_production:
                if not rec.released_date:
                    raise UserError(_('Please put in released date! '))
                rec.state = 'released'
            else:
                rec.state = 'completed'


class ModuleChangeRequest(models.Model):
    _name = 'module.change.requests'

    change_request_num = fields.Integer(required=True)
    date = fields.Date()
    ticket_id = fields.Many2one('helpdesk.ticket', required=True)
    release_type = fields.Selection([('issue', 'Issue'), ('enhancement', 'Enhancement')], default='enhancement')
    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket')


class FunctionalityTags(models.Model):
    """ Tags of helpdesk used as functionality """
    _name = "helpdesk.functionality.tags"
    _description = "Functionality Tags"

    name = fields.Char(required=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!"),
    ]
