from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class CsmMeeting(models.Model):
    _name = 'csm.meeting'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "CSM Meeting Module"
    _rec_name = 'ref'

    # @api.model
    # def _get_default_name(self):
    #     return self.env['ir.sequence'].next_by_code('csm.meeting')

    ref = fields.Char(string='Reference', size=32, required=True, default='New',
                      track_visibility='onchange', readonly=True)
    client_name = fields.Many2one('production.access.system', string='Client Name')
    meeting_date = fields.Datetime(string='Meeting Date')
    duration = fields.Float(string='Duration')
    stop = fields.Datetime('Stop', compute='_compute_duration', required=True,
                           help="Stop date of an event, without time for full days events")
    organiser = fields.Many2one('res.users', string='Organizer')
    attendees = fields.Many2many('res.partner', string='Attendees')
    location = fields.Selection([
        ('onsite', 'Onsite'),
        ('remote', 'Remote'),
    ], string="Location")
    state = fields.Selection([('new', 'NEW'),
                              ('schedule', 'SCHEDULE'),
                              ('done', 'DONE')], default='new', string='Status',
                             track_visibility='onchange', tracking=True)
    agenda = fields.Text(string='Agenda', track_visibility='onchange', tracking=True)
    action_points = fields.One2many('action.points', 'csm_meeting', string='Action Points')
    meeting_name = fields.Char(string='Meeting Name', compute='_compute_name')

    @api.depends('meeting_date', 'duration')
    def _compute_duration(self):
        if self.meeting_date:
            # Round the duration (in hours) to the minute to avoid weird situations where the event
            # stops at 4:19:59, later displayed as 4:19.
            self.stop = self.meeting_date + timedelta(minutes=round((self.duration or 1.0) * 60))

    @api.depends('client_name')
    def _compute_name(self):
        for rec in self:
            rec.meeting_name = str(rec.ref) + " - Meeting with " + str(rec.client_name)

    def done_button(self, act_type_xmlid='', date_deadline=None, summary='', note='', **act_values):
        Activity = self.env['mail.activity']
        ActivityType = self.env['mail.activity.type']
        IrModel = self.env['ir.model']

        if not date_deadline:
            date_deadline = fields.Date.context_today(self) + relativedelta(days=1)

        meeting_act_type = ActivityType.search([('name', '=', 'Confirm meeting notes')], limit=1)
        if not meeting_act_type:
            meeting_act_type = ActivityType.create({'name': 'Confirm meeting notes'})

        model = IrModel._get(self._name)
        activities = self.env['mail.activity']

        for record in self:
            # Create "Confirm meeting notes" activity
            Activity.create({
                'activity_type_id': meeting_act_type.id,
                'summary': 'Confirm meeting notes and action points with client',
                'automated': True,
                'note': note or meeting_act_type.default_note,
                'date_deadline': date_deadline,
                'res_model_id': model.id,
                'res_id': record.id,
                'user_id': record.organiser.id,
            })

            # Create activities for each action point
            for point in record.action_points:
                action_type = ActivityType.search([('name', '=', point.next_step.name)], limit=1)
                if not action_type:
                    continue  # Optionally handle this case

                create_vals = {
                    'activity_type_id': action_type.id,
                    'summary': summary or action_type.summary,
                    'automated': True,
                    'note': note or action_type.default_note,
                    'date_deadline': date_deadline,
                    'res_model_id': model.id,
                    'res_id': record.id,
                    'user_id': record.organiser.id,
                }
                create_vals.update(act_values)
                activities |= Activity.create(create_vals)

        self.write({'state': 'done'})
        return activities

    '''def done_button(self, act_type_xmlid='', date_deadline=None, summary='', note='', **act_values):
        if not date_deadline:
            date_deadline = fields.Date.context_today(self) + relativedelta(days=1)
        meeting_act_type = self.env['mail.activity.type'].search([('name', '=', 'Confirm meeting notes')], limit=1)
        if not meeting_act_type:
            self.env['mail.activity.type'].create({
                'name': 'Confirm meeting notes',
            })
        model_id = self.env['ir.model']._get(self._name).id
        for notes in self:
            self.env['mail.activity'].create({
                'activity_type_id': meeting_act_type.id,
                'summary': 'Confirm meeting notes and action points with client',
                'automated': True,
                'note': note or meeting_act_type.summary,
                'date_deadline': date_deadline,
                'res_model_id': model_id,
                'res_id': notes.id,
                'user_id': self.organiser.id
            })
        for record in self:
            #record.model_id = self.env['ir.model']._get(self._name).id
            activities = self.env['mail.activity']
            for rec in record.action_points:
                record.activity_type_id = self.env['mail.activity.type'].search([('name', '=', rec.next_step.name)],
                                                                             limit=1)
                record.create_vals = {
                    'activity_type_id': record.activity_type_id.id,
                    'summary': summary or record.activity_type_id.summary,
                    'automated': True,
                    'note': note or record.activity_type_id.summary,
                    'date_deadline': date_deadline,
                    'res_model_id': model_id,
                    'res_id': record.id,
                    'user_id': record.organiser.id
                }
                record.create_vals.update(act_values)
                activities |= self.env['mail.activity'].create(record.create_vals)
        self.write({'state': 'done'})
        return activities'''

    def schedule_button(self):
        if self.action_points:
            # view_id = self.env.ref('calendar.view_calendar_event_form').id
            user = self.env['res.partner'].search([('name', '=', self.organiser.name)])
            self.write({'state': 'schedule'})
            #
            for rec in self:
                self.env['calendar.event'].create({
                    'location': rec.location,
                    'description': rec.agenda,
                    'name': rec.meeting_name,
                    'start': rec.meeting_date,
                    'stop': rec.stop,
                    'partner_ids': rec.attendees.ids + user.ids
                })

            # for rec in self:
            #     return {
            #         'name': 'Create Meetings',
            #         'view_type': 'form',
            #         'view_mode': 'form',
            #         'views': [(view_id, 'form')],
            #         'res_model': 'calendar.event',
            #         'view_id': view_id,
            #         'type': 'ir.actions.act_window',
            #         'context': {
            #             'default_name': rec.meeting_name,
            #             'default_partner_ids': rec.attendees.ids + user.ids,
            #             'default_location': rec.location,
            #             'default_description': rec.agenda,
            #             'default_start': rec.meeting_date,
            #             'default_stop': rec.stop,
            #
            #         },
            #         'target': 'new',
            #     }
        else:
            raise UserError(_('Action Points line is empty'))

    @api.model
    def create(self, vals):
        if vals.get('ref', 'New') == 'New':
            vals['ref'] = self.env['ir.sequence'].next_by_code('csm.meeting') or 'New'
        return super(CsmMeeting, self).create(vals)

class NextStep(models.Model):
    _name = 'next.step'
    _description = "Next Step"

    name = fields.Char(string='Name')

    @api.model
    def create(self, vals):
        res = super(NextStep, self).create(vals)
        self.env['mail.activity.type'].create({
            'name': vals["name"],
        })
        return res


class MeetingType(models.Model):
    _name = 'meeting.type'
    _description = "Meeting Type"

    name = fields.Char(string='Name')


class ActionPoints(models.Model):
    _name = 'action.points'
    _description = "Action Point"

    type = fields.Many2one('meeting.type', string='Type')
    meeting_notes = fields.Text(string='Meeting Notes')
    next_step = fields.Many2one('next.step', string='Next Step')
    csm_meeting = fields.Many2one('csm.meeting', string='CSM Meeting')
