# from msilib import sequence
import threading
import json
import os
import base64
import logging
import shutil
import subprocess
from odoo import models, fields, registry, api, _
from odoo.exceptions import UserError, ValidationError

logger = logging.getLogger(__name__)

OD00_VERSIONS = [('11', 'Odoo 11'), ('12', 'Odoo 12'), ('13', 'Odoo 13'),
                 ('14', 'Odoo 14'), ('15', 'Odoo 15'), ('16', 'Odoo 16'),
                 ('17', 'Odoo 17'), ('18', 'Odoo 18'), ('19', 'Odoo 19'), ('20', 'Odoo 20')]


def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""

    # from whichcraft import which
    from shutil import which

    return which(name) is not None


class TestRunner:

    def clean_dir(self, ticket_name):
        file_p = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        dir_fil = os.path.join(file_p, '../data/tests/', ticket_name)
        try:
            shutil.rmtree(dir_fil)
        except OSError as e:
            logger.exception(e)

    def run_regression_check(self, ticket_name, tool_check=False):
        if not self.selenium_ide_script:
            raise UserError(_("Please upload your selenium .side regression file."))
        if tool_check and not is_tool('selenium-side-runner'):
            raise UserError(_('Selenium side runner is not installed please contact support'))
        if not ticket_name:
            raise UserError(_('Please set ticket technical name'))

    @api.model
    def _run_regression_test(self, ticket_name, test_ticket_id=None, host_url=None):
        ticket_name = ticket_name.replace(' ', '-')
        with api.Environment.manage():
            # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
            new_cr = self.pool.cursor()
            new_cr.autocommit(True)
            self = self.with_env(self.env(cr=new_cr))
            self.run_regression_check(ticket_name, False)
            file_p = os.path.join(os.path.dirname(os.path.abspath(__file__)))
            dir_fil = os.path.join(file_p, '../data/tests/', ticket_name)
            if not os.path.exists(dir_fil):
                os.makedirs(dir_fil)
            file_con = base64.b64decode(self.selenium_ide_script).decode()
            file_con = json.loads(file_con)

            if host_url:
                file_con['url'] = host_url
                file_con['urls'] = [host_url]
                file_con = json.dumps(file_con)
            result_name = file_con['name']
            file_con = json.dumps(file_con)
            print(file_con)
            side_file = os.path.join(dir_fil, '{}.side'.format(ticket_name))
            with open(side_file, 'w') as f:
                f.write(file_con)
            # yaml_conf = """
            # capabilities:
            #     browserName: "chrome"
            # baseUrl: "{}"
            # server: "{}"
            # """.format(host_url, self.env.user.company_id.selenium_grid_server)
            # print(side_file)
            side_runner = self.env.user.company_id.selenium_ide_runner_location
            run = [side_runner, '--debug', '--no-sideyml', '--server', self.env.user.company_id.selenium_grid_server,
                   side_file, "-c", '"browserName=\'chrome\' goog:chromeOptions.args=[disable-infobars, headless]"',
                   "--output-directory={}".format(dir_fil)]
            logger.info("Running command")
            print(' '.join(run))
            print(os.path.join(dir_fil, '{}.json'.format(result_name)))
            result = subprocess.run(' '.join(run), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    cwd=dir_fil)
            p = result.stdout
            logger.info("Got res %s", p)
            logger.info("Got error %s", result.stderr)
            side_res = os.path.join(dir_fil, '{}.json'.format(result_name))
            # elf.write({'selenium_cmd_res': result})
            print(side_res)
            if not os.path.exists(side_res):
                self.message_post(body=_('Ran selenium test but cannot get result file. please contact support'))
                print('Ran selenium test but cannot get result file. please contact support')
            else:
                with open(side_res) as f:
                    res = json.load(f)
                    srt = json.dumps(res)
                    logger.info("Res %s  ", srt)
                    self.selenium_test_res = json.dumps(res)
                    # self.write({'selenium_test_res': json.dumps(res)})
                    test_ticket = self.env['helpdesk.test.script'].sudo().search([('id', '=', test_ticket_id)], limit=1)
                    if res["numFailedTestSuites"] > 0:
                        logger.info("Failed Test")
                        if test_ticket:
                            test_ticket.message_post(body=_('Selenium regression test %s failed'
                                                            '  please check test result') % self.name)
                            test_ticket.failed_tester()
                        else:
                            self.message_post(body=_('Selenium test failed please check test result'))
                            self.failed_tester()
                    else:
                        if test_ticket:
                            test_ticket.move_to_first_testing()
                        else:
                            self.move_to_first_testing()
            self.clean_dir(ticket_name)
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
            self._cr.commit()
            self._cr.close()
            new_cr.close()


class ResCompany(models.Model):
    _inherit = 'res.company'

    selenium_regression_test = fields.Boolean(string='Run Selenium Test')
    selenium_grid_server = fields.Char()
    selenium_ide_runner_location = fields.Char(default='selenium-side-runner')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    selenium_regression_test = fields.Boolean(readonly=False, related='company_id.selenium_regression_test',
                                              string='Run Selenium Test')
    selenium_grid_server = fields.Char(readonly=False, related='company_id.selenium_grid_server')
    selenium_ide_runner_location = fields.Char(readonly=False, related='company_id.selenium_ide_runner_location')


class HelpdesTick(models.Model):
    _inherit = 'helpdesk.ticket'

    odoo_supported_version = fields.Selection(OD00_VERSIONS, default='18')

    def test_failed(self):
        scr = self.env['helpdesk.test.script'].search([('customization_ticket_id', '=', self.id)], limit=1)
        if not scr or (scr and scr.state != 'failed'):
            raise UserError(_("Please Use Helpdesk Test Repository before running this."))
        return super(HelpdesTick, self).test_failed()

    def test_completed(self):
        scr = self.env['helpdesk.test.script'].search([('customization_ticket_id', '=', self.id)], limit=1)
#        if not scr or (scr and scr.state != 'done'):
#            raise UserError(_("Please Use Helpdesk Test Repository before running this."))
        return super(HelpdesTick, self).test_completed()

    def complete_development(self, force=False):
        if force and self.env.user.company_id.selenium_regression_test:
            scr = self.env['helpdesk.test.script'].search([('customization_ticket_id', '=', self.id)], limit=1)
            # if there is a  test and script and regression file has been uploaded before perform regression test
            if scr.selenium_ide_script:
                scr.run_regression_test()
        return super(HelpdesTick, self).complete_development(force=force)


class TestScriptTags(models.Model):
    _name = 'helpdesk.test.tags'
    _description = 'Test Tags'

    name = fields.Char()


class TestScripts(models.Model, TestRunner):
    _name = 'helpdesk.test.script'
    _description = 'Test Script'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Test Script ID", readonly=True)
    description = fields.Char()
    module_id = fields.Many2one("ir.module.module")
    client_id = fields.Many2one('helpdesk.team')
    customization_ticket_id = fields.Many2one('helpdesk.ticket', require=True)
    odoo_supported_version = fields.Selection(OD00_VERSIONS, default='18')
    created_by_id = fields.Many2one('res.users', default=lambda self: self.env.user.id)
    project_manager_id = fields.Many2one('hr.employee')
    test_tags_id = fields.Many2many('helpdesk.test.tags')
    selenium_untested = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='yes')
    created_on = fields.Datetime(default=fields.Datetime.now)
    selenium_ide_script = fields.Binary()
    selenium_cmd_res = fields.Text()
    selenium_test_res = fields.Text(copy=False)
    first_level_tester_id = fields.Many2one('hr.employee')
    second_level_tester_id = fields.Many2one('hr.employee')
    team_lead_id = fields.Many2one('hr.employee')
    test_case_line = fields.One2many('helpdesk.test.case', 'test_script_id', 'Test Case', copy=True)
    test_db_line = fields.One2many('helpdesk.test.db', 'test_script_id', 'Test Case',copy=True)
    # test_regression_line = fields.One2many('helpdesk.test.case.regression', 'test_script_id', 'Test Regression',
    #                                       copy=True)
    regression_ids = fields.Many2many('helpdesk.test.regression')
    state = fields.Selection(
        [('regression_level_testing', 'Regression TESTING'),
         ('first_level_testing', 'FIRST LEVEL TESTING'), ('second_level_testing', 'SECOND LEVEL TESTING'),
         ('team_lead', 'TEAM LEAD'), ('done', 'Done'),
         ('failed', 'Failed'), ('rejected', 'Rejected')],
        default='first_level_testing',
        string="Status", track_visibility="onchange")
    active = fields.Boolean(default=True)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('helpdesk.test.script')
        if 'first_level_tester_id' in vals:
            fld = int(vals['first_level_tester_id'])
            employee = self.env['hr.employee'].sudo().search([('id', '=', fld)], limit=1)
            self.message_subscribe(partner_ids=employee.user_partner_id.ids)
        res = super(TestScripts, self).create(vals)
        return res

    def unlink(self):
        raise ValidationError(_("You are not authorized to delete a record. Contact administrator!"))

    def _get_client_test_url(self):
        if self.client_id.client_test_url and self.test_db_line:
            db_line = self.test_db_line[0]
            url = self.client_id.client_test_url
            if '@' in url:
                half_url = url.split('@')[1]
                half_url = half_url.split(':')[0]
                url = 'https://{}/web?db={}'.format(half_url, db_line.db)
                logger.info("Automatically detected url %s from client %s  for ticket %s", url, self.client_id.name,
                            self.name)
                return url

    def run_regression_test(self):
        self.write({'state': 'regression_level_testing', 'selenium_untested': 'no'})
        host_url = self._get_client_test_url()
        threaded_calculation = threading.Thread(target=self._run_regression_test,
                                                args=(self.customization_ticket_id.technical_name,),
                                                kwargs={'host_url': host_url})
        threaded_calculation.start()
        for r in self.regression_ids:
            if r.selenium_test_suite_name and r.state == 'passed':
                r.run_regression_test(self.id, host_url)
        # self._run_regression_test()

    def failed_ticket_test(self):
        self.customization_ticket_id.issue_sheet_url_link = 'https'
        self.customization_ticket_id.tested_by_user = self.first_level_tester_id.user_id
        self.customization_ticket_id.test_failed()

    def reset_to_draft(self):
        return self.write({'state': 'first_level_testing'})

    def move_to_first_testing(self):
        if self.first_level_tester_id:
            self.message_subscribe(partner_ids=self.first_level_tester_id.user_partner_id.ids)
        return self.write({'state': 'first_level_testing'})

    def passed_first_tester(self):
        if self.second_level_tester_id:
            self.message_subscribe(partner_ids=self.second_level_tester_id.user_partner_id.ids)
        self.run_regression_check(self.customization_ticket_id.technical_name)
        return self.write({'state': 'second_level_testing'})

    def failed_tester(self):
        # self.failed_ticket_test() let user fill manually
        return self.write({'state': 'failed'})

    def passed_second_tester(self):
        if self.team_lead_id:
            self.message_subscribe(partner_ids=self.team_lead_id.user_partner_id.ids)
        return self.write({'state': 'team_lead'})

    def approved_test(self):

        return self.write({'state': 'done'})

    def approved_reject(self):
        return self.write({'state': 'rejected'})

    def get_test_regression_tags(self):
        regressions = self.env['helpdesk.test.regression'].sudo(). \
            search([('test_tags_id', 'in', self.test_tags_id.ids),
                    ('odoo_supported_version', '=', self.odoo_supported_version)])
        return regressions

    def populate(self):
        regs = self.env['helpdesk.test.regression'].sudo(). \
            search([('client_id', '=', self.client_id.id),
                    ('module_id', '=', self.module_id.id),
                    ('odoo_supported_version', '=', self.odoo_supported_version)])
        # self.test_regression_line.unlink()
        lines = []
        self.write({'regression_ids': regs.ids + self.get_test_regression_tags().ids})
        # for rec in regs.test_regression_line:
        #    lines.append((0, 0, {'expected_result': rec.expected_result, 'test_steps': rec.test_steps,
        #                         'state': rec.state}))
        # self.write({'test_regression_line': lines})

    @api.onchange('client_id')
    def _get_customization_ticket_domain(self):
        # Get tickets on development completed
        res = self.env['helpdesk.ticket'].sudo(). \
            search([('stage_id.sequence', 'in', [7, 2]), ('team_id', '=', self.client_id.id)])
        return {'domain': {'customization_ticket_id': [('id', 'in', res.ids)]}}

    @api.onchange('team_lead_id')
    def _get_team_lead_id_domain(self):
        hrs = self.env['hr.employee'].sudo().search([])
        hr_em = hrs.filtered(lambda r: r.user_id and r.user_id.has_group('helpdesk_erp.group_helpdesk_team_manager'))
        return {'domain': {'team_lead_id': [('id', 'in', hr_em.ids)]}}


class TestCase(models.Model):
    _name = 'helpdesk.test.case'
    _description = 'Test Case'

    test_script_id = fields.Many2one('helpdesk.test.script')
    tr_id = fields.Char(string='TR ID')
    tr_description = fields.Char(string='TR Description')
    tc_id = fields.Char(string='TC ID', readonly=True)
    test_cases = fields.Char()
    test_steps = fields.Text()
    expected_result = fields.Text()
    actual_result = fields.Text()
    state = fields.Selection([('untested', 'Untested'),
                              ('failed', 'Failed'), ('passed', 'Passed')], default='untested', required=True)
    sequence = fields.Integer()
    test_data = fields.Text()

    @api.model
    def create(self, vals):
        vals['tc_id'] = self.env['ir.sequence'].next_by_code('helpdesk.test.case')

        res = super(TestCase, self).create(vals)
        return res


class TestDB(models.Model):
    _name = 'helpdesk.test.db'
    _description = 'Test DB'

    test_script_id = fields.Many2one('helpdesk.test.script')
    db = fields.Char(string='DB', required=True)
    test_user = fields.Char(required=True)


class TestCaseRegression(models.Model):
    _name = 'helpdesk.test.case.regression'
    _description = 'Test Regression'

    test_script_id = fields.Many2one('helpdesk.test.script')
    expected_result = fields.Text(readonly=True)
    test_steps = fields.Text(readonly=True)


class TestRegression(models.Model, TestRunner):
    _name = 'helpdesk.test.regression'
    _description = 'Test Regression'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Regression ID", readonly=True)
    module_id = fields.Many2one("ir.module.module")
    client_id = fields.Many2one('helpdesk.team')
    selenium_ide_script = fields.Binary()
    test_tags_id = fields.Many2many('helpdesk.test.tags')
    selenium_cmd_res = fields.Text()
    selenium_test_res = fields.Text(copy=False)
    selenium_test_suite_name = fields.Char()
    odoo_supported_version = fields.Selection(OD00_VERSIONS, default='18')
    created_by_id = fields.Many2one('res.users', default=lambda self: self.env.user.id)
    test_regression_line = fields.One2many('helpdesk.regression.line', 'test_regression_id', 'Test Regression Line',
                                           copy=True)
    state = fields.Selection(
        [('untested', 'Untested'), ('running_test', 'Running Test'), ('failed', 'Failed'), ('passed', 'Passed')],
        string='Status', default='untested', copy=False)
    active = fields.Boolean(default=True)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('helpdesk.test.regression')
        res = super(TestRegression, self).create(vals)
        return res

    def run_regression_test(self, test_id=None, host_url=None):
        self.write({'state': 'running_test'})
        if not self.selenium_test_suite_name:
            raise UserError(_("Selenium test suite name must be filled"))
        threaded_calculation = threading.Thread(target=self._run_regression_test,
                                                args=(self.selenium_test_suite_name, test_id),
                                                kwargs={'host_url': host_url})
        threaded_calculation.start()

    def failed_tester(self):
        self.write({'state': 'failed'})

    def move_to_first_testing(self):
        self.write({'state': 'passed'})


class RegressionLine(models.Model):
    _name = 'helpdesk.regression.line'
    _description = 'Test Regression Line'

    test_regression_id = fields.Many2one('helpdesk.test.regression')
    expected_result = fields.Text()
    test_steps = fields.Text()
    state = fields.Selection([('failed', 'Failed'), ('passed', 'Passed')], string='Status')
    active = fields.Boolean(default=True)
