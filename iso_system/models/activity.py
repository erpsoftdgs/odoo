import datetime
from odoo import _
from odoo.exceptions import UserError



class CreateActivityMix:

    def create_activity(self, env, model, rec_id, department_id, activity_type, days=2, sum=''):
        approver = env['iso.approver'].sudo().search([('department', '=', department_id)], limit=1)
        if approver:
            user_id = getattr(approver, activity_type).id
        else:
            raise UserError(_('Please make sure the department set has an approver on the ISO approver list.'))

        activity_type_id = env.ref("iso_system.mail_activity_data_%s_approval"%(activity_type)).id

        env['mail.activity'].sudo().create({
            'res_model_id': env.ref('iso_system.model_%s'%(model.replace('.','_'))).id,
            'res_id': rec_id,
            'user_id': user_id,
            'activity_type_id': activity_type_id ,
            'summary': "%s approval / refusal required"%(sum),
            'date_deadline': datetime.datetime.now() + datetime.timedelta(days=days),
        })
    
    @staticmethod
    def track(self, state):
        pass
    """
        if state == 'auditor':
            return self.env.ref('iso_system.mt_auditor_state_change')
        elif state in ['compilance_mgr','compliance_mgr','comp_mgr']:
            return self.env.ref('iso_system.mt_compliance_manager_change')
        elif state == 'executive_board':
            return self.env.ref('iso_system.mt_executive_board_state_change')
        elif state == 'audited':
            return self.env.ref('iso_system.mt_audited_state_change')
        elif state == 'pass':
            return self.env.ref('iso_system.mt_external_audit_passed_state_change')
        elif state == 'team_lead':
            return self.env.ref('iso_system.mt_team_lead_state_change')
        elif state == 'project_mgr':
            return self.env.ref('iso_system.mt_project_manager_state_change')
        elif state == 'evaluation':
            return self.env.ref('iso_system.mt_evaluation_state_change')
        elif state == 'quality_mgr':
            return self.env.ref('iso_system.mt_quality_manager_change')
        elif state == 'recommendation':
            return self.env.ref('iso_system.mt_recommendation_state_change')
        elif state == 'implement':
            return self.env.ref('iso_system.mt_implement_state_change')
        elif state == 'granted':
            return self.env.ref('iso_system.mt_concession_granted_state_change')
        elif state == 'completed':
            return self.env.ref('iso_system.mt_corrective_action_completed_state_change')
        elif state == 'pm_review':
            return self.env.ref('iso_system.mt_pm_review_state_change')
        elif state == 'review_completed':
            return self.env.ref('iso_system.mt_review_completed_state_change')
        elif state == 'cmpl_review':
            return self.env.ref('iso_system.mt_cmpl_review_state_change')
        return
    """
