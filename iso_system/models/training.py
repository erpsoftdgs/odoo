import datetime
from odoo import models, fields, api, _

class  ISOSystemTraining(models.Model):

    _name = 'iso.system.training'
    _description = 'Training'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string='Training Ref.', readonly=True)
    non_conformity_type = fields.Many2one('iso.non.conformity.type', string='Type', required=True)
    department = fields.Many2one('hr.department', required=True)
    completion_date = fields.Datetime(required=True)
    company_id = fields.Many2one('res.company', required=True)
    training_date = fields.Datetime(required=True)
    employees = fields.Many2many('hr.employee')
    meeting_id = fields.Many2one('calendar.event', copy=False)
    trainer_topic = fields.Char()
    process_doc_one = fields.Char()
    process_doc_two = fields.Char()
    trainer = fields.Many2one('res.users')
    trainer_notes = fields.Text(tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'),('scheduled', 'Scheduled'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
        tracking=True, string='Status', default='draft')

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

    def create_meeting(self, partners, begin, end):

        for res in self:

            cal = self.env['calendar.event'].sudo().create(
                {
                    'name': '%s Training Event' % (res.name),
                    'partner_ids': [(6, 0, partners)],
                    'stop':   end,
                    'start': begin,
                    'duration': 2,
                    'alarm_ids': [(6,0,[self.env.ref('calendar.alarm_notif_1').id])]
                }
            )
            res.write({'meeting_id': cal.id})


    def action_schedule(self):
        #self.create_activity(self.env, self._name, self.id, self.department.id, 'project_manager',
        #                     sum='Project Manager')

        self.write({'state':'scheduled'})

    def action_done(self):
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_set_draft(self):
        self.write({'state': 'draft'})
    def get_emp_partners(self):
        partners = []
        for emp in self.employees:
            if emp.user_partner_id.id and emp.user_partner_id.id not in partners:
                partners.append(emp.user_partner_id.id)
        return partners

    def create_employee_followers(self, vals):
        partners = self.get_emp_partners()
        if 'employees' in vals:
            emp_ids = vals['employees'][0][2]
            employee_ids = self.env['hr.employee'].sudo().search([('id', 'in', emp_ids)])
            partners.extend([emp.user_partner_id.id for emp in employee_ids if emp.user_partner_id.id  and emp.user_partner_id.id not in partners])
            self.message_subscribe(partner_ids=partners)

        s_d = vals.get('training_date') or self.training_date
        com_d = vals.get('completion_date') or self.completion_date
        if self.meeting_id and com_d and s_d:
                self.meeting_id.write({
                    'start': s_d,
                    'stop': com_d,
                    'partner_ids': [(6, 0, partners)],
                })
        elif (vals.get('state') == 'scheduled' or self.state == 'scheduled') and not self.meeting_id:
                self.create_meeting(partners, s_d, com_d)
                self.message_post(body='Training Event Created')


    @api.model_create_multi
    def create(self, vals_list):
        vals['name'] = self.env['ir.sequence']. \
            next_by_code('iso.system.training')
        res = super(ISOSystemTraining, self).create(vals_list)
        #self.create_activity(res.env, res._name, res.id,res.department.id,'team_lead',sum='Team Lead' )
        res.create_employee_followers(vals_list)
        return res

    def write(self, vals):
        res = super(ISOSystemTraining, self).write(vals)
        self.create_employee_followers(vals)
        return res
