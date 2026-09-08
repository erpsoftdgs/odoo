from odoo import models, fields, api


class InheritCrm(models.Model):
    _inherit = 'crm.lead'
    # _rec_name = 'subject'


    purchase = fields.Boolean(string='Purchase')
    hr = fields.Boolean(string='HR')
    warehousing = fields.Boolean(string='Warehousing')
    payroll = fields.Boolean(string='Payroll')
    sales = fields.Boolean(string='Sales')
    accounting = fields.Boolean(string='Accounting')
    project = fields.Boolean(string='Project')
    point = fields.Boolean(string='Point of Sales')
    manufacturing = fields.Boolean(string='Manufacturing')
    crm = fields.Boolean(string='CRM')
    no_months = fields.Char(string='Number of Months Financial History')
    any_info = fields.Char(string='Any Other Information')
    subject = fields.Char(string="Subject")

    # Define missing fields to avoid errors
    # number_employees_id = fields.Integer(string='Number of Employees')
    # number_users_id = fields.Integer(string='Number of Users')
    # industry_sector_id= fields.Many2one('res.partner.industry', string="Industry Sector")
    # website = fields.Char(string="Company Website")

    def print_report(self):
        return self.env.ref('client_sales_webform.report_crm_lead').report_action(self)
