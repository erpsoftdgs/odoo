# -*- coding: utf-8 -*-
import odoo
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers import portal
# from odoo.addons.web.controllers.main import ensure_db

SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error', 'scope', 'mode',
                          'redirect', 'redirect_hostname', 'email', 'name', 'partner_id',
                          'password', 'confirm_password', 'city', 'country_id', 'lang'}


class DeveloperPortalDashboard(portal.CustomerPortal):
    def authenticate(self, code, surname):
        employee = request.env['hr.employee'].sudo().search(
            [('registration_number', '=', code), ('job_id.name', 'ilike', 'developer')], limit=1)
        if employee:
            lastname = employee.name.split(' ')[1].lower()
            if lastname == surname.strip().lower():
                return employee.id, employee.name, employee.work_email
        raise odoo.exceptions.AccessDenied

    def _get_default_values(self, is_rework=False, last_path_node=None, dashboard=False):
        values = {k: v for k, v in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}
        values['last_path_node'] = last_path_node if last_path_node is None else [last_path_node]
        values['page_name'] = 'rework' if is_rework else 'queue'
        if dashboard:
            values['page_name'] = 'home'
        values['no_footer'] = True
        return values

    @http.route('/developers/login', auth='public', website=True)
    def dev_login(self, redirect=None, **kw):
        if request.httprequest.method == 'GET' and redirect and request.session.devid:
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = self._get_default_values()
        values['no_footer'] = False
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            try:
                # login with code and surname
                devid, name, email = self.authenticate(request.params['code'], request.params['surname'])
                request.params['login_success'] = True
                request.session.update({'devid': devid, 'dev_name': name, 'dev_email': email})
                # record audit
                request.env['developer.audit'].sudo().create({'name': name})
                return request.redirect('/developer/dashboard')
                # return http.redirect_with_hash(self._login_redirect(uid, redirect=redirect))
            except odoo.exceptions.AccessDenied as e:
                #request.uid = old_uid
                request.update_env(user=old_uid)
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("You’re not authorised to access this page, contact your administrator!")
                else:
                    values['error'] = e.args[0]
        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = _('Only employees can access this database. Please contact the administrator.')

        # print('values', values, request.session)

        # values['no_header'] = True
        response = request.render('developers_queue.dev_login_tmp', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route('/developer/dashboard', auth='public', website=True)
    def dev_dashboard(self, redirect=None, **kw):
        if not request.session.devid:
            return request.redirect('/developers/login')
        # request.uid = '1234'
        values = self._get_default_values(dashboard=True)
        values['dev_name'] = request.session.dev_name
        values['dev_email'] = request.session.dev_email
        devid = request.session.devid
        values['job_count'] = len(request.env['helpdesk.ticket'].sudo().search(
            [('remote_developer', '=', devid), ('stage_id.name', 'ilike', 'job queue')]))
        values['rework_count'] = len(request.env['helpdesk.ticket'].sudo().search(
            [('remote_developer', '=', devid), ('stage_id.name', 'ilike', 'rework')]))
        # print('request', request, request.uid)
        response = request.render('developers_queue.dev_dash', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route('/developer/test-script/<int:ticket_id>', auth='public', website=True)
    def dev_test_script(self, ticket_id, redirect=None, **kw):
        if not request.session.devid:
            return request.redirect('/developers/login')
        # request.uid = '1234'
        values = self._get_default_values(dashboard=True)
        values['dev_name'] = request.session.dev_name
        values['dev_email'] = request.session.dev_email
        ticket = request.env['helpdesk.ticket'].sudo().browse(ticket_id)
        if ticket:
            spec_test_url_link = ticket.spec_test_url_link
            if 'docs.google' in spec_test_url_link:
                # return the link
                return request.redirect(spec_test_url_link)
            if 'erpsoftapp.com' in spec_test_url_link:
                test_script_id = int(spec_test_url_link.split('=')[1].split('&')[0])
                test_script = request.env['helpdesk.test.script'].sudo().browse(test_script_id)
                values['tests'] = test_script.test_case_line
        # print('request', request, request.uid)
        response = request.render('developers_queue.dev_test_script', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route(['/developer/job-queue', '/developer/reworks', '/developer/rework'], auth='public', website=True)
    def dev_queue(self, redirect=None, **kw):
        devid = request.session.devid
        if not devid:
            return request.redirect('/developers/login')
        is_rework = request.httprequest.url.split('/')[-1] in ['reworks', 'rework']
        stage = 'rework' if is_rework else 'job queue'
        values = self._get_default_values(is_rework=is_rework)
        values['tickets'] = request.env['helpdesk.ticket'].sudo().search(
            [('remote_developer', '=', devid), ('stage_id.name', 'ilike', stage)])
        # values['tickets'] = request.env['helpdesk.ticket'].sudo().search([])
        # print('Is rework', is_rework, request.httprequest.url, request.session, 'tickets', values['tickets'])
        response = request.render('developers_queue.dev_jobs', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route(['/developer/logout', '/logout'], auth='public', website='True')
    def dev_logout(self, **kw):
        request.session.update({'devid': None, 'dev_name': None, 'dev_email': None})
        return request.redirect('/developers/login')

