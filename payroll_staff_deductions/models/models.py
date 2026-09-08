# -*- coding: utf-8 -*-
import datetime
import dateutil
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PayrollStaffDeductionContract(models.Model):
    _inherit = 'hr.contract'
    gender_new = fields.Selection(related='employee_id.gender', readonly=True)
    esa_loan_amount = fields.Float('Loan Amount',
                                   digits=(16, 2),
                                   default=0.0,
                                   required=True,
                                   help="The Loan Amount")
    esa_monthly_payment = fields.Float('Monthly Payment',
                                       digits=(16, 2),
                                       default=0.0,
                                       required=True,
                                       help="The Monthly Payment")
    # 'esa_loan_balance': fields.Float('Loan Balance',
    # digits=(16,2) required=False, readonly=True, help="The Loan Balance")
    esa_number_of_payments = fields.Integer('Number Of Payments')
    esa_start_date = fields.Date('Loan Start Date')
    esa_end_date = fields.Date('Loan End Date')
    esa_penalty_amount = fields.Float('Penalty Amount',
                                      digits=(16, 2),
                                      required=False,
                                      readonly=False,
                                      help="The Penalty  Amount")
    esa_th_amount = fields.Float('13th Month Amt', digits=(16, 2), required=False, readonly=False,
                                 help="The 13th Month Amount")

    esa_active_flg = fields.Boolean('Loan Active')
    esa_terminate_loan = fields.Boolean('Terminate Loan')
    esa_penalty_active = fields.Boolean('Penalty Active')
    maternity_pay = fields.Boolean('Maternity Pay')
    nhf_fund = fields.Boolean('NHF Fund')
    month_value = fields.Boolean('13th Month')
    month_percent_value = fields.Integer('13th Month %')
    is_created = fields.Boolean('Created')
    # loan_histories_id = fields.One2many('loan_status_history','employee_id')
    overtime = fields.Float("Overtime Hours", digits=(16, 2))
    overtime_two = fields.Float("Overtime Rate", digits=(16, 2))
    time_off_period = fields.Integer("Time off Period")
    time_off_pay_rate = fields.Integer("Time off Pay rate")
    overtime_amount = fields.Integer("Overtime amount", compute="_compute_overtime_amount")

    @api.depends('overtime', 'overtime_two')
    def _compute_overtime_amount(self):
        for rec in self:
            rec.overtime_amount = rec.overtime * rec.overtime_two

    def save_loan_history(self, vals, termintate=False):
        if termintate:
            status = 'terminated'
            balance = 0.0

        elif 'esa_loan_amount' in vals:
            status = 'approved'

            balance = vals['esa_loan_amount']
        else:
            status = 'terminated'
            balance = 0.0
        loan_history = [(0, 0, {'status': status,
                                'date': datetime.date.today(),
                                'balance': balance,
                                'processed_by': self.env.user.name,
                                'employee_id': self.employee_id})]
        return loan_history

    @api.model
    def create(self, vals):

        if vals.get('is_created', None):
            vals['esa_active_flg'] = True
            vals['esa_terminate_loan'] = False

            # vals['loan_histories_id']=self.save_loan_history(vals)
        lot = super(PayrollStaffDeductionContract, self).create(vals)
        return lot

    def write(self, vals):
        if vals.get('is_created', None):
            vals['esa_active_flg'] = True
            vals['esa_terminate_loan'] = False
            # vals['loan_histories_id'] = self.save_loan_history(vals)
        if vals.get('esa_terminate_loan', None):
            vals['esa_active_flg'] = False
            vals['is_created'] = False
            # vals['loan_histories_id'] = self.save_loan_history(vals,Termintate=True)
            # else:
            #   vals['esa_active_flg']=True
            #  vals['is_created'] = True

        lot = super(PayrollStaffDeductionContract, self).write(vals)
        return lot

    @api.onchange('esa_active_flg')
    def onchange_active(self):
        mess = {}
        if self.esa_active_flg:
            if self.esa_loan_amount <= 0.0:
                mess = {

                    'warning': {'title': 'Warning!', 'message': ' Loan Amount Must Be Greater than 0'},
                    'value': {'esa_loan_amount': 0.0, 'esa_active_flg': False}
                }

        return mess

    @api.onchange('esa_terminate_loan')
    def confirm_onchange(self):
        mess = {}
        if self.esa_terminate_loan:
            mess = {

                'value': {'is_created': True, 'esa_active_flg': False}
            }
        return mess

    @api.onchange('esa_monthly_payment')
    def onchange_payment(self):
        mess = {}
        amount = self.esa_loan_amount
        num_amount = self.esa_number_of_payments
        if amount and num_amount:
            r = amount / num_amount
            if int(r) != int(self.esa_monthly_payment):
                mess = {

                    'warning': {'title': 'Warning!',
                                'message': 'The Monthly Payment Must Be Equal To'
                                           ' The Loan Amount / Number of Payments '},
                    'value': {'esa_monthly_payment': ''}
                }

        return mess

    @api.onchange('esa_number_of_payments')
    def onchange_m_payment(self):
        mess = {}
        if self.esa_start_date and self.esa_end_date:
            date1 = datetime.datetime.strptime(self.esa_start_date, '%Y-%m-%d')
            date2 = datetime.datetime.strptime(self.esa_end_date, '%Y-%m-%d')

            r = dateutil.relativedelta.relativedelta(date2, date1)
            if int(r.months) != int(self.esa_number_of_payments):
                mess = {

                    'warning': {'title': 'Warning!',
                                'message': 'The Total Number of Payment Must Match'
                                           ' The Number of Month Between Loan Start and End Date'},
                    'value': {'esa_number_of_payments': ''}
                }

        return mess


# class loan_status(models.Model):
#
#     _name = 'loan_status_history'
#     status_selection = [('approve','Approved'),('active','Active'),
#                          ('terminated','Terminated'),('paid','Paid')]
#     status = fields.Selection(status_selection,'Loan Status')
#     date = fields.Date('Proccessed Date')
#     amount_paid = fields.Float('Amount Paid',digits=(16, 2) )
#     balance = fields.Float('Balance',digits=(16, 2) )
#     processed_by = fields.Char(string='Proceesed By')
#     employee_id = fields.Many2one('hr.contract','loan_histories_id')


class HRSalaryRules(models.Model):
    _inherit = 'hr.salary.rule'

    enable_automation = fields.Boolean()


class PayslipModelO(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def create(self, values):
        hr_rule = self.env['hr.salary.rule'].search([('enable_automation', '=', True)])
        rid_list = []
        if 'employee_id' not in values or 'contract_id' not in values:
            payslip = self.env['hr.payslip'].browse(values.get('slip_id'))
            values['employee_id'] = values.get('employee_id') or payslip.employee_id.id
            values['contract_id'] = values.get('contract_id') or payslip.contract_id and payslip.contract_id.id
            if not values['contract_id']:
                raise UserError(_('You must set a contract to create a payslip line.'))
        for rule in hr_rule:
            rid = {'name': rule.name, 'code': rule.code, 'contract_id': values['contract_id']}
            rid_list.append((0, 0, rid))
        # values['worked_days_line_ids'] = rid_list
        return super(PayslipModelO, self).create(values)
