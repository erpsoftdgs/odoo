import datetime
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from .activity import CreateActivityMix

class NonConformityTypes(models.Model):

    _name = 'iso.non.conformity.type'
    _description = 'Non Conformity Type'

    name = fields.Char(required=True)


class ConcessionsTypes(models.Model):

    _name = 'iso.concessions.type'
    _description = 'Concessions Type'

    name = fields.Char(required=True)


class NonConformityRequest(models.Model, CreateActivityMix):

    _name = 'iso.non.conformity.request'
    _description = 'Non Conformity Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='NCR Ref.', readonly=True)
    non_conformity_type = fields.Many2one('iso.non.conformity.type', string='Type', required=True)
    department = fields.Many2one('hr.department', required=True)
    completion_date = fields.Datetime(required=True)
    team_lead = fields.Many2one('res.users', compute='_compute_approver', readonly=True)
    company_id = fields.Many2one('res.company', required=True)
    description = fields.Text(required=True)
    effect = fields.Text(required=True)
    observation = fields.Text(tracking=True)
    resolution_suggestion = fields.Text(tracking=True, required=True)
    state = fields.Selection([('draft', 'Draft'), ('team_lead', 'Team Lead'), ('project_mgr','Project MGR'),
                               ('quality_mgr', 'Quality MGR'), ('evaluation', 'Evaluation'), ('cancelled', 'Cancelled')],tracking=True,string='Status', default='draft')
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence']. \
            next_by_code('iso.non.conformity.request')
        return super(NonConformityRequest, self).create(vals)

    @api.depends('department')
    def _compute_approver(self):
        for rec in self:
            approver = self.env['iso.approver'].sudo().search([('department','=',rec.department.id)], limit=1)
            if approver:
                rec.team_lead = approver.team_lead
            else:
                rec.team_lead = None

    def subscribe_users(self):
        self.message_subscribe(partner_ids=self.env.user.mapped('partner_id').ids)

    def action_submit(self):
        self.subscribe_users()
        self.create_activity(self.env, self._name, self.id,self.department.id,'team_lead',sum='Team Lead' )
        self.write({'state': 'team_lead'})

    def action_approve_team_lead(self):
        self.subscribe_users()
        self.create_activity(self.env, self._name, self.id, self.department.id, 'project_manager', sum='Project Manager')
        self.write({'state':'project_mgr'})

    def action_approve_project_mgr(self):
        self.subscribe_users()
        self.create_activity(self.env, self._name, self.id, self.department.id, 'quality_manager',
                             sum='Quality Manager')

        self.write({'state':'quality_mgr'})

    def action_approve_quality_mgr(self):
        self.subscribe_users()
        self.create_evaluation()
        self.write({'state':'evaluation'})

    def create_evaluation(self):
        self.env['iso.system.evaluation'].sudo().create({'non_conform_req': self.id})
    def action_cancel(self):
        self.write({'state': 'cancelled'})
    def action_set_draft(self):
        self.write({'state':'draft'})

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values:
            rec = self.track(self, self.state)
            if rec:
                return rec
        return super(NonConformityRequest, self)._track_subtype(init_values)

class EvaluationModel(models.Model, CreateActivityMix):

    _name = 'iso.system.evaluation'
    _description = 'Evaluation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    non_conform_req = fields.Many2one('iso.non.conformity.request')
    name = fields.Char(related='non_conform_req.name', string='NCR Ref.', readonly=True)
    non_conformity_type = fields.Many2one('iso.non.conformity.type', string='Type', related='non_conform_req.non_conformity_type', required=True, readonly=True)
    department = fields.Many2one('hr.department', related='non_conform_req.department', required=True, readonly=True)
    completion_date = fields.Datetime(related='non_conform_req.completion_date',required=True, readonly=True)
    company_id = fields.Many2one('res.company', related='non_conform_req.company_id', required=True, readonly=True)
    active_document_link = fields.Char(string='Active Document URL')
    meeting_date_assesment = fields.Datetime()
    employees = fields.Many2many('hr.employee')
    notes = fields.Text()
    minutes_of_meeting = fields.Text(help='Include the list of attendees to this minute', tracking=True)
    risk_assesment = fields.Text(tracking=True)
    state = fields.Selection([('internal_audit', 'Internal Audit'), ('quality_mgr', 'Quality MGR'), ('compliance_mgr', 'Compliance MGR'),
                              ('executive_board', 'Executive Board'), ('recommendation', 'Recommendation'), ('cancelled', 'Cancelled')],
                             tracking=True, string='Status', default='internal_audit')
    edit_minute = fields.Boolean(compute='_compute_edit_minute')
    edit_risk_assesment = fields.Boolean(compute='_compute_risk_assesment')
    meeting_id = fields.Many2one('calendar.event')

    def _compute_edit_minute(self):
       if self.env.user.has_group('iso_system.group_iso_auditor'):
            self.edit_minute = True
       else:
            self.edit_minute = False

    def _compute_risk_assesment(self):
       if self.env.user.has_group('iso_system.group_iso_auditor') or self.env.user.has_group('iso_system.group_iso_quality_manager'):
            self.edit_risk_assesment = True
       else:
            self.edit_risk_assesment = False


    def create_recommendation(self):
        self.env['iso.system.recommedation'].sudo().create(
            {'req_eval': self.non_conform_req.id}
        )

    def action_view_meeting(self):
        view = self.env.ref('calendar.view_calendar_event_form')
        return {
            'name': _('Meeting'),
            'view_mode': 'form',
            'res_model': 'calendar.event',
            'res_id': self.meeting_id.id or None,
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            #'target': 'new',
        }

    def action_approve_internal_audit(self):
        self.create_activity(self.env, self._name, self.id, self.department.id, 'quality_manager',
                             sum='Quality Manager')
        self.write({'state': 'quality_mgr'})

    def action_approve_quality_mgr(self):
        self.create_activity(self.env, self._name, self.id, self.department.id, 'compliance_manager',
                             sum='Compliance Manager')
        self.write({'state': 'compliance_mgr'})

    def action_approve_compliance_mgr(self):
        self.create_activity(self.env, self._name, self.id, self.department.id, 'executive_board',
                             sum='Executive Board')

        self.write({'state': 'executive_board'})

    def action_executive_board(self):
        self.create_recommendation()
        self.write({'state': 'recommendation'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
    def action_set_draft(self):
        self.write({'state':'internal_audit'})
    def create_meeting(self, meeting_date, partners):

        for res in self:

            cal = self.env['calendar.event'].sudo().create(
                {
                    'name': '%s Evaluation Meeting' % (res.name),
                    'partner_ids': [(6, 0, partners)],
                    'stop': meeting_date + datetime.timedelta(hours=2),
                    'start': meeting_date,
                    'duration': 2,
                    'alarm_ids': [(6,0,[self.env.ref('calendar.alarm_notif_1').id])]
                }
            )
            res.write({'meeting_id': cal.id})

    @api.model
    def create(self, vals):
        res = super(EvaluationModel, self).create(vals)
        #if 'state' in vals and  vals['state'] == 'internal_audit':
        self.create_activity(res.env, res._name, res.id, res.department.id, 'auditor',
                             sum='Internal Audit')
          
        if res.meeting_date_assesment:
            pass
        return res

    def write(self, vals):
        partners = []
        if 'employees' in vals:
           emp_ids = vals['employees'][0][2]
           employee_ids = self.env['hr.employee'].sudo().search([('id','in', emp_ids)])
           partners.extend([emp.user_partner_id.id for emp in employee_ids if emp.user_partner_id.id is not None])
        for emp in self.employees:
            if emp.user_partner_id.id and emp.user_partner_id.id not in partners:
                partners.append(emp.user_partner_id.id)
        self.message_subscribe(partner_ids=partners)

        if 'meeting_date_assesment' in vals:
            meeting_date = vals['meeting_date_assesment']
            meeting_date = meeting_date  or self.meeting_date_assesment
            meeting_date = datetime.datetime.strptime(meeting_date, DEFAULT_SERVER_DATETIME_FORMAT)
            if self.meeting_id:
                self.meeting_id.write({
                    'start': meeting_date,
                    'stop': meeting_date+datetime.timedelta(hours=2),
                })
            else:
                self.create_meeting(meeting_date, partners)
                self.message_post(body='Evaluation Meeting Created')
        return super(EvaluationModel, self).write(vals)

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values:
            rec = self.track(self, self.state)
            if rec:
                return rec
        return super(EvaluationModel, self)._track_subtype(init_values)

class  ISORecommedation(models.Model, CreateActivityMix):

    _name = 'iso.system.recommedation'
    _description = 'Recommendation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_iso_users(self):
        #SEARCH MODE
        groups = []
        groups.extend(self.env['res.groups'].search(
            [('id', '=', self.env.ref('iso_system.group_iso_quality_manager').id)]).ids)
        groups.extend(self.env['res.groups'].search(
            [('id', '=', self.env.ref('iso_system.group_iso_compliance_manager').id)]).ids)
        groups.extend(self.env['res.groups'].search(
            [('id', '=', self.env.ref('iso_system.group_iso_executive_board').id)]).ids)
        users = self.env['res.users'].search([('groups_id','in',groups)]).ids
        return [('id','in', users)]

    req_eval = fields.Many2one('iso.non.conformity.request')
    name = fields.Char(string='NCR Ref.', related='req_eval.name', readonly=True)
    non_conformity_type = fields.Many2one('iso.non.conformity.type', related='req_eval.non_conformity_type', string='Type', required=True)
    department = fields.Many2one('hr.department',related='req_eval.department', required=True, readonly=True)
    completion_date = fields.Datetime(required=True, related='req_eval.completion_date', readonly=True)
    company_id = fields.Many2one('res.company',related='req_eval.company_id', required=True, readonly=True)
    updated_document_url = fields.Char()
    meeting_date_assesment = fields.Datetime()
    meeeting_attendees = fields.Many2many('res.users', domain=_get_iso_users, string='Meeting Attendees')
    minutes_of_meeting = fields.Text(tracking=True)
    executive_board = fields.Text(tracking=True)
    implementation_date = fields.Date(copy=False, readonly=True)
    logged_in_user = fields.Char(compute='_compute_logged_in_user_group')
    state = fields.Selection(
        [('quality_mgr', 'Quality MGR'), ('compilance_mgr', 'Compliance MGR'),
         ('executive_board', 'Executive Board'), ('implement', 'Implement'), ('cancelled', 'Cancelled')],
        tracking=True, string='Status', default='quality_mgr')

    def _compute_logged_in_user_group(self):
        
        if self.env.user.has_group('iso_system.group_iso_compliance_manager'):
            self.logged_in_user = 'compliance_manager'
        elif self.env.user.has_group('iso_system.group_iso_executive_board'):
            self.logged_in_user = 'executive_board'
        else:
            self.logged_in_user = None

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
        self.write({'state': 'implement', 'implementation_date': datetime.date.today()})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
    def action_set_draft(self):
        self.write({'state':'quality_mgr'})

    def create_creative_action(self):
        self.env['iso.system.corrective.action'].sudo().create({'ncr_ref': self.req_eval.id, 'implementation_date': self.implementation_date})

    @api.model
    def create(self, vals):
        res = super(ISORecommedation, self).create(vals)
        #if 'state' in vals and  vals['state'] == 'quality_mgr':
        self.create_activity(res.env, res._name, res.id, res.department.id, 'quality_manager',
                             sum='Quality Manager')
          
       
        return res

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values:
            rec = self.track(self, self.state)
            if rec:
                return rec
        return super(ISORecommedation, self)._track_subtype(init_values)


class  ISOConcessionsRequest(models.Model, CreateActivityMix):

    _name = 'iso.system.concessions.request'
    _description = 'Concessions Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    def _get_iso_users(self):
        #SEARCH MODE
        return []

    name = fields.Char(string='CSR Ref.', readonly=True)
    non_conformity_type = fields.Many2one('iso.concessions.type', string='Type', required=True)
    department = fields.Many2one('hr.department', required=True)
    completion_date = fields.Datetime(required=True)
    company_id = fields.Many2one('res.company', required=True)

    team_lead = fields.Many2one('res.users', compute='_compute_approver')
    description = fields.Text(required=True, tracking=True)
    logged_in_user = fields.Boolean(compute='_compute_logged_in_user_group')
    logged_in_user_prj = fields.Boolean(compute='_compute_logged_in_user_group')
    logged_in_user_qlty = fields.Boolean(compute='_compute_logged_in_user_group')
    logged_in_user_comp = fields.Boolean(compute='_compute_logged_in_user_group')
    logged_in_user_exec = fields.Boolean(compute='_compute_logged_in_user_group')

    team_lead_comments = fields.Text(tracking=True)
    project_manager_comments = fields.Text(tracking=True)
    quality_manager_comments = fields.Text(tracking=True)
    compliance_manager_comments = fields.Text(tracking=True)
    executive_board_comments = fields.Text(tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'),('team_lead', 'Team Lead'),('project_mgr', 'Project MGR'), ('quality_mgr', 'Quality MGR'), ('compilance_mgr', 'Compliance MGR'),
         ('executive_board', 'Executive Board'), ('granted', 'Granted'), ('cancelled', 'Cancelled')],
        tracking=True, string='Status', default='draft')

    def _compute_logged_in_user_group(self):
        self.logged_in_user = False
        self.logged_in_user_prj =  False
        self.logged_in_user_qlty = False
        self.logged_in_user_comp = False
        self.logged_in_user_exec = False
        if self.env.user.has_group('iso_system.group_iso_team_lead'):
            self.logged_in_user = True
        if self.env.user.has_group('iso_system.group_iso_project_manager'):
            self.logged_in_user_prj =  True
        if self.env.user.has_group('iso_system.group_iso_quality_manager'):
            self.logged_in_user_qlty = True
        if self.env.user.has_group('iso_system.group_iso_compliance_manager'):
            self.logged_in_user_comp = True
        if self.env.user.has_group('iso_system.group_iso_executive_board'):
            self.logged_in_user_exec = True
        
    
    def subscribe_users(self):
        self.message_subscribe(partner_ids=self.env.user.mapped('partner_id').ids)

    def action_submit(self):
        self.subscribe_users()
        self.create_activity(self.env, self._name, self.id,self.department.id,'team_lead',sum='Team Lead' )
        self.write({'state': 'team_lead'})

    def action_approve_team_lead(self):
        self.subscribe_users()
        self.create_activity(self.env, self._name, self.id, self.department.id, 'project_manager', sum='Project Manager')
        self.write({'state':'project_mgr'})

    def action_approve_project_mgr(self):
        self.subscribe_users()
        self.create_activity(self.env, self._name, self.id, self.department.id, 'quality_manager',
                             sum='Quality Manager')
        self.write({'state': 'quality_mgr'})

    @api.depends('department')
    def _compute_approver(self):
        for rec in self:
            approver = self.env['iso.approver'].sudo().search([('department', '=', rec.department.id)], limit=1)
            if approver:
                rec.team_lead = approver.team_lead
            else:
                rec.team_lead = None

    def action_approve_quality_mgr(self):
        self.create_activity(self.env, self._name, self.id, self.department.id, 'compliance_manager',
                             sum='Compliance Manager')
        self.write({'state': 'compilance_mgr'})

    def action_approve_compilance_mgr(self):
        self.create_activity(self.env, self._name, self.id, self.department.id, 'executive_board',
                             sum='Executive Board')
        self.write({'state': 'executive_board'})

    def action_executive_board(self):
        self.create_creative_action()
        self.write({'state': 'granted'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
    def action_set_draft(self):
        self.write({'state':'draft'})

    def create_creative_action(self):
        pass

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence']. \
            next_by_code('iso.system.concessions.request')
        return super(ISOConcessionsRequest, self).create(vals)

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values:
            rec = self.track(self, self.state)
            if rec:
                return rec
        return super(ISOConcessionsRequest, self)._track_subtype(init_values)
