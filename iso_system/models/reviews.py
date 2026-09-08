import datetime
from odoo import models, fields, api
from .activity import CreateActivityMix


class ISOReviewProjectManager(models.Model, CreateActivityMix):

    _name = 'iso.system.project.manager'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Project Manager Review'
    _rec_name = 'ncr_ref'

    def _get_iso_users(self):
        # SEARCH MODE
        return []


    external_audit = fields.Many2one('iso.system.audit.external')
    cra_ref = fields.Many2one('iso.system.corrective.action',related='external_audit.cra_ref', readonly=True)
    ncr_ref = fields.Many2one('iso.non.conformity.request', string='NCR Ref.', readonly=True,
                                          related='external_audit.ncr_ref')
    non_conformity_type = fields.Many2one('iso.non.conformity.type', string='Type', readonly=True,
                                          related='external_audit.non_conformity_type')
    department = fields.Many2one('hr.department', readonly=True, related='external_audit.department')
    implementation_date = fields.Date(required=True, readonly=True, related='external_audit.implementation_date')
    completion_date = fields.Date(related='external_audit.completion_date',string='Completed Date', required=True, readonly=True)
    date_of_audit = fields.Date(related='external_audit.date_of_audit', readonly=True)
    audit_closed_date = fields.Date(related='external_audit.audit_closed_date', readonly=True)
    date_of_review = fields.Date()
    reviews_of_meeting = fields.Text(tracking=True)
    project_manager_user = fields.Boolean(compute='_compute_logged_in_user_group')
    state = fields.Selection(
        [('project_mgr', 'Project MGR'),
         ('auditor', 'Auditor'), ('pm_review', 'PM Review'), ('cancelled', 'Cancelled')],
        tracking=True, string='Status', default='project_mgr')

    def _compute_logged_in_user_group(self):
        
        if self.env.user.has_group('iso_system.group_iso_project_manager'):
            self.project_manager_user = True
        else:
            self.project_manager_user = False

    def action_approve_auditor(self):
        self.create_comp_manager_form()
        self.write({'state': 'pm_review'})

    def action_approve_project_mgr(self):
        self.create_activity(self.env, self._name, self.id, self.department.id, 'auditor',
                             sum='Auditor')
        self.write({'state': 'auditor'})


    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_set_draft(self):
        self.write({'state': 'project_mgr'})

    def create_comp_manager_form(self):
        self.env['iso.system.compliance.manager'].sudo().create(
            {'project_manager': self.id}
        )
    @api.model_create_multi
    def create(self, vals_list):
        
        res = super(ISOReviewProjectManager, self).create(vals_list)
        self.create_activity(res.env, res._name, res.id,res.department.id,'project_manager', sum='Project Manager' )
        return res

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values:
            rec = self.track(self, self.state)
            if rec:
                return rec
        return super(ISOReviewProjectManager, self)._track_subtype(init_values)


class ISOReviewComplianceManager(models.Model, CreateActivityMix):

    _name = 'iso.system.compliance.manager'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Compliance Manager Review'
    _rec_name = 'ncr_ref'


    def _get_iso_users(self):
        # SEARCH MODE
        return []


    project_manager = fields.Many2one('iso.system.project.manager')
    cra_ref = fields.Many2one('iso.system.corrective.action',related='project_manager.cra_ref', readonly=True)
    ncr_ref = fields.Many2one('iso.non.conformity.request', string='NCR Ref.', readonly=True,
                                          related='project_manager.ncr_ref')
    non_conformity_type = fields.Many2one('iso.non.conformity.type', string='Type', readonly=True,
                                          related='project_manager.non_conformity_type')
    department = fields.Many2one('hr.department', readonly=True, related='project_manager.department')
    implementation_date = fields.Date(required=True, readonly=True, related='project_manager.implementation_date')
    completion_date = fields.Date(related='project_manager.completion_date',string='Completed Date', required=True, readonly=True)
    date_of_audit = fields.Date(related='project_manager.date_of_audit', readonly=True)
    audit_closed_date = fields.Date(related='project_manager.audit_closed_date', readonly=True)
    date_of_review = fields.Date()
    reviews_of_meeting = fields.Text(tracking=True)
    compliance_manager_user = fields.Boolean(compute='_compute_logged_in_user_group')
    state = fields.Selection(
        [
         ('auditor', 'Auditor'),
            ('comp_mgr', 'Compliance MGR'),
            ('cmpl_review', 'CMPL Review'), ('cancelled', 'Cancelled')],
        tracking=True, string='Status', default='auditor')

    def _compute_logged_in_user_group(self):
        
        if self.env.user.has_group('iso_system.group_iso_compliance_manager'):
            self.compliance_manager_user = True
        else:
            self.compliance_manager_user = None


    def action_approve_auditor(self):
        self.create_activity(self.env, self._name, self.id, self.department.id, 'compliance_manager',
                             sum='Compliance Manager')
        self.write({'state': 'comp_mgr'})

    def action_approve_comp_mgr(self):
        self.create_exec_manager_form()
        self.write({'state': 'cmpl_review'})


    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_set_draft(self):
        self.write({'state': 'auditor'})

    def create_exec_manager_form(self):
        self.env['iso.system.executive.board'].sudo().create(
            {'comp_manager': self.id}
        )

    @api.model
    def create(self, vals):
        
        res = super(ISOReviewComplianceManager, self).create(vals)
        self.create_activity(res.env, res._name, res.id,res.department.id,'auditor',
                             sum='Internal Audit' )
        return res

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values:
            rec = self.track(self, self.state)
            if rec:
                return rec
        return super(ISOReviewComplianceManager, self)._track_subtype(init_values)

class ISOReviewExecutiveBoard(models.Model, CreateActivityMix):

    _name = 'iso.system.executive.board'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Executive Board'
    _rec_name = 'ncr_ref'


    def _get_iso_users(self):
        # SEARCH MODE
        return []


    comp_manager = fields.Many2one('iso.system.compliance.manager')
    cra_ref = fields.Many2one('iso.system.corrective.action',related='comp_manager.cra_ref', readonly=True)
    ncr_ref = fields.Many2one('iso.non.conformity.request', string='NCR Ref.', readonly=True,
                                          related='comp_manager.ncr_ref')
    non_conformity_type = fields.Many2one('iso.non.conformity.type', string='Type', readonly=True,
                                          related='comp_manager.non_conformity_type')
    department = fields.Many2one('hr.department', readonly=True, related='comp_manager.department')
    implementation_date = fields.Date(required=True, readonly=True, related='comp_manager.implementation_date')
    completion_date = fields.Date(related='comp_manager.completion_date',string='Completed Date', required=True, readonly=True)
    date_of_audit = fields.Date(related='comp_manager.date_of_audit', readonly=True)
    audit_closed_date = fields.Date(related='comp_manager.audit_closed_date', readonly=True)
    date_of_review = fields.Date()
    reviews_of_meeting = fields.Text(tracking=True)

    state = fields.Selection(
        [
            ('comp_mgr', 'Compliance MGR'),
            ('executive_board', 'Executive Board'),('review_completed','Review Completed'), ('cancelled', 'Cancelled')],
        tracking=True, string='Status', default='comp_mgr')

    def action_approve_executive_board(self):
        self.write({'state': 'review_completed'})

    def action_approve_comp_mgr(self):
        #self.create_exec_manager_form()
        self.create_activity(self.env, self._name, self.id, self.department.id, 'executive_board',
                             sum='Executive Board')
        self.write({'state': 'executive_board'})


    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_set_draft(self):
        self.write({'state': 'comp_mgr'})

    def create_exec_manager_form(self):
        pass
    @api.model
    def create(self, vals):
        
        res = super(ISOReviewExecutiveBoard, self).create(vals)
        self.create_activity(res.env, res._name, res.id,res.department.id,'compliance_manager',
                             sum='Compliance Manager')
        return res


    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values:
            rec = self.track(self, self.state)
            if rec:
                return rec
        return super(ISOReviewExecutiveBoard, self)._track_subtype(init_values)
