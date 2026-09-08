import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    requirement_id = fields.Many2one('csm.requirements')
    new_business_tracker = fields.Boolean(related='team_id.new_business_tracker')

    def new_business_requirements(self):
        # seq = self.env['ir.sequence'].next_by_code('csm.requirements')
        # req.message_post(body='New business requirement %s has been created' % (req.name))
        view = self.env.ref('csm_requirements.csm_requirement_form')
        return {
            'type': 'ir.actions.act_window',
            'name': _('CSM Requirements'),
            'res_model': 'csm.requirements',
            'views': [(view.id, 'form')],
            'view_mode': 'form',
        }


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    new_business_tracker = fields.Boolean()


class GenerateTicket(models.TransientModel):
    _name = 'generate.helpdesk.ticket'
    _description = 'Create new ticket'

    team = fields.Many2one("helpdesk.team")
    name = fields.Char(string='Title')
    summary = fields.Char()

    odoo_supported_versions = fields.Selection(
        [('11', 'Odoo 11'), ('12', 'Odoo 12'), ('13', 'Odoo 13'), ('14', 'Odoo 14'), ('15', 'Odoo 15')], default='15')

    csm_requirement_id = fields.Many2one('csm.requirements')

    def new_business_requirements(self):
        self.env['helpdesk.ticket'].create({'name': self.name, 'team_id': self.team.id, 'summary': self.summary,
                                            'odoo_supported_version': self.odoo_supported_versions,
                                            'requirement_id': self.csm_requirement_id.id})
        return {'type': 'ir.actions.act_window_close'}


class CSMApprovers(models.Model):
    _name = 'csm.approvers'
    _description = 'CSM Approvers'

    department = fields.Many2one('hr.department', required=True)
    team_lead_id = fields.Many2one('res.users')
    cx_manager_id = fields.Many2one('res.users')
    project_manager_id = fields.Many2one('res.users')
    account_manager_id = fields.Many2one('res.users')


class CSMRequirements(models.Model):
    _name = 'csm.requirements'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'CSM Requirement'

    def _get_deparments(self):
        depart_ids = self.env['csm.approvers'].sudo().search([]).mapped('department').ids
        return [('id', 'in', depart_ids)]

    ticket_id = fields.Many2one('helpdesk.ticket')
    reason = fields.Selection([('change', 'Client Rejected Change'),
                               ('notpay', 'Client does not want to pay'),
                               ('progress', 'Client does not want to progress')],
                              track_visibility='onchange', tracking=True, string="Title Cancellation Reason")

    name = fields.Char('Reference', readonly=True, required=True, index=True, copy=False, default='New')
    title = fields.Char(required=True,
                        states={'account_manager': [('readonly', True)], 'approved_for_build': [('readonly', True)],
                                'approved_for_production': [('readonly', True)], 'done': [('readonly', True)]})
    client_id = fields.Many2one('res.partner', required=True, string='Client Name', domain=[('is_company', '=', True)],
                                states={'account_manager': [('readonly', True)],
                                        'approved_for_build': [('readonly', True)],
                                        'approved_for_production': [('readonly', True)], 'done': [('readonly', True)]}
                                )
    requirement_date = fields.Date(required=True, states={'account_manager': [('readonly', True)],
                                                          'approved_for_build': [('readonly', True)],
                                                          'approved_for_production': [('readonly', True)],
                                                          'done': [('readonly', True)]})

    requirement_owner_id = fields.Many2one('res.partner', required=True,
                                           domain="[('parent_id', '=', client_id), ('is_company', '=', False)]",
                                           states={'account_manager': [('readonly', True)],
                                                   'approved_for_build': [('readonly', True)],
                                                   'approved_for_production': [('readonly', True)],
                                                   'done': [('readonly', True)]})
    client_project_manager = fields.Many2one('res.partner', required=True,
                                             states={'account_manager': [('readonly', True)],
                                                     'approved_for_build': [('readonly', True)],
                                                     'approved_for_production': [('readonly', True)],
                                                     'done': [('readonly', True)]})
    logged_by = fields.Many2one('res.users', default=lambda r: r.env.user, readonly=True)
    requirement_document = fields.Char(required=True, states={'account_manager': [('readonly', True)],
                                                              'approved_for_build': [('readonly', True)],
                                                              'approved_for_production': [('readonly', True)],
                                                              'done': [('readonly', True)]})
    department_id = fields.Many2one('hr.department', domain=_get_deparments, required=True,
                                    states={'account_manager': [('readonly', True)],
                                            'approved_for_build': [('readonly', True)],
                                            'approved_for_production': [('readonly', True)],
                                            'done': [('readonly', True)]})
    team_lead_id = fields.Many2one('res.users', compute='_compute_approvers', readonly=True)
    project_manager_id = fields.Many2one('res.users', compute='_compute_approvers', readonly=True)
    account_manager_id = fields.Many2one('res.users', compute='_compute_approvers', readonly=True)
    specification_count = fields.Integer(compute='_compute_get_spec', readonly=True)
    specification_ids = fields.Many2many("helpdesk.ticket", string='Tickets', compute="_compute_get_spec",
                                         readonly=True, copy=False)
    responsible = fields.Many2one('res.users', states={'account_manager': [('readonly', True)],
                                                       'approved_for_build': [('readonly', True)],
                                                       'approved_for_production': [('readonly', True)],
                                                       'done': [('readonly', True)]})
    req_approved_by = fields.Many2one('res.users', readonly=True)
    prod_approved_by = fields.Many2one('res.users', readonly=True)
    req_approval_date = fields.Datetime(readonly=True)
    prod_approval_date = fields.Datetime(readonly=True)
    activity = fields.Selection([('spec_document', 'Specification Document'),
                                 ('dev_build', 'Dev Build'),
                                 ('testing', 'Testing'),
                                 ('data_conv', 'Data Conversions'),
                                 ('training', 'Training'),

                                 ], states={'account_manager': [('readonly', True)],
                                            'approved_for_build': [('readonly', True)],
                                            'approved_for_production': [('readonly', True)],
                                            'done': [('readonly', True)]})
    estimated_duration = fields.Float('Estimated Duration (hrs) ', states={'account_manager': [('readonly', True)],
                                                                           'approved_for_build': [('readonly', True)],
                                                                           'approved_for_production': [
                                                                               ('readonly', True)],
                                                                           'done': [('readonly', True)]})
    state = fields.Selection([('new', 'New'),
                              ('team_lead', 'Team Lead'),
                              ('awaiting_client_approval', 'Awaiting Client Approval'),
                              ('reviewed', 'Reviewed'),
                              ('project_manager', 'Project Manager'),
                              ('account_manager', 'Account Manager'),
                              ('approved_for_build', 'Approved For Build'),
                              ('approved_for_production', 'Approved For Production'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')
                              ], default='new', string='Status', copy=False, readonly=True, index=True, tracking=True)

    uat_delivery_date = fields.Date(string='UAT Delivery Date', tracking=True)
    production_delivery_date = fields.Date(string='Production Delivery Date', tracking=True)
    build_complexity = fields.Selection([
        ('low', 'Low (1 - 3 days)'),
        ('medium', 'Medium (7 - 14 Days)'),
        ('high', 'High (14 - 28 days)'),
        ('very', 'Very High ( 42 Days +)')
    ], string='Build Complexity', tracking=True)

    def action_get_specification_tree_view(self):
        specs = self.mapped('specification_ids')
        action = {
            'name': 'Helpdesk Ticket',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'helpdesk.ticket',
            'domain': "[('id', 'in', " + str(specs.ids) + ")]",
            'context': {},

        }
        return action

    def cancel_button(self):
        view_id = self.env.ref('csm_requirements.view_cancel_reason_form')
        return {
            'name': ('Cancellation Reason'),
            'domain': [('cancel_id', '=', self.id), ],
            'type': 'ir.actions.act_window',
            'res_model': 'cancel.reason',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id.id,
            'target': 'new',
        }

    def _compute_get_spec(self):
        for rec in self:
            reqs = self.env['helpdesk.ticket'].search([('requirement_id', '=', rec.id)])
            rec.specification_ids = reqs
            rec.specification_count = len(reqs.ids)

    # def submit(self):
    #     self.env['mail.activity'].sudo().create({
    #         'res_model_id': self.env.ref('csm_requirements.model_csm_requirements').id,
    #         'res_id': self.id,
    #         'user_id': self.id,
    #         'activity_type_id': self.env.ref("csm_requirements.mail_activity_new_csm_requirement").id,
    #         'date_deadline': datetime.datetime.now() + datetime.timedelta(days=1),
    #         'summary': 'Review my document'
    #     })
    #     return self.write({'state': 'team_lead'})

    def submit(self):
        self.ensure_one()

        if not self.team_lead_id:
            raise UserError(_("No Team Lead configured for this department."))

        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env.ref('csm_requirements.model_csm_requirements').id,
            'res_id': self.id,
            'user_id': self.team_lead_id.id,
            'activity_type_id': self.env.ref(
                "csm_requirements.mail_activity_new_csm_requirement"
            ).id,
            'date_deadline': fields.Date.today() + datetime.timedelta(days=1),
            'summary': 'Review my document'
        })

        return self.write({'state': 'team_lead'})

    def review(self):
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env.ref('csm_requirements.model_csm_requirements').id,
            'res_id': self.id,
            'user_id': self.logged_by.id,
            'activity_type_id': self.env.ref("csm_requirements.mail_activity_update_csm_requirement").id,
            'summary': 'Update new requirement document',
            'date_deadline': datetime.datetime.now() + datetime.timedelta(days=1),
        })
        self.message_post(body=_('Reviewed by %s') % (self.team_lead_id.name))
        # return self.write({'state': 'team_lead'})

    def resubmit(self):
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env.ref('csm_requirements.model_csm_requirements').id,
            'res_id': self.id,
            'user_id': self.team_lead_id.id,
            'activity_type_id': self.env.ref("csm_requirements.mail_activity_review_update_csm_requirement").id,
            'summary': 'Review updated requirement document',
            'date_deadline': datetime.datetime.now() + datetime.timedelta(days=1),

        })
        self.message_post(body=_('Resubmitted by %s') % (self.logged_by.name))

    def push_for_client_review(self):
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env.ref('csm_requirements.model_csm_requirements').id,
            'res_id': self.id,
            'user_id': self.logged_by.id,
            'activity_type_id': self.env.ref("csm_requirements.mail_activity_send_csm_requirement").id,
            'summary': 'Send new business requirement document to client in PDF',
            'date_deadline': datetime.datetime.now() + datetime.timedelta(days=1),
        })
        return self.write({'state': 'awaiting_client_approval'})

    def requirement_approved(self):
        if not self.responsible or not self.activity or not self.estimated_duration:
            raise UserError(_('You need to state the effort required for this requirement'))

        # if not self.req_approved_by or not self.req_approval_date:
        #     raise UserError(_('Fill the requirements approval section to progress'))
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env.ref('csm_requirements.model_csm_requirements').id,
            'res_id': self.id,
            'user_id': self.project_manager_id.id,
            'activity_type_id': self.env.ref("csm_requirements.mail_activity_updated_epic").id,
            'summary': 'Update EPIC',
            'date_deadline': datetime.datetime.now() + datetime.timedelta(days=1),

        })
        return self.write({'req_approved_by': self.env.user.id, 'req_approval_date': datetime.date.today(),
                           'state': 'project_manager'})

    def epic_updated(self):
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env.ref('csm_requirements.model_csm_requirements').id,
            'res_id': self.id,
            'user_id': self.account_manager_id.id,
            'activity_type_id': self.env.ref("csm_requirements.mail_activity_account_manager_required").id,
            'summary': 'Account manager approval required to proceed',
            'date_deadline': datetime.datetime.now() + datetime.timedelta(days=3),
        })
        return self.write({'state': 'account_manager'})

    def approved_for_build(self):

        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env.ref('csm_requirements.model_csm_requirements').id,
            'res_id': self.id,
            'user_id': self.logged_by.id,
            'activity_type_id': self.env.ref("csm_requirements.mail_activity_build_create_ticket").id,
            'summary': 'Approved for build',
            'date_deadline': datetime.datetime.now() + datetime.timedelta(days=1),
        })
        return self.write({'state': 'approved_for_build'})

    def create_ticket(self):
        view = self.env.ref('csm_requirements.csm_requirement_ticket_form')
        res = self.env['generate.helpdesk.ticket'].create({'csm_requirement_id': self.id})
        return {
            'name': _('Create Ticket'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'generate.helpdesk.ticket',
            'res_id': res.id,
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new'
        }

    def client_signoff_review(self):
        # if not self.prod_approved_by or not self.prod_approval_date:
        #     raise UserError(_('Fill the production approval section to progress'))
        return self.write({'state': 'approved_for_production', 'prod_approved_by': self.env.user.id,
                           'prod_approval_date': datetime.date.today()})

    def mark_as_done(self):
        return self.write({'state': 'done'})

    @api.depends('department_id')
    def _compute_approvers(self):
        for rec in self:
            rec.team_lead_id = False
            rec.project_manager_id = False
            rec.account_manager_id = False
            if rec.department_id:

                approver = self.env['csm.approvers'].sudo().search([('department', '=', rec.department_id.id)], limit=1)
                if approver:
                    rec.team_lead_id = approver.team_lead_id
                    rec.project_manager_id = approver.project_manager_id
                    rec.account_manager_id = approver.account_manager_id

    @api.onchange('client_id')
    def _onchange_client_name(self):
        partner_ids = self.env['res.partner'].search([('parent_id', '=', self.client_id.id)]).ids
        return {'domain': {'requirement_owner_id': [('id', 'in', partner_ids)]}, }

    @api.onchange('client_id')
    def _onchange_client_id(self):
        """Clear requirement owner when client changes and update domain"""
        if self.client_id:
            # Clear requirement owner when client changes
            self.requirement_owner_id = False
            # Return domain to show only contacts from selected company
            return {
                'domain': {
                    'requirement_owner_id': [
                        ('parent_id', '=', self.client_id.id),
                        ('is_company', '=', False)
                    ]
                }
            }
        else:
            self.requirement_owner_id = False
            return {
                'domain': {
                    'requirement_owner_id': [('id', '=', False)]
                }
            }

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('csm.requirements') or '/'
        return super(CSMRequirements, self).create(vals)

class CsmOnboardingConfig(models.Model):
    _name = 'csm.onboarding.config'
    _description = 'CSM Onboarding Configuration'

    name = fields.Char(string='Task', required=True)
    description = fields.Char(string='Description')
    email_template_id = fields.Many2one('mail.template', string='Email Template',
                                        domain="[('model', '=', 'csm.onboarding')]")

class CsmOnboarding(models.Model):
    _name = 'csm.onboarding'
    _description = 'CSM Onboarding'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # For chatter and audit trail
    _rec_name = 'reference'

    # reference = fields.Char(string='Reference',readonly=True, required=True, index=True, copy=False, default='New')
    reference = fields.Char(
        string='Reference',
        copy=False,
        readonly=True,
        default=False,  # Remove the lambda to avoid repeated calls
    )
    client_id = fields.Many2one('res.partner', string='Client Name',
                                domain="[('is_company', '=', True)]", required=True,
                                tracking=True)
    onboarding_date = fields.Date(string='Onboarding Date', required=True, tracking=True)
    client_pm_id = fields.Many2one('res.partner', string='Client Project Manager',
                                   domain="[('parent_id', '=', client_id), ('is_company', '=', False)]",
                                   required=True, tracking=True)
    odoo_pm_id = fields.Many2one('res.partner', string='Odoo Account Manager',
                                 domain="[('is_company', '=', False)]", required=True, tracking=True)
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='new', tracking=True)
    task_ids = fields.One2many('csm.onboarding.line', 'onboarding_id', string='Tasks')


    @api.model
    def create(self, vals):
        if not vals.get('reference'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('csm.onboarding') or '/'
        return super(CsmOnboarding, self).create(vals)

    def action_approve(self):
        self.ensure_one()
        if self.state == 'new':
            self.state = 'in_progress'

    def action_complete(self):
        self.ensure_one()
        if self.state == 'in_progress':
            if all(line.completed for line in self.task_ids):
                self.state = 'completed'
            else:
                raise ValidationError(_("All tasks must be completed before moving to Completed status."))

    def action_cancel(self):
        self.ensure_one()
        if self.state in ('new', 'in_progress'):
            self.state = 'cancelled'

class CsmOnboardingLine(models.Model):
    _name = 'csm.onboarding.line'
    _description = 'CSM Onboarding Line'

    onboarding_id = fields.Many2one('csm.onboarding', required=True)
    config_id = fields.Many2one('csm.onboarding.config', string='Task', required=True)
    description = fields.Char(string='Description', related='config_id.description', store=True)
    completed = fields.Boolean(string='Completed', tracking=True)
    comments = fields.Char(string='Comments')

    def send_email(self):
        self.ensure_one()
        if not self.config_id.email_template_id:
            raise UserError(_("No email template configured for this task."))

        template_id = self.config_id.email_template_id.id
        ctx = {
            'default_model': 'csm.onboarding',
            'default_res_ids': [self.onboarding_id.id], # <--- FIX: Pass a list of IDs
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'email_to': self.onboarding_id.client_pm_id.email or '',
            'email_cc': self.onboarding_id.client_id.email or '',
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
    def write(self, vals):
        res = super().write(vals)
        if 'completed' in vals and vals['completed']:
            self.onboarding_id.message_post(body=_("Task %s completed at %s.") % (self.config_id.name, fields.Datetime.now()))
        return res
