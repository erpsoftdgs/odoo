from . import models
from odoo.api import Environment, SUPERUSER_ID

ALL_MODELS = ['iso.system.audit.internal','iso.system.audit.external', 'iso.non.conformity.request',
              'iso.system.evaluation','iso.system.recommedation',  'iso.system.concessions.request',
               'iso.system.corrective.action', 'iso.system.project.manager', 'iso.system.executive.board', 'iso.system.compliance.manager']
SUBTYPE_NAMES = ['Team Lead','Project Manager', 'Auditor', 'Quality Manager', 'Compliance Manager', 'Executive Board', 'Evaluation',
                 'Recommendation', 'Implement', 'Concession Granted', 'Corrective Action Completed', 'Audited', 'External Audit Passed',
                  'PM Review', 'CMPL Review', 'Review Completed']
def post_init_hook(env):
    for sub in SUBTYPE_NAMES:
        for md in ALL_MODELS:
           env['mail.message.subtype'].create({'name':sub, 'default': False, 'res_model': md})
    # do your checks and insertion here

# def uninstall_hook(cr,):
#     env =  Environment(cr, SUPERUSER_ID, {})
#     env['mail.message.subtype'].search([('res_model', 'in', ALL_MODELS)]).unlink()
def uninstall_hook(env):
    env['mail.message.subtype'].search([('res_model', 'in', ALL_MODELS)]).unlink()