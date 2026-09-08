# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
# from odoo.exceptions import UserError
from odoo.exceptions import UserError as ProjectError


class ProjectAuditResCompany(models.Model):
    _inherit = 'res.company'
    minimum_audits_per_phase = fields.Boolean("Minimum Audits Per Phase")
    num_audits = fields.Integer("", default="")


class ProjectAuditResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    minimum_audits_per_phase = fields.\
        Boolean(related="company_id.minimum_audits_per_phase", readonly=False)
    num_audits = fields.Integer(related="company_id.num_audits", readonly=False)


class ProjectAuditApprovers(models.Model):
    _name = 'project.approvers'
    _description = "Project approvers"

    name = fields.Many2one("hr.employee", "User")
    role = fields.Selection([('project_manager_audit', 'Project / Project Manager'),
                             ('compliance_manager_audit', 'Project / Compliance Manager'),
                             ('delivery_manager_audit', 'Project / Delivery Manager')], default='')


class ProjectScoreCard(models.Model):
    _name = 'project.scorecard'
    _description = 'Project scorecard'
    _rec_name = 'name_rating'


    name = fields.Integer("Score")
    ratings = fields.Char("Ratings")
    name_rating = fields.Char(string='Rating Name', compute='get_name_rating')

    @api.depends('name')
    def get_name_rating(self):
        for record in self:
            record.name_rating = f"[{record.name}] {record.ratings}"



class ProjectAuditPhases(models.Model):
    _name = 'project.audit.phases'
    _description = 'Project Audit Phase'

    name = fields.Char("Project Phase")


class ProjectAuditDelivery(models.Model):
    _name = 'project.delivery'
    _description = 'Project delivery'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.depends('project_manager')
    def _compute_user_role(self):
        user_company = self.env.company.id
        employee_detail = self.env['hr.employee'].sudo(). \
            search(['&', ('user_id', '=', self.env.uid),
                    ('company_id', '=', user_company)], limit=1)
        retrieved_user_roles = []
        get_approver_role = self.env['project.approvers'].sudo().\
            search([('name', '=', employee_detail.id)])

        for user_role in get_approver_role:
            retrieved_user_roles.append(user_role.role)
        self.audit_user_role = retrieved_user_roles

        if 'project_manager_audit' in retrieved_user_roles:
            self.role_project_manager = True

        if 'compliance_manager_audit' in retrieved_user_roles:
            self.role_compliance_manager = True

        if 'delivery_manager_audit' in retrieved_user_roles:
            self.role_delivery_manager = True

        if 'project_manager_audit' in \
                retrieved_user_roles or 'compliance_manager_audit' in \
                retrieved_user_roles or 'delivery_manager_audit' \
                in retrieved_user_roles:
            self.any_available_role = True

    @api.onchange('project_lines')
    def _scoretotal_all(self):
        total_ratings = 0
        number_lines = 0
        audit_phases = []
        score_card = []

        # get the maximum scorecard
        highest_score = self.env['project.scorecard'].sudo().search([], order="name desc")
        for highest_val in highest_score:
            score_card.append(highest_val.name)

        for record in self.project_lines:

            if not record.display_type:
                total_ratings = total_ratings + int(record.ratings.name)
                number_lines = number_lines + 1
                if record.audit_phase.id:
                    audit_phases.append(record.audit_phase.id)

        self.audit_score = total_ratings

        self.score = (score_card[0] if score_card else 0) * number_lines

        if self.score != 0:
            self.performance_percent = (total_ratings / self.score) * 100

        unique_audit_phase = list(set(audit_phases))

        # get config from company
        minimum_lines = self.env['res.company'].sudo().\
            search([('minimum_audits_per_phase', '=', True)], limit=1)

        if minimum_lines:

            minimum_audit_phase_lines = minimum_lines.num_audits

            for list_val in unique_audit_phase:

                num_counts = audit_phases.count(list_val)

                if num_counts < minimum_audit_phase_lines:
                    # update field to track audit phase limit
                    self.minimum_lines_per_phase_tracker = True

                if num_counts >= minimum_audit_phase_lines:
                    # update field to track audit phase limit
                    self.minimum_lines_per_phase_tracker = False

    name = fields.Char('Audit Number')
    active = fields.Boolean('Active', default=True)
    client_name = fields.Many2one('project.project', "Client Name")
    audit_date = fields.Date("Audit Date", default=lambda self: fields.Date.today())
    project_current_week = fields.Integer("Project Current Week")
    project_current_phase = fields.Many2one('project.audit.phases', "Project Current Phase")
    score = fields.Integer("Possible Score")
    audit_score = fields.Integer("Audit Score")
    performance_percent = fields.Integer("Performance %")
    audit_user_role = fields.Char("User role", compute='_compute_user_role', store=False)
    role_project_manager = fields.Boolean("Role Manager", store=False, default=False)
    role_compliance_manager = fields.Boolean("Role Compliance Manager", store=False, default=False)
    role_delivery_manager = fields.Boolean("Role Delivery Manager", store=False, default=False)
    any_available_role = fields.Boolean("Any Role", store=False, default=False)
    scheduled_lock = fields.Boolean("Lock fields", store=True, default=False, copy=False)
    require_lock = fields.Boolean("Require Lock", store=True, default=False)
    project_manager = fields.Many2one('res.users', domain=lambda self: [
        ("groups_id", "=", self.env.ref("project_audit.project_audit_manager").id)])
    project_lines = fields.One2many('project.delivery.lines', 'delivery_id', string="Project Lines",
                                    states={'cancelled': [('readonly', True)],
                                            'done': [('readonly', True)]},
                                    copy=True, auto_join=True)
    minimum_lines_per_phase_tracker = fields.\
        Boolean("audit lines tracker", store=True, default=False)
    state = fields.Selection(
        [('draft', 'Draft'), ('scheduled', 'Scheduled'),
         ('in_progress', 'In Progress'), ('done', 'Done'),
         ('cancelled', 'Cancelled')], default="draft", tracking=True, copy=False, readonly=False)

    def action_audit_start(self):
        self.state = 'scheduled'
        self.scheduled_lock = True

    def approve_audit_record(self):
        self.state = 'in_progress'
        self.require_lock = True

    def action_audit_done(self):
        self.state = 'done'

    def action_cancel_audit(self):
        self.state = 'cancelled'

    @api.constrains('minimum_lines_per_phase_tracker')
    def check_minimum_requirements(self):

        if self.minimum_lines_per_phase_tracker:
            raise ProjectError(_('Minimum audit lines per audit phase not met'))

    @api.model_create_multi
    def create(self, vals_list):
        # Ensure vals_list is always a list
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        # Process each record's values
        for vals in vals_list:
            if vals.get('minimum_lines_per_phase_tracker'):
                raise ProjectError(_('Minimum audit lines per audit phase not met'))
            # Generate sequence number for each record
            vals['name'] = str(self.env['ir.sequence'].next_by_code('project.audit.number'))

        res = super(ProjectAuditDelivery, self).create(vals_list)
        return res

    def write(self, vals):
        res = super(ProjectAuditDelivery, self).write(vals)
        if self.state == 'done':

            for record in self.project_lines:
                if not record.display_type:
                    if not record.ratings or not record.comments:
                        raise ProjectError(_('Ratings and Comments are mandatory to proceed'))
        return res

    def unlink(self):
        for record in self:
            logging.debug("You cannot delete %s", record.name)
            raise ProjectError(_('Record cannot be deleted'))
        res = super(ProjectAuditDelivery, self).unlink()
        return res


class ProjectLines(models.Model):
    _name = 'project.delivery.lines'
    _description = 'Project delivery lines'

    @api.depends('audit_phase')
    def _compute_user_role(self):

        user_company = self.env.company.id
        employee_detail = self.env['hr.employee'].sudo(). \
            search(['&', ('user_id', '=', self.env.uid),
                    ('company_id', '=', user_company)], limit=1)
        retrieved_user_roles = []
        get_approver_role = self.env['project.approvers'].sudo().\
            search([('name', '=', employee_detail.id)])

        for user_role in get_approver_role:
            retrieved_user_roles.append(user_role.role)
        self.audit_user_role = retrieved_user_roles

        if 'project_manager_audit' in retrieved_user_roles:
            self.role_project_manager = True

        if 'compliance_manager_audit' in retrieved_user_roles:
            self.role_compliance_manager = True

        if 'delivery_manager_audit' in retrieved_user_roles:
            self.role_delivery_manager = True

        if 'project_manager_audit' in \
                retrieved_user_roles or 'compliance_manager_audit' in \
                retrieved_user_roles or 'delivery_manager_audit' in \
                retrieved_user_roles:
            self.any_available_role = True

    delivery_id = fields.Many2one('project.delivery', "Delivery ID")
    audit_phase = fields.Many2one('project.audit.phases', "Audit Phase")
    audit_task = fields.Char("Audit Task")
    name = fields.Text(string='Description')
    ratings = fields.Many2one('project.scorecard', "Ratings", copy=False)
    sequence = fields.Integer(string='Sequence', default=10)
    comments = fields.Char("Comments", copy=False)
    document = fields.Char("Document", copy=False)
    audit_user_role = fields.Char("User role", compute='_compute_user_role', store=False)
    role_project_manager = fields.Boolean("Role Manager", store=False, default=False)
    role_compliance_manager = fields.Boolean("Role Compliance Manager", store=False, default=False)
    role_delivery_manager = fields.Boolean("Role Delivery Manager", store=False, default=False)
    any_available_role = fields.Boolean("Any Role", store=False, default=False)
    status = fields.Selection(related="delivery_id.state", readonly=False)
    scheduled_lock = fields.Boolean(related="delivery_id.scheduled_lock", readonly=False)
    require_lock = fields.Boolean(related="delivery_id.require_lock", readonly=False)
    total_score = fields.Integer(related="delivery_id.score", readonly=False)
    display_type = fields.Selection([('line_section', "Section")],
                                    default=False, help="Technical field for UX purpose.")
