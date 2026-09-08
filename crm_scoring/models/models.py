# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ContactType(models.Model):
    _name = 'contact.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Contact Type'

    name = fields.Char(string='Contact Type', required=True)
    score = fields.Integer(string='Score', required=True)


class BusinessSize(models.Model):
    _name = 'business.size'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Business Size'

    name = fields.Char(string='Business Size', required=True)
    score = fields.Integer(string='Score', required=True)


class CompanyAge(models.Model):
    _name = 'company.age'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Company Age'

    name = fields.Char(string='Company Age', required=True)
    score = fields.Integer(string='Score', required=True)


class NumberEmployee(models.Model):
    _name = 'number.employee'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Number of Employees'

    name = fields.Char(string='Number of Employees', required=True)
    score = fields.Integer(string='Score', required=True)


class ModulesEstimate(models.Model):
    _name = 'modules.estimate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Modules Estimate'

    name = fields.Char(string='Modules Estimate', required=True)
    score = fields.Integer(string='Score', required=True)


class IndustrySector(models.Model):
    _name = 'industry.sector'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Industry Sector'

    name = fields.Char(string='Industry Sector', required=True)
    score = fields.Integer(string='Score', required=True)


class NumberUser(models.Model):
    _name = 'number.user'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Number of Users'

    name = fields.Char(string='Number of Users', required=True)
    score = fields.Integer(string='Score', required=True)


class Customization(models.Model):
    _name = 'res.customization'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Customization'

    name = fields.Char(string='Customization', required=True)
    score = fields.Integer(string='Score', required=True)


class CrmLead(models.Model):
    _inherit = "crm.lead"

    contact_type = fields.Many2one("contact.type", string="Contact Type")
    business_size = fields.Many2one("business.size", string="Business Size")
    company_size = fields.Many2one("company.age", string="Company Age")
    number_employee = fields.Many2one("number.employee", string="Number of Employees")
    modules_estimate = fields.Many2one("modules.estimate", string="Modules Estimate")
    industry_sector = fields.Many2one("industry.sector", string="Industry Sector")
    number_user = fields.Many2one("number.user", string="Number of Users")
    customization = fields.Many2one("res.customization", string="Customisation")

    score_percentage = fields.Float(string="Score %", compute="_compute_score_percentage",
                                    store=True, tracking=True)

    @api.depends('contact_type.score', 'business_size.score', 'company_size.score',
                 'number_employee.score', 'modules_estimate.score', 'industry_sector.score',
                 'number_user.score', 'customization.score')
    def _compute_score_percentage(self):
        for rec in self:
            if rec.contact_type and rec.business_size and rec.company_size and \
                    rec.number_employee and rec.modules_estimate and rec.industry_sector \
                    and rec.number_user and rec.customization:
                rec.score_percentage = (
                    rec.contact_type.score + rec.business_size.score + rec.company_size.score +
                    rec.number_employee.score + rec.modules_estimate.score + rec.industry_sector.score +
                    rec.number_user.score + rec.customization.score
                )
            else:
                rec.score_percentage = 0.0

    def update_lead_scores(self):
        for lead in self.search([]):
            lead._compute_score_percentage()

    @api.model
    def trigger_score_update(self):
        cron = self.env.ref("crm_scoring.crm_lead_score_update_cron")
        cron.active = True

    def write(self, vals):
        res = super(CrmLead, self).write(vals)
        if "probability" in vals:
            self.trigger_score_update()
        if 'score_percentage' in vals:
            for lead in self:
                old_score = lead.score_percentage
                new_score = vals.get('score_percentage')
                if old_score != new_score:
                    timestamp = fields.Datetime.now()
                    user_name = self.env.user.name

                    lead.message_post(
                        body=_(f"""
                            <b>Score Updated:</b><br/>
                            <b>User:</b> {user_name} <br/>
                            <b>Date & Time:</b> {timestamp} <br/>
                            <b>Old Score:</b> {old_score}% <br/>
                            <b>New Score:</b> {new_score}%
                        """),
                        subtype_xmlid="mail.mt_note",
                    )
        return res
