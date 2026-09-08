# -*- coding: utf-8 -*-

import base64
import requests
import time
from odoo import http
from odoo.http import request


class HelpdeskWebform(http.Controller):
    @http.route('/helpdesk/webform', type="http", auth="public", website=True)
    def index(self, **kw):
        company = request.env['res.company']\
            ._company_default_get('helpdesk_support_webform')
        ticket_type = request.env['ticket.type.customization'].sudo().search([('webform_show', '=', True)
                                                                         ])
        variables = {'ticket_type': ticket_type, 'company': company}
        return request.render('helpdesk_support_webform.create_ticket', variables)

    # @http.route('/create/ticket', type="http", auth="public", website=True, methods=["POST"])
    # def create_ticket(self, **kw):
    #     kw.pop("followers")
    #     kw.pop("attachments")
    #     ticket_phone = kw['user_phone_number']
    #     ticket_email = kw['partner_email']
    #     kw['tag_ids'] = [kw['ticket_type_id']]

    #     new_ticket = request.env['helpdesk.ticket'].sudo().create(kw)

    #     ticket_owner = request.env['res.partner'].sudo().search(
    #         [('email', '=', ticket_email)])
    #     ticket_owner.phone = ticket_phone

    #     template_id = request.env.ref(
    #         'helpdesk_support_webform.new_webform_ticket_email_template').id
    #     template = request.env['mail.template'].sudo().browse(template_id)
    #     template.send_mail(new_ticket
    #                        .id, force_send=True)
        
    #     if 'followers' in request.params:
    #         raw_emails = request.httprequest.form.get('followers').split(',')
    #         emails = [user.strip() for user in raw_emails if user.strip().lower() != "alert@gitlab.erpsoftapp.com"]

    #         for email in emails:
    #             follower = request.env['res.partner'].sudo().search(
    #                 [('email', '=', email)])
    #             if bool(follower):
    #                 new_ticket.message_subscribe(follower.ids)
    #             else:
    #                 message = "TO DO: Add {} to the system and make the user a follower of this ticket".format(
    #                     email)
    #                 new_ticket.message_post(body=message)

    #         all_followers = [
    #             user.email for user in new_ticket.message_partner_ids if user.email if user.email != new_ticket.email]
    #         follower_ticket_template_id = request.env.ref(
    #             'helpdesk_support_webform.follower_webform_ticket_email_template').id
    #         follower_ticket_template = request.env['mail.template'].sudo().browse(
    #             follower_ticket_template_id)
    #         follower_ticket_template.write(
    #             {'email_to': ','.join(all_followers)})
    #         follower_ticket_template.send_mail(
    #             new_ticket.id, force_send=True)

    #     if 'attachments' in request.params:
    #         attached_files = request.httprequest.files.getlist(
    #             'attachments')
    #         for attachment in attached_files:
    #             if attachment.filename == "":
    #                 continue
    #             attached_file = attachment.read()
    #             request.env['ir.attachment'].sudo().create({
    #                 'name': attachment.filename,
    #                 'res_model': 'helpdesk.ticket',
    #                 'res_id': new_ticket.id,
    #                 'type': 'binary',
    #                 'store_fname': attachment.filename,
    #                 'datas': base64.b64encode(attached_file),
    #             })

    #     return request.render('helpdesk_support_webform.form_thanks')

    def _looks_like_bot(self, vals):
        name = (vals.get('name') or vals.get('partner_name') or '').strip()

        # Signal 1: too long, no-space, mixed-case token
        if len(name) >= 15 and ' ' not in name and re.search(r'[a-z]', name) and re.search(r'[A-Z]', name):
            return True

        # Signal 2: honeypot — add a hidden field in the form template that
        # real users never see/fill (CSS display:none, NOT type="hidden")
        if vals.get('website'):
            return True

        # Signal 3: submitted too fast to be human (needs a timestamp field
        # rendered into the form, e.g. <input type="hidden" name="form_ts">)
        try:
            elapsed = time.time() - float(vals.get('form_ts', 0))
            if elapsed < 2:  # under 2s is basically impossible for a human
                return True
        except (TypeError, ValueError):
            pass

        return False


    @http.route('/create/ticket', type="http", auth="public", website=True, methods=["POST"])
    def create_ticket(self, **kw):
        # # Validate reCAPTCHA v2
        # recaptcha_response = kw.get('g-recaptcha-response')
        # if not recaptcha_response:
        #     return http.request.render('helpdesk_support_webform.form_error', {
        #         'error': 'Please check the reCAPTCHA box.'
        #     })
        #
        # secret_key = http.request.env['ir.config_parameter'].sudo().get_param('recaptcha_private_key')
        # if not secret_key:
        #     return http.request.render('helpdesk_support_webform.form_error', {
        #         'error': 'reCAPTCHA configuration missing. Please contact the administrator.'
        #     })
        #
        # # Verify reCAPTCHA with Google
        # response = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
        #     'secret': secret_key,
        #     'response': recaptcha_response
        # })
        # result = response.json()
        #
        # if not result.get('success', False):
        #     return http.request.render('helpdesk_support_webform.form_error', {
        #         'error': 'reCAPTCHA verification failed. Please try again.'
        #     })

        # Original controller logic
        kw.pop("followers", None)
        kw.pop("g-recaptcha-response", None)
        kw.pop("attachments", None)
        ticket_phone = kw['user_phone_number']
        ticket_email = kw['partner_email']
        kw['tag_ids'] = [kw['ticket_type_id']]

        if self._looks_like_bot(kw):
            return request.render('helpdesk_support_webform.form_thanks')
        
        kw.pop("website", None)
        kw.pop("form_ts", None)
        new_ticket = request.env['helpdesk.ticket'].sudo().create(kw)

        ticket_owner = request.env['res.partner'].sudo().search(
            [('email', '=', ticket_email)])
        ticket_owner.phone = ticket_phone

        template_id = request.env.ref(
            'helpdesk_support_webform.new_webform_ticket_email_template').id
        template = request.env['mail.template'].sudo().browse(template_id)
        template.send_mail(new_ticket.id, force_send=True)

        if 'followers' in request.params:
            raw_emails = request.httprequest.form.get('followers').split(',')
            emails = [user.strip() for user in raw_emails if user.strip() and user.strip().lower() != "alert@gitlab.erpsoftapp.com"]

            for email in emails:
                follower = request.env['res.partner'].sudo().search(
                    [('email', '=', email)], limit=1)
                if bool(follower):
                    new_ticket.message_subscribe(follower.ids)
                else:
                    message = "TO DO: Add {} to the system and make the user a follower of this ticket".format(email)
                    new_ticket.message_post(body=message)

            all_followers = [
                user.email for user in new_ticket.message_partner_ids if user.email if user.email != new_ticket.email_cc]
            follower_ticket_template_id = request.env.ref(
                'helpdesk_support_webform.follower_webform_ticket_email_template').id
            follower_ticket_template = request.env['mail.template'].sudo().browse(
                follower_ticket_template_id)
            follower_ticket_template.write(
                {'email_to': ','.join(all_followers)})
            follower_ticket_template.send_mail(
                new_ticket.id, force_send=True)

        if 'attachments' in request.params:
            attached_files = request.httprequest.files.getlist('attachments')
            for attachment in attached_files:
                if attachment.filename == "":
                    continue
                attached_file = attachment.read()
                request.env['ir.attachment'].sudo().create({
                    'name': attachment.filename,
                    'res_model': 'helpdesk.ticket',
                    'res_id': new_ticket.id,
                    'type': 'binary',
                    'store_fname': attachment.filename,
                    'datas': base64.b64encode(attached_file),
                })

        return request.render('helpdesk_support_webform.form_thanks')
