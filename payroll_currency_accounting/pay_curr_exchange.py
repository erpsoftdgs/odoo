# coding: utf-8
import logging
import re
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)



class HrPayroll(models.Model):
    _inherit = "hr.payroll.structure"

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        help="Select the currency for this salary structure."
             "Only active currencies are shown.",
        domain=[('active', '=', True)]
    )


    @api.constrains('currency_id', 'rule_ids')
    def _check_currency_uniqueness(self):
        for structure in self:
            selected_currency = structure.currency_id
            rule_currencies = (structure.rule_ids.mapped('currency_id')
                               .filtered(lambda c: c))

            if rule_currencies and selected_currency and any(
                currency != selected_currency for
                currency in rule_currencies
            ):
                raise UserError(
                    _("You can only have one currency for a salary "
                      "structure.Please ensure all salary rules "
                      "use the same currency.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        structures = super(HrPayroll, self).create(vals_list)
        for structure in structures:
            structure._check_currency_uniqueness()
        return structures


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    currency_id = fields.Many2one(
        'res.currency', string="Currency",
        related="struct_id.currency_id", readonly=False, store=True
    )

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        res = super()._prepare_line_values(
            line=line, account_id=account_id, date=date, debit=debit, credit=credit
        )

        if not self.currency_id:
            raise UserError(_("Salary Structure currency is not set. Please set the currency in the Salary Structure."))

        res['currency_id'] = self.currency_id.id
        res['company_currency_id'] = self.company_id.currency_id.id
        res['company_id'] = self.company_id.id
        return res

    def action_payslip_done(self):
        """
        Generate the accounting entries related to the selected payslips.
        A move is created for each journal and for each month.
        """
        for slip in self:
            if not slip.struct_id.currency_id:
                raise UserError(_("Salary Structure must have a currency set."))

            # Enforce use of structure's currency only
            slip.currency_id = slip.struct_id.currency_id
            slip.contract_id.currency_id = slip.struct_id.currency_id

            # Optional: Validate exchange rate if needed
            if slip.currency_id != slip.company_id.currency_id:
                rates = slip.env['res.currency.rate'].search([
                    ('rate', '>', 0),
                    ('currency_id', '=', slip.currency_id.id)
                ])
                current_month_rate = next(
                    (rate for rate in rates if rate.name.month == slip.date_to.month), None
                )
                if not current_month_rate:
                    raise UserError(_(
                        "No exchange rate is set for the current month."
                        " Please set an exchange rate for the month."
                    ))

        return super().action_payslip_done()


class HrContract(models.Model):
    _inherit = "hr.contract"

    struct_id = fields.Many2one('hr.payroll.structure', string="Salary Structure")
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  related="structure_type_id.default_struct_id.currency_id",
                                  store=True,
                                  readonly=False,
                                  default=lambda self: self.env.company.currency_id)
    wage = fields.Monetary(string="Wage", currency_field='currency_id')


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            company_id = vals.get('company_id', self.env.company.id)
            company = self.env['res.company'].browse(company_id)
            company_currency_id = company.currency_id.id

            narration = vals.get('narration', '')
            payslip_name = None
            if narration:
                match = re.search(r'SLIP/\d+', narration)
                if match:
                    payslip_name = match.group(0)
            payslip_currency_id = None
            if payslip_name:
                payslip = self.env['hr.payslip'].search([('number', '=', payslip_name)], limit=1)
                if payslip:
                    payslip_currency_id = payslip.currency_id.id
            line_ids = vals.get('line_ids', [])
            for line in line_ids:
                if line[0] == 0:
                    line_data = line[2]
                    line_data['company_id'] = line_data.get('company_id', company_id)
                    currency_id = payslip_currency_id or company_currency_id
                    if (currency_id and currency_id != company_currency_id and
                            ('debit' in line_data or 'credit' in line_data)):
                        conversion_date = vals.get('date', fields.Date.today())
                        transaction_currency = self.env['res.currency'].browse(currency_id)
                        company_currency = self.env['res.currency'].browse(company_currency_id)

                        if line_data.get('debit', 0) > 0:
                            original_debit = line_data['debit']
                            line_data['amount_currency'] = original_debit
                            # converted_data = transaction_currency._convert(
                            #     original_debit, company_currency, company, conversion_date
                            # )
                            line_data['debit'] = transaction_currency._convert(
                                original_debit, company_currency, company, conversion_date
                            )
                            line_data['currency_id'] = currency_id

                        if line_data.get('credit', 0) > 0:
                            original_credit = line_data['credit']
                            line_data['amount_currency'] = -original_credit
                            line_data['credit'] = transaction_currency._convert(
                                original_credit, company_currency, company, conversion_date
                            )
                            line_data['currency_id'] = currency_id

        return super(AccountMove, self).create(vals_list)


class SalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    is_currency_translatable = fields.Boolean(string="Translate Currency",
                                              default=False)
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        help="Select the currency for this salary rule. "
             "Only active currencies are shown.",
        domain=[('active', '=', True)]
    )
    cur_date = fields.Datetime(
        string='Currency Date',
        default=lambda self: fields.Datetime.now()
    )

    @api.onchange('is_currency_translatable')
    def _onchange_is_currency_translatable(self):
        if not self.is_currency_translatable:
            self.currency_id = False
            self.cur_date = False

    @api.model
    def compute_rule(self, employee, contract, date_from,
                     date_to, payslip_id=None):
        amount = (super(SalaryRule, self).compute_rule
                  (employee, contract, date_from, date_to, payslip_id))
        if self.currency_id:
            return self.currency_id.round(amount)
        return amount
