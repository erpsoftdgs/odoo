# -*- coding: utf-8 -*-

from lxml import etree
from lxml.html import builder as html

from odoo import _, api, models


class Invite(models.TransientModel):
    _inherit = 'mail.wizard.invite'

    @api.model
    def default_get(self, fields):
        result = super(Invite, self).default_get(fields)
        if self._context.get('mail_invite_follower_channel_only'):
            result['send_mail'] = False
        if 'message' not in fields:
            return result

        user_name = self.env.user.display_name
        model = result.get('res_model')
        res_id = result.get('res_id')
        if model and res_id:
            document = self.env['ir.model']._get(model).display_name
            title = self.env[model].browse(res_id).display_name
            msg_fmt = _(
                '%(user_name)s invited you to follow %(document)s document: %(title)s')

            if document == 'Helpdesk Ticket':
                url = self.env[model].browse(res_id).get_portal_url()

                if user_name and title:
                    pass

                text = msg_fmt % locals()
                message = html.DIV(
                    html.P(_('Hello,')),
                    html.P(text),
                    html.BR(),
                    html.P(html.A("View Ticket", href=url,
                                  style="background-color: #875A7B; padding: 8px 16px 8px 16px; "
                                  "text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;"))
                )

                result['message'] = etree.tostring(message)
                return result

        else:
            msg_fmt = _('%(user_name)s invited you to follow a new document.')

        text = msg_fmt % locals()
        message = html.DIV(
            html.P(_('Hello,')),
            html.P(text)
        )

        result['message'] = etree.tostring(message)
        return result
