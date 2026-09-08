# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class ClientWebForm(http.Controller):
    @http.route(['/client_webform/form'], type='http', auth='public', website=True)
    def client_webform(self, **kw):
        partners = request.env['number.employee'].sudo().search([])
        users = request.env['number.user'].sudo().search([])
        sectors = request.env['industry.sector'].sudo().search([])
        return request.render('client_sales_webform.register_client_website',
                              {'partners': partners, 'users': users, 'sectors': sectors})

    @http.route('/client_webform/submit', type='http', auth="public", website=True, methods=['POST'], csrf=False)
    def client_webform_submit(self, **post):
        number_users_input = post.get('number_users_id')
        industry_sector_input = post.get('industry_sector_id')
        number_employees_input = post.get('number_employees_id')

        number_users_id = False
        if number_users_input:
            number_users = request.env['number.user'].sudo().search([('name', '=', number_users_input)], limit=1)
            if not number_users:
                user = request.env['number.user'].sudo().create({
                    'name': number_users_input,
                    'score': 0,
                })
                number_users_id = user.id

        industry_sector_id = False
        if industry_sector_input:
            sector = request.env['industry.sector'].sudo().search([('name', '=', industry_sector_input)],
                                                                           limit=1)
            if not sector:
                sector = request.env['industry.sector'].sudo().create({
                    'name': industry_sector_input,
                    'score':0,
                })
            industry_sector_id = sector.id

        number_employees_id = False
        if number_employees_input:
            employee = request.env['number.employee'].sudo().search([
                ('name', '=', number_employees_input)
            ], limit=1)
            if not employee:
                employee = request.env['number.employee'].sudo().create({
                    'name': number_employees_input,
                    'score': 0,
                })
            number_employees_id = employee.id

        vals = {
            'subject': post.get('subject'),
            'contact_name': post.get('contact_name'),
            'function': post.get('function'),
            'email_from': post.get('email_from'),
            'name': post.get('name'),  # Company Name
            'website': post.get('website'),
            'number_user': number_users_id,
            'industry_sector': industry_sector_id,
            'number_employee': number_employees_id,
            'crm': bool(post.get('crm')),
            'purchase': bool(post.get('purchase')),
            'hr': bool(post.get('hr')),
            'warehousing': bool(post.get('warehousing')),
            'payroll': bool(post.get('payroll')),
            'sales': bool(post.get('sales')),
            'accounting': bool(post.get('accounting')),
            'project': bool(post.get('project')),
            'point': bool(post.get('point')),
            'manufacturing': bool(post.get('manufacturing')),
            'no_months': post.get('no_months'),
            'any_info': post.get('any_info'),
            'partner_name': post.get('name'),

            'type': 'lead'
        }

        request.env['crm.lead'].sudo().create(vals)
        return request.redirect('/success')

    @http.route('/success', type='http', auth="public", website=True)
    def success_register(self):
        return request.render("client_sales_webform.success_register")

