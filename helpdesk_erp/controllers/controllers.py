# -*- coding: utf-8 -*-
import re
from odoo import http, SUPERUSER_ID
from ..models.lab import LabModel
import json
import logging

TRIGGER = 'c4348140c3323fdfa0bb1ed5fa7533'

logger = logging.getLogger(__name__)


class GitlabBase(http.Controller):

    def message_technical(self, message):
        user = http.request.env['res.users'].sudo().browse(SUPERUSER_ID)
        logger.info('Creating message : %s ' % (message))
        http.request.env['mail.message'] \
            .sudo().create({'email_from': user.partner_id.email,
                            'author_id': user.partner_id.id, 'model': 'mail.channel',
                            'subtype_id': http.request.env.ref('mail.mt_comment').id,
                            'body': message,
                            'channel_ids': [
                                (4, http.request.env.ref('helpdesk_erp.channel_all_technical').id)],
                            'res_id': http.request.env.ref('helpdesk_erp.channel_all_technical').id,
                            })

    @http.route('/gitlab/remote_development', type='json', auth='public')
    def index(self, **kw):
        data = json.loads(http.request.httprequest.data)
        if data.get('event_type') == 'merge_request':
            merge_state = data['object_attributes']['state']
            developer = data['user']['name']
            project_id = data['project']['id']
            project_name = data['project']['name']
            source = data['object_attributes']['source_branch']
            repository_url = data['repository']['url']
            logger.info('source %s', repository_url)
            version_match = re.findall(r'(1[2-9])', repository_url)
            version = version_match[0] if version_match else ''
            module_name = source.split('local_')[1]
            short_comit = data['object_attributes']['last_commit']['id'][:8]
            logger.info('Got a new merge request with state %s from developer %s with project %s ' %
                        (merge_state, developer, project_id))
            if merge_state == 'merged':
                search_params = [('technical_name', '=', module_name), ('stage_id.sequence', 'not in', [8, 9])]
                if version and int(version) > 11:
                    client_version = http.request.env['odoo.client.version'].sudo().search(
                        [('name', '=', version)], limit=1)
                    if client_version:
                        search_params.append(('team_id.client_version', '=', client_version.id))
                ticket = http.request.env['helpdesk.ticket'].sudo().search(search_params, limit=1)
#                ticket = http.request.env['helpdesk.ticket'].sudo().search(
#                    [('technical_name', '=', module_name), ('stage_id.sequence', 'not in', [8, 9])], limit=1)

                if not ticket:
                    logger.info('Could not find ticket with name %s gotten from %s ' % (module_name, source))
                    self.message_technical("A developer %s tried to merge branch %s but the ticket with technical"
                                           " name %s cannot be found.</p> Please inform the developer to use"
                                           " the proper branch name and module name" % (
                                               developer, source, module_name))
                    return 'ok'
                logger.info('Gotten ticket with name %s now writting id %s' % (ticket.name, project_id))
                ticket.write({'remote_project_id': project_id, 'remote_short_commit': short_comit})
                try:
                    ticket.merge_remote_module()
                    logger.info('Ticked %s merged to test' % (ticket.name))
                except Exception as e:
                    logger.exception('Error occured while merging')
                    self.message_technical(
                        "An error occured while moving ticket %s to correct staging environment from developer %s"
                        "from branch %s. Error %s</p> Please move module manually or tell rerun merge request on gitlab"
                        % (ticket.name, developer, source, str(e)))
            else:
                logger.warning("Got a new merge request but not doing anything with state %s from developer %s with"
                               " project %s  branch %s  " % (merge_state, developer, project_name, source))

        return "ok"

