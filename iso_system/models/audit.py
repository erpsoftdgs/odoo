import datetime
from odoo import models, fields, api
from .activity import CreateActivityMix


class ISOAuditInternal(models.Model, CreateActivityMix):

    _name = 'iso.system.audit.internal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Internal'

    def _get_iso_users(self):
        # SEARCH MODE
        return []

    name = fields.Char(string='ADT Ref.', readonly=True)
    cra_ref = fields.Many2one('iso.system.corrective.action',  domain=[('state', '=', 'completed')])
    audit_purpose = fields.Selection([('corrective_action', 'Corrective Action'),('standard', 'Standard')], default='corrective_action')
    ncr_ref = fields.Many2one('iso.non.conformity.request', string='NCR Ref.')
    non_conformity_type = fields.Many2one('iso.non.conformity.type', string='Type')
    department = fields.Many2one('hr.department', required=True)
    implementation_date = fields.Date(required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    completion_date = fields.Date(string='Completed Date', required=True, readonly=True)
    date_of_audit = fields.Date()
    audit_type = fields.Selection([('internal', 'Internal'),('external', 'External')], default='internal')
    pre_audit_url = fields.Char(string='Pre Audit Document URL')

    document_review = fields.Text(tracking=True)
    audit_checklist = fields.Text(tracking=True)
    non_conformities_found = fields.Boolean()
    description = fields.Text()
    responsible = fields.Many2one('hr.employee')
    date_to_resolve = fields.Date()
    point_complete_closure = fields.Text(string='Points to complete closure', tracking=True)
    audit_report_url = fields.Char()
    date_of_report = fields.Date()
    audit_closed_date = fields.Date()
    post_audit_url = fields.Char(string='Post Audit Document URL')
    external_audit = fields.Boolean()
    auditor_logged_in_user = fields.Boolean(compute='_compute_logged_in_user_group', default=False)
    state = fields.Selection(
        [('auditor', 'Auditor'),
         ('compilance_mgr', 'Compliance MGR'),
         ('executive_board', 'Executive Board'), ('audited', 'Audited'), ('cancelled', 'Cancelled')],
        tracking=True, string='Status', default='auditor')

    @api.onchange('auditor_logged_in_user')    
    def _onchange_auditor_logged_in_user(self):
        self.auditor_logged_in_user = False
        if self.env.user.has_group('iso_system.group_iso_auditor'):
            self.auditor_logged_in_user = True

    @api.onchange('audit_purpose')
    def _onchange_audit_purpose(self):
        if self.audit_purpose == 'standard':
            self.cra_ref = None

    @api.onchange('cra_ref')
    def _onchange_cra_ref(self):
        if self.cra_ref:
            self.ncr_ref = self.cra_ref.ncr_ref
            self.non_conformity_type = self.cra_ref.non_conformity_type
            self.department = self.cra_ref.department
            self.implementation_date = self.cra_ref.implementation_date
            self.company_id = self.cra_ref.company_id
            self.completion_date = self.cra_ref.completion_date

    def _compute_logged_in_user_group(self):
        self.auditor_logged_in_user = False
        if self.env.user.has_group('iso_system.group_iso_auditor'):
            self.auditor_logged_in_user = True

    def action_approve_auditor(self):
        self.create_activity(self.env, self._name, self.id, self.department.id, 'compliance_manager',
                             sum='Compliance Manager')
        self.write({'state': 'compilance_mgr'})

    def action_approve_compilance_mgr(self):
        self.create_activity(self.env, self._name, self.id, self.department.id, 'executive_board',
                             sum='Executive Board')
        self.write({'state': 'executive_board'})

    def action_executive_board(self):
        for rec in self:
            if rec.audit_type == 'external':
                rec.create_external_audit()
            rec.write({'state': 'audited'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_set_draft(self):
        self.write({'state': 'auditor'})

    def create_cra_data(self, values):
        cra_id = values.get('cra_ref', None)
        
        cra_ref = self.env['iso.system.corrective.action'].search([('id', '=', cra_id)], limit=1)
        if cra_ref:
            values['ncr_ref'] = cra_ref.ncr_ref.id
            values['non_conformity_type'] = cra_ref.non_conformity_type.id
            values['department'] = cra_ref.department.id
            values['implementation_date'] = cra_ref.implementation_date
            values['company_id'] = cra_ref.company_id.id
            values['completion_date'] = cra_ref.completion_date
        return values
    
    def create_external_audit(self):
        self.env['iso.system.audit.external'].sudo().create({'internal_audit': self.id, 'cra_ref': self.cra_ref.id})

    @api.model_create_multi
    def create(self, vals_list):
        vals['name'] = self.env['ir.sequence']. \
            next_by_code('iso.system.audit')
        vals = self.create_cra_data(vals_list)
        res = super(ISOAuditInternal, self).create(vals_list)
        self.create_activity(res.env, res._name, res.id, res.department.id, 'auditor',
                             sum='Internal Audit')
        return res

    def write(self, vals):
        vals = self.create_cra_data(vals)
        return super(ISOAuditInternal, self).write(vals)
    
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values:
            rec = self.track(self, self.state)
            if rec:
                return rec
        return super(ISOAuditInternal, self)._track_subtype(init_values)

class ISOAuditExternal(models.Model, CreateActivityMix):

    _name = 'iso.system.audit.external'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'External'
    _rec_name = 'cra_ref'

    def _get_iso_users(self):
        # SEARCH MODE
        return []


    internal_audit = fields.Many2one('iso.system.audit.internal')
    cra_ref = fields.Many2one('iso.system.corrective.action')
    ncr_ref = fields.Many2one('iso.non.conformity.request', string='NCR Ref.', readonly=True,
                                          related='internal_audit.ncr_ref')
    non_conformity_type = fields.Many2one('iso.non.conformity.type', string='Type', readonly=True,
                                          related='internal_audit.non_conformity_type')
    department = fields.Many2one('hr.department', readonly=True, related='internal_audit.department')
    implementation_date = fields.Date(required=True, readonly=True, related='internal_audit.implementation_date')
    company_id = fields.Many2one('res.company',  readonly=True, related='internal_audit.company_id')
    completion_date = fields.Date(related='internal_audit.completion_date',string='Completed Date', required=True, readonly=True)
    date_of_audit = fields.Date(related='internal_audit.date_of_audit', readonly=True)
    audit_closed_date = fields.Date(related='internal_audit.audit_closed_date', readonly=True)
    external_auditor = fields.Char()
    auditor_company = fields.Char()
    date_of_external_audit = fields.Date()
    iso_complaint_issues = fields.Text(string='ISO complaint issues')
    iso_improvements_required = fields.Text(string='ISO improvements required')
    external_audit_report_url = fields.Char()
    external_audit_closed_date = fields.Date()
    auditor_logged_in_user = fields.Boolean(compute='_compute_logged_in_user_group', default=False)
    state = fields.Selection(
        [('auditor', 'Auditor'),
         ('compilance_mgr', 'Compliance MGR'),
         ('executive_board', 'Executive Board'), ('pass', 'Pass'), ('cancelled', 'Cancelled')],
        tracking=True, string='Status', default='auditor')

    @api.onchange('auditor_logged_in_user')    
    def _onchange_auditor_logged_in_user(self):
        self.auditor_logged_in_user = False
        if self.env.user.has_group('iso_system.group_iso_auditor'):
            self.auditor_logged_in_user = True
        

    def _compute_logged_in_user_group(self):
        self.auditor_logged_in_user = False
        if self.env.user.has_group('iso_system.group_iso_auditor'):
            self.auditor_logged_in_user = True

    def action_approve_auditor(self):
        self.create_activity(self.env, self._name, self.id, self.department.id, 'compliance_manager',
                             sum='Compliance Manager')
        self.write({'state': 'compilance_mgr'})

    def action_approve_compilance_mgr(self):
        self.create_activity(self.env, self._name, self.id, self.department.id, 'executive_board',
                             sum='Executive Board')
        self.write({'state': 'executive_board'})

    def action_executive_board(self):
        for rec in self:
            #if rec.external_audit:
            rec.create_project_manager_form()
            rec.write({'state': 'pass'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_set_draft(self):
        self.write({'state': 'auditor'})

    def create_project_manager_form(self):
        self.env['iso.system.project.manager'].sudo().create({'external_audit': self.id})

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values:
            rec = self.track(self, self.state)
            if rec:
                return rec
        return super(ISOAuditExternal, self)._track_subtype(init_values)
    @api.model
    def create(self, vals):
        res = super(ISOAuditExternal, self).create(vals)
        self.create_activity(res.env, res._name, res.id, res.department.id, 'auditor',
                             sum='External Audit')
        return res
