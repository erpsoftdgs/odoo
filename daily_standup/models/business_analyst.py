# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from odoo import models, fields, _, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BusinessAnalyst(models.Model):
    _name = 'business.analyst'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Business Analyst'
    _rec_name = "employee_name"

    active = fields.Boolean(default=True)
    creation_date = fields.Date(default=fields.Date.today)
    employee_name = fields.Many2one('hr.employee', default=lambda self: self.env.user.employee_id)
    department_id = fields.Many2one(
        'hr.department',
        string="Department",
        related="employee_name.department_id",
        store=True,
        readonly=True,
    )
    project_id = fields.Many2one('project.project', string="Project")
    task_id = fields.Many2one(
        'project.task',
        string="Task",
        domain="[('project_id', '=', project_id)]"
    )
    employee_tag_ids = fields.Many2many(
        'employee.tags',
        string="Employee Tags"
    )
    location = fields.Selection(
        [('office', 'Office'), ('home', 'Home')],
        default="office",
        tracking=True,
    )
    date = fields.Date(tracking=True, string="Work Date")
    percentage_completion = fields.Integer(tracking=True)
    escalation_key_id = fields.Many2one('escalation.key')
    priority_task_key_id = fields.Many2one('key.priority.task', string="Key Priority Task", required=True, tracking=True)
    time_estimation_key_id = fields.Many2one('time.escalation.key', string="Time Estimation Key", required=True)
    comments = fields.Text(string="Comments", required=True)
    completion_date = fields.Date(string="Completion Date", readonly=True, tracking=True)

    # ER 4.0 - 2.0.3: Task Type field, mandatory, dropdown from Configuration
    # > Task Type. Business-Analyst-only by virtue of living on this model.
    task_type_id = fields.Many2one(
        'task.type',
        string="Task Type",
        required=True,
        tracking=True,
    )

    @api.constrains('percentage_completion')
    def _check_percentage_completion_limit(self):
        for rec in self:
            if rec.percentage_completion and rec.percentage_completion > 100:
                raise UserError(_("Percentage Completion cannot exceed 100%."))
            if rec.percentage_completion and rec.percentage_completion < 0:
                raise UserError(_("Percentage Completion cannot be negative."))
    state = fields.Selection(
        [
            ('draft', 'To Approve'),
            ('approved', 'Approved'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
        default='draft',
        string="Status",
        tracking=True,
        copy=False
    )
    next_date = fields.Date()
    key_priority_color_code = fields.Integer(
        related="priority_task_key_id.color",
        string="Priority Color Code",
        store=True
    )
    key_priority_color = fields.Char(
        string="Priority",
        compute="_compute_key_priority_color",
        store=False
    )
    key_priority_color_block = fields.Html(string="Priority Color Block",
                                           compute="_compute_key_priority_color_block",
                                           sanitize=False)
    HEX_COLOR_MAP = {
            0: "#FFFFFF",
            1: "#FF0000",
            2: "#FFA500",
            3: "#FFFF00",
            4: "#00FFFF",
            5: "#800080",
            6: "#FFEBCD",
            7: "#008080",
            8: "#0000FF",
            9: "#E30B5D",
            10: "#008000",
            11: "#8F00FF",
        }

    @api.depends("key_priority_color_code")
    def _compute_key_priority_color_block(self):
        for rec in self:
            color_hex = self.HEX_COLOR_MAP.get(rec.key_priority_color_code, "#FFFFFF")
            rec.key_priority_color_block = f"""
                <div style="
                    background-color: {color_hex};
                    width: 100px;
                    height: 100px;
                    border-radius: 10px;
                    border: 1px solid #000;">
                </div>
            """
    COLOR_MAP = {
        0: "No Color",
        1: "Red",
        2: "Orange",
        3: "Yellow",
        4: "Cyan",
        5: "Purple",
        6: "Almond",
        7: "Teal",
        8: "Blue",
        9: "Raspberry",
        10: "Green",
        11: "Violet",
    }

    @api.depends("key_priority_color_code")
    def _compute_key_priority_color(self):
        for record in self:
            record.key_priority_color = self.COLOR_MAP.get(
                record.key_priority_color_code, "Unknown"
            )

    # Restrict delete globally
    def unlink(self):
        raise UserError("You cannot delete Daily Standup records.")

    def action_accept(self):
        self.write({'state': 'approved'})
        self._schedule_task_type_activity()

    def action_refuse(self):
        self.write({'state': 'cancelled'})

    def action_approve(self):
        for record in self:
            record.write({'state': 'approved'})
        self._schedule_task_type_activity()

    def cancel(self):
        self.write({'state': 'cancelled'})

    field_readonly = fields.Boolean(
        string='Readonly for completed',
        compute='_compute_field_readonly'
    )

    @api.depends('state')
    def _compute_field_readonly(self):
        for rec in self:
            rec.field_readonly = rec.state == 'completed'

    def action_business_analyst(self):
        """
        Trigger the wizard for business analysts.
        """
        today = fields.Date.today()
        next_day = today + timedelta(days=1)

        if today.weekday() == 4:  # Friday -> skip weekend
            next_day = today + timedelta(days=3)

        wizard = self.env['business.analyst.wizard'].create({'date': next_day})
        return {
            'name': _("Business Analyst"),
            'type': 'ir.actions.act_window',
            'res_model': 'business.analyst.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': wizard.id,
        }

    def action_completed(self):
        for rec in self:
            # Validate before marking as completed
            if rec.percentage_completion < 100:
                raise UserError(_("You cannot mark this task Completed at less than 100%"))

            # Update state and completion date
            rec.write({
                'state': 'completed',
                'completion_date': fields.Date.today(),
            })

            # Create or update performance record
            performance = self.env['performance'].search([
                ('business_analyst_id', '=', rec.id)], limit=1)
            vals = {
                'business_analyst_id': rec.id,
                'employee_id': rec.employee_name.id,
                'department_id': rec.department_id.id,
                'completed_date': rec.completion_date,
                'priority_score': rec.priority_task_key_id.score if rec.priority_task_key_id else 0.0,
                'time_estimation_score': rec.time_estimation_key_id.score if rec.time_estimation_key_id else 0.0,
                'escalation_score': rec.escalation_key_id.score if rec.escalation_key_id else 0.0,
                'total_score': (
                    (rec.priority_task_key_id.score if rec.priority_task_key_id else 0.0)
                    + (rec.time_estimation_key_id.score if rec.time_estimation_key_id else 0.0)
                    + (rec.escalation_key_id.score if rec.escalation_key_id else 0.0)
                ),
                'creation_date': rec.creation_date,
                'approved_date': fields.Datetime.now(),
            }

            if performance:
                performance.write(vals)
            else:
                self.env['performance'].create(vals)

            rec._sync_to_standup_analysis()

    @api.model
    def create(self, vals):
        record = super(BusinessAnalyst, self).create(vals)

        if record.employee_name:
            record._sync_to_standup_analysis(on_create=True)

        return record

    def write(self, vals):
        # Restrict archiving unless cancelled
        if "active" in vals and vals["active"] is False:
            for record in self:
                if record.state != "cancelled":
                    raise UserError("You can only archive Daily Standup records when state is Cancelled.")

        res = super(BusinessAnalyst, self).write(vals)

        # After saving, sync to daily.standup.analysis using update logic
        for rec in self:
            rec._sync_to_standup_analysis(on_create=False)

        return res

    def _sync_to_standup_analysis(self, on_create=False):
        """Sync Business Analyst record to daily.standup.analysis

        on_create: if True, create a record as soon as employee_name is set
        """
        Standup = self.env['daily.standup.analysis']

        for rec in self:
            if not rec.employee_name:
                continue

            if on_create:
                Standup.create({
                    'business_analyst_id': rec.id,
                    'employee_name': rec.employee_name.id,
                    'project_id': rec.project_id.id,
                    'task_id': rec.task_id.id,
                    'priority_task_key_id': rec.priority_task_key_id.id,
                    'percentage_completion': rec.percentage_completion,
                    'completion_date': rec.completion_date,
                })
            else:
                analysis = Standup.search([('business_analyst_id', '=', rec.id)], limit=1)

                vals = {
                    'employee_name': rec.employee_name.id,
                    'project_id': rec.project_id.id,
                    'task_id': rec.task_id.id,
                    'priority_task_key_id': rec.priority_task_key_id.id,
                    'percentage_completion': rec.percentage_completion,
                    'completion_date': rec.completion_date,
                }

                if analysis:
                    analysis.write(vals)
                else:
                    Standup.create(dict(vals, business_analyst_id=rec.id))

    def action_non_compliance(self):
        """Trigger the non-compliance selection wizard"""
        return {
            'name': _("Non-Compliance"),
            'type': 'ir.actions.act_window',
            'res_model': 'non.compliance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_res_id': self.id, 'default_res_model': self._name}
        }

    def _schedule_task_type_activity(self):
        """ER 4.0 - 2.0.4: when a Business Analyst standup reaches Approved,
        schedule the Activity Type linked to its Task Type on the employee.
        No date_deadline is passed, so Odoo computes the due date from the
        Activity Type's own delay setup (2.0.4 rule 2)."""
        for rec in self:
            if rec.state != 'approved':
                continue
            if not rec.task_type_id or not rec.task_type_id.activity_type_id:
                continue
            user = rec.employee_name.user_id
            if not user:
                continue
            rec.activity_schedule(
                activity_type_id=rec.task_type_id.activity_type_id.id,
                user_id=user.id,
            )

    # def action_duplicate_records(self):
    #     """Action for the Server Action to duplicate selected records and reset state"""
    #     for record in self:
    #         record.copy()