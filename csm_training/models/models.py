import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    client_training = fields.Boolean(related='team_id.client_training')

    def new_client_training(self):
        # seq = self.env['ir.sequence'].next_by_code('csm.requirements')
        # req.message_post(body='New business requirement %s has been created' % (req.name))
        view = self.env.ref('csm_training.csm_training_form')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Client Training'),
            'res_model': 'csm.client.training',
            'views': [(view.id, 'form')],
            'view_mode': 'form',
        }


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    client_training = fields.Boolean()


class CancellationWizard(models.TransientModel):
    _name = 'client.training.cancel'
    message = fields.Char()
    training_id = fields.Many2one('csm.client.training', required=True)

    def cancel_training(self):
        self.training_id.write({'state': 'cancelled'})
        self.training_id.message_post(body='Cancellation reason : %s' % (self.message))
        return {'type': 'ir.actions.act_window_close'}


class ClientTraining(models.Model):
    _name = 'csm.client.training'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'CSM Client Training'

    def _get_deparments(self):
        depart_ids = self.env['csm.approvers'].sudo().search([]).mapped('department').ids
        return [('id', 'in', depart_ids)]

    name = fields.Char('Reference', required=True, index=True, copy=False, default='New', readonly=True, tracking=True)
    department_id = fields.Many2one('hr.department', domain=_get_deparments, required=True)
    team_lead_id = fields.Many2one('res.users', compute='_compute_approvers', readonly=True)
    project_manager_id = fields.Many2one('res.users', compute='_compute_approvers', readonly=True)
    pmo_officer = fields.Many2one('res.users', default=lambda r: r.env.user)
    module = fields.Char()
    training_content = fields.Text()
    client_id = fields.Many2one('res.partner', required=True, string='Client Name', domain=[('is_company', '=', True)])
    attendees_ids = fields.Many2many('res.partner', required=True)

    training_system = fields.Char()
    trainer = fields.Many2one('hr.employee')
    training_date = fields.Datetime()
    duration = fields.Float('Duration (hrs)')
    attendees_report_ids = fields.One2many('csm.training.report', 'training_id')
    state = fields.Selection([('new', 'New'),
                              ('team_lead', 'Team Lead'),
                              ('pmo', 'PMO'),
                              ('account_manager', 'Account Manager'),
                              ('confirmed', 'Confirmed'),
                              ('scheduled', 'Scheduled'),
                              ('done', 'Done'),
                              ('cancelled', 'Cancelled')
                              ], default='new', string='Status', copy=False, readonly=True, index=True, tracking=True)

    def push_for_review(self):
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env.ref('csm_training.model_csm_client_training').id,
            'res_id': self.id,
            'user_id': self.team_lead_id.id,
            'activity_type_id': self.env.ref("csm_requirements.mail_activity_new_csm_requirement").id,
            'date_deadline': datetime.datetime.now() + datetime.timedelta(days=0),
            'summary': 'Verify and confirm this training schedule'
        })
        return self.write({'state': 'team_lead'})

    def verify(self):
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env.ref('csm_training.model_csm_client_training').id,
            'res_id': self.id,
            'user_id': self.pmo_officer.id,
            'activity_type_id': self.env.ref("csm_requirements.mail_activity_new_csm_requirement").id,
            'date_deadline': datetime.datetime.now() + datetime.timedelta(days=1),
            'summary': 'Confirm the schedule with client'
        })
        self.message_post(body='Verified by %s' % (self.pmo_officer.name))
        return self.write({'state': 'pmo'})

    def confirm_with_client(self):
        for sum in ['Create and send out meeting invites', 'Create and send out training brochure (if it applies)']:
            self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('csm_training.model_csm_client_training').id,
                'res_id': self.id,
                'user_id': self.pmo_officer.id,
                'activity_type_id': self.env.ref("csm_requirements.mail_activity_new_csm_requirement").id,
                'date_deadline': datetime.datetime.now() + datetime.timedelta(days=1),
                'summary': sum
            })
        return self.write({'state': 'account_manager'})

    def approve_by_account_manager(self):
        self.env['mail.activity'].sudo().create({
            'res_model_id': self.env.ref('csm_training.model_csm_client_training').id,
            'res_id': self.id,
            'user_id': self.pmo_officer.id,
            'activity_type_id': self.env.ref("csm_requirements.mail_activity_new_csm_requirement").id,
            'date_deadline': datetime.datetime.now() + datetime.timedelta(days=1),
            'summary': 'Account manager approved the schedule with client'
        })
        self.message_post(body='Approved by %s' % (self.env.user.name))
        return self.write({'state': 'confirmed'})

    def schedule(self):
        if not self.trainer.user_id:
            raise UserError(_('Please set the related user on the trainer employee record!'))
        for sum in ['Confirm training system and ehelp platform has been sent to client',
                    'Send out ehelp login details']:
            self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('csm_training.model_csm_client_training').id,
                'res_id': self.id,
                'user_id': self.trainer.user_id.id,
                'activity_type_id': self.env.ref("csm_requirements.mail_activity_new_csm_requirement").id,
                'date_deadline': datetime.datetime.now() + datetime.timedelta(days=1),
                'summary': sum
            })
        return self.write({'state': 'scheduled'})

    def mark_as_done(self):
        report_attendess = self.attendees_report_ids.mapped('attendee_id')
        missng_attendess = (report_attendess - self.attendees_ids)
        if not self.attendees_report_ids.ids:
            raise UserError(_('Please fill the training report for attendees to progress'))
        for record in self.attendees_report_ids.mapped('next_step'):
            activity_type = self.env['mail.activity.type'].search([('name', '=', record.name)],
                                                                  limit=1)
            if not activity_type:
                continue
            self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('csm_training.model_csm_client_training').id,
                'res_id': self.id,
                'user_id': self.trainer.user_id.id,
                'activity_type_id': activity_type.id,
                'date_deadline': datetime.datetime.now(),
                'summary': record.name
            })
        return self.write({'state': 'done'})

    def cancel(self):
        cancel_id = self.env['client.training.cancel'].create({'training_id': self.id})

        view = self.env.ref('csm_training.csm_training_cancel_form')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cancellation Reason'),
            'res_model': 'client.training.cancel',
            'res_id': cancel_id.id,
            'views': [(view.id, 'form')],
            'view_mode': 'form',
            'target': 'new'
        }

    @api.onchange('client_id')
    def _onchange_client_name(self):
        partner_ids = self.env['res.partner'].search([('parent_id', '=', self.client_id.id)]).ids
        return {'domain': {'attendees_ids': [('id', 'in', partner_ids)],
                           'attendees_report_ids.attendee_id': [('id', 'in', partner_ids)]}}

    @api.depends('department_id')
    def _compute_approvers(self):
        for rec in self:
            rec.team_lead_id = False
            rec.project_manager_id = False
            if rec.department_id:

                approver = self.env['csm.approvers'].sudo().search([('department', '=', rec.department_id.id)], limit=1)
                if approver:
                    rec.team_lead_id = approver.team_lead_id
                    rec.project_manager_id = approver.project_manager_id

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('csm.client.training') or '/'
        return super(ClientTraining, self).create(vals)


class CSMTrainingReport(models.Model):
    _name = 'csm.training.report'

    training_id = fields.Many2one('csm.client.training', index=True, ondelete='cascade', required=True)

    attendee_id = fields.Many2one('res.partner', required=True)
    feedback = fields.Text()
    next_step = fields.Many2one('next.step')

    @api.onchange('attendee_id')
    def _onchange_attendee_id(self):
        partner_ids = self.env['res.partner'].search([('parent_id', '=', self.training_id.client_id.id)]).ids
        return {'domain': {'attendee_id': [('id', 'in', partner_ids)]}}
