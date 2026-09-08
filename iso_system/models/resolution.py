import datetime
from odoo import models, fields, api
from .activity import CreateActivityMix

class  ISOCorrectiveAction(models.Model, CreateActivityMix):

    _name = 'iso.system.corrective.action'
    _description = 'Corrective Action'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    def _get_iso_users(self):
        #SEARCH MODE
        return []

    name = fields.Char(string='CRA Ref.', readonly=True)
    ncr_ref = fields.Many2one('iso.non.conformity.request', required=True)
    #main_ncr_ref = fields.Many2one('iso.non.conformity.request', readonly=True, related='ncr_ref.req_eval')
    non_conformity_type = fields.Many2one('iso.non.conformity.type', string='Type', readonly=True, related='ncr_ref.non_conformity_type')
    department = fields.Many2one('hr.department', readonly=True, related='ncr_ref.department')
    implementation_date = fields.Date(compute='_compute_imp_date')
    company_id = fields.Many2one('res.company', required=True, readonly=True, related='ncr_ref.company_id')
    cra_document_url = fields.Char()
    new_document_url = fields.Char()
    follow_up_date = fields.Date(string='Follow up Meetings Date Post Adoption')
    date_of_adoption = fields.Date()
    completion_date = fields.Date(copy=False, string='Completed Date', readonly=True)
    minute_of_minutes = fields.Text(tracking=True)
    executive_board = fields.Text(tracking=True)
    logged_in_user = fields.Boolean(compute='_compute_logged_in_user_group')
    logged_in_user_exec = fields.Boolean(compute='_compute_logged_in_user_group_exec')
    state = fields.Selection(
        [('team_lead', 'Team Lead'),('project_mgr', 'Project MGR'), ('quality_mgr', 'Quality MGR'), ('compilance_mgr', 'Compliance MGR'),
         ('executive_board', 'Executive Board'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
        tracking=True, string='Status', default='team_lead')

    @api.onchange('ncr_ref')
    def _onchange_ncr_ref(self):

        res_ids = self.env['iso.system.recommedation'].sudo().search([('state','=', 'implement')]).mapped('req_eval.id')
        return {'domain' : { 'ncr_ref' : [('id', 'in', res_ids)]}}

    @api.depends('ncr_ref')
    def _compute_imp_date(self):
        for rec in self:
            if rec.ncr_ref:
                mend = self.env['iso.system.recommedation'].sudo().search([('req_eval','=', rec.ncr_ref.id)], limit=1)
                if mend:
                    rec.implementation_date = mend.implementation_date
                else:
                    rec.implementation_date = None
            else:
                rec.implementation_date = None

    def _compute_logged_in_user_group(self):
        self.logged_in_user = False
        if self.env.user.has_group('iso_system.group_iso_quality_manager'):
            self.logged_in_user = True

    def _compute_logged_in_user_group_exec(self):
        self.logged_in_user_exec = False
        if self.env.user.has_group('iso_system.group_iso_executive_board'):
            self.logged_in_user_exec = True
        


    def action_approve_team_lead(self):
        self.create_activity(self.env, self._name, self.id, self.department.id, 'project_manager',
                             sum='Project Manager')

        self.write({'state':'project_mgr'})

    def action_approve_project_mgr(self):
        self.create_activity(self.env, self._name, self.id, self.department.id, 'quality_manager',
                             sum='Quality Manager')
        self.write({'state': 'quality_mgr'})

    def _compute_approver(self):
        for rec in self:
            approver = self.env['iso.approver'].search([], limit=1)
            if approver:
                rec.team_lead = approver.team_lead

    def action_approve_quality_mgr(self):
        self.create_activity(self.env, self._name, self.id, self.department.id, 'compliance_manager',
                             sum='Compliance Manager')
        self.write({'state': 'compilance_mgr'})

    def action_approve_compilance_mgr(self):
        self.create_activity(self.env, self._name, self.id, self.department.id, 'executive_board',
                             sum='Executive Board')
        self.write({'state': 'executive_board'})

    def action_executive_board(self):
        #self.create_creative_action()
        self.write({'state': 'completed', 'completion_date': datetime.date.today()})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
    def action_set_draft(self):
        self.write({'state':'team_lead'})

    def create_creative_action(self):
        pass
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence']. \
            next_by_code('iso.system.corrective.action')
        res = super(ISOCorrectiveAction, self).create(vals)
        self.create_activity(res.env, res._name, res.id,res.department.id,'team_lead',sum='Team Lead' )
        return res

    def _track_subtype(self, init_values):
        self.ensure_one()
        rec = self.track(self, self.state)
        if rec:
            return rec
        return super(ISOCorrectiveAction, self)._track_subtype(init_values)
