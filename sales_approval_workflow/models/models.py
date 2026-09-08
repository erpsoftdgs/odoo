# -*- coding: utf-8 -*-
from odoo import fields, models, _, api
from odoo.exceptions import ValidationError


# -----------------------------------Sales Module Extension---------------------------------------------#
class SalesWorkFlow(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('reviewer', 'Quotation Review'),
        ('quotation_approval', 'Quotation Approved'),
        ('sent', 'Quotation Sent'),
        ('approve 1', 'Sales Manager'),
        ('approve 2', 'CFO'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),

    ], string='Status', readonly=True, copy=False, track_visibility='onchange', default='draft')
    compute_field = fields.Boolean(string="check state", compute='_compute_get_user', defaul=False)

    # return string

    '''def get_str(self, string):
        total_amount = sum([line.total_amount for line in self.expense_line_ids])
        limit = self.env['expense.monetary.limit'].search(
            ['&', ('company_id', '=', self.company_id.id), ('sequence', '=', string)], limit=1)
        if not limit:
            return string
        if total_amount >= limit.monetary_limit:
            string = int(string) + 1
            return str(string)
        return string'''

    def switch_approval_state(self, val='1'):
        if not self.company_id.skip_workflow:
            self.action_confirm()
            return True
        if val == '1':
            self.write({'state': 'approve %s' % ('1')})
        elif val == '2':
            self.write({'state': 'approve %s' % ('2')})
        elif val == '3':
            self.button_approve(confirm=True)
        else:
            self.write({'state': 'approve %s' % (str(val))})
        return True


    def button_approve_3(self, force=False):
        self.action_confirm()
        return {}

    def button_approve_2(self, force=False):
        d_str = '2'
        return self.switch_approval_state(d_str)

    def button_confirm_quotation(self, force=False):
        d_str = '1'
        return self.switch_approval_state(d_str)

    def action_cfo_cancel(self):
        return self.write({'state': 'cancel'})

    def action_quotation_reviewer(self):
        return self.write({'state': 'reviewer'})

    def action_quotation_approval(self):
        return self.write({'state': 'quotation_approval'})

    def action_manager_cancel(self):
        return self.write({'state': 'cancel'})

    def _confirmation_error_message(self):
        """ Return whether order can be confirmed or not if not then returm error message. """
        self.ensure_one()
        if self.state not in {'approve 2'}:
            return _("Some orders are not in a state requiring confirmation.")
        if any(
                not line.display_type
                and not line.is_downpayment
                and not line.product_id
                for line in self.order_line
        ):
            return _("A line on these orders missing a product, you cannot confirm it.")

        return False

    def action_approve_2_cancel(self):
        return self.write({'state': 'cancel'})

    def action_reviewer_stage(self):
        return self.write({'state': 'reviewer'})

    def action_reviewer_cancel(self):
        return self.write({'state': 'cancel'})

    def action_quotation_approve_stage(self):
        return self.write({'state': 'quotation_approval'})

    def action_quotation_approve_cancel(self):
        return self.write({'state': 'cancel'})

    def confirm_approve_quotation(self):
        return self.write({'state': 'sent'})

    def action_send_quotation_approve_cancel(self):
        return self.write({'state': 'cancel'})

    #def action_quotation_send(self):
    #    self.ensure_one()
    #    for rec in self:
    #        res_user = rec.env['res.users'].search([('id', '=', rec._uid)])
    #        if res_user.has_group('sales_approval_workflow.group_quotation_reviewer'):
    #            raise ValidationError(_("Sales / Quotation Reviewer Role cannot perform this action"))
    #
    #    return super(SalesWorkFlow, self).action_quotation_send()

    def _compute_get_user(self):
        for rec in self:
            res_user = rec.env['res.users'].search([('id', '=', rec._uid)])
            if res_user.has_group('sales_approval_workflow.group_quotation_reviewer'):
                rec.compute_field = True
            else:
                rec.compute_field = False

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_so_as_sent'):
            self.filtered(lambda o: o.state == 'quotation_approval').with_context(tracking_disable=True).write(
                {'state': 'sent'})
            so_ctx = {'mail_post_autofollow': self.env.context.get('mail_post_autofollow', True)}
            if self.env.context.get('mark_so_as_sent') and 'mail_notify_author' not in kwargs:
                kwargs['notify_author'] = self.env.user.partner_id.id in (kwargs.get('partner_ids') or [])
            return super(SalesWorkFlow, self.with_context(**so_ctx)).message_post(**kwargs)
        
        return super(SalesWorkFlow, self).message_post(**kwargs)
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'sale':
            self.env.ref('sale.mt_order_confirmed')
        elif 'state' in init_values and self.state == 'sent':
            self.env.ref('sale.mt_order_sent')
        elif 'state' in init_values and self.state == 'reviewer':
            self.env.ref('sales_approval_workflow.mt_sale_quotation_reviewer')
        elif 'state' in init_values and self.state == 'quotation_approval':
            self.env.ref('sales_approval_workflow.mt_sale_quotation_approve')
        elif 'state' in init_values and self.state == 'approve 1':
            self.env.ref('sales_approval_workflow.mt_sale_approved_one')
        elif 'state' in init_values and self.state == 'approve 2':
            self.env.ref('sales_approval_workflow.mt_sale_approved_two')
        return super(SalesWorkFlow, self)._track_subtype(init_values)
