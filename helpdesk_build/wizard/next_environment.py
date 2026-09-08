from odoo import models, fields, _


class NextEnvironmentWizard(models.TransientModel):
    _name = 'next.environment.wizard'
    _description = 'Next Environment To Build Wizard'

    build_id = fields.Many2one('system.build')
    environment_id = fields.Many2one('system.environment', string="System Environment")

    def action_next_environment(self):
        if self.build_id:
            new_build = self.build_id.copy(
                {
                    'environment_id': self.environment_id.id,
                    'name': False,
                    'copied': True,
                    'status': 'progress',
                    'date': False,
                })

            if new_build.build_type == 'multi':
                for line in self.build_id.multi_line_ids:
                    line.copy({'build_id': new_build.id})
                for line in self.build_id.multi_configuration_ids:
                    line.copy({'build_id': new_build.id})
                for line in self.build_id.multi_team_lead_check_ids:
                    line.copy({'build_id': new_build.id})
            else:
                for line in self.build_id.configuration_ids:
                    line.copy({'build_id': new_build.id})
                for line in self.build_id.team_lead_check_ids:
                    line.copy({'build_id': new_build.id})
                for line in self.build_id.line_ids:
                    line.copy({'build_id': new_build.id})

            for line in self.build_id.build_company_ids:
                line.copy({'build_id': new_build.id})

            return {
                'name': _("System Build"),
                'res_id': new_build.id,
                'view_type': 'form',
                'res_model': 'system.build',
                'view_mode': 'form,tree',
                'nodestroy': True,
                'target': 'current',
                'type': 'ir.actions.act_window',
            }
        return False
