# -*- coding: utf-8 -*-
import logging
from datetime import date

from odoo import models, fields, api, _, exceptions

_logger = logging.getLogger(__name__)


class Strike(models.Model):
    _inherit = 'gamification.badge'
    _name = "employee.strike"
    _description = "Employee Strike"
    NOT_MANAGER = 4

    name = fields.Char('Strike', required=True, translate=True)
    penalty = fields.Char("Penalties for Strikes")
    granted_count = fields.Integer("Total", compute='_compute_get_owners_info',
                                   help="The number of time this badge has \
                                    been received.")
    stat_count = fields.Integer("Stat Count")
    granted_users_count = fields.Integer("Number of users",
                                         compute='_compute_get_owners_info',
                                         help="The number of time this badge \
                                              has been received by unique \
                                              users.")
    stat_count_distinct = fields.Integer("Users")
    unique_owner_ids = fields.Many2many(
        'res.users', string="Unique Owners",
        compute='_compute_get_owners_info',
        help="The list of unique users having received this badge.")

    # add this field, gives error for odoo 17 if not added for \
    # employee_strike_id
    goal_definition_ids = fields.Many2many(
        'gamification.goal.definition', 'badge_unlocked_definition_strike_rel',
        string='Rewarded by',
        help="The users that have succeeded these goals will receive \
             automatically the badge.")

    stat_this_month = fields.Integer(
        "Monthly total", compute='_compute_get_badge_user_stats',
        help="The number of time this badge has been received this month.")
    stat_my = fields.Integer(
        "My Total", compute='_compute_get_badge_user_stats',
        help="The number of time the current user has received this badge.")
    stat_my_this_month = fields.Integer(
        "My Monthly Total", compute='_compute_get_badge_user_stats',
        help="The number of time the current user has received this badge \
             this month.")
    stat_my_monthly_sending = fields.Integer(
        'My Monthly Sending Total',
        compute='_compute_get_badge_user_stats',
        help="The number of time the current user has sent this badge \
             this month.")
    rule_strike = fields.Selection(selection=[
        ('manager', 'Manager'),
        ('users', 'A selected list of users'),
    ], default='manager',
        string="Allowance to Issue", help="Who can issue this strike",
        required=True)

    # remaining_sending = fields.Integer(
    #     "Remaining Sending Allowed", compute='_remaining_sending_calc',
    #     help="If a maximum is set")

    rule_auth_user_ids = fields.Many2many(
        'res.users', 'badge_auth_users_rel',
        string='Authorized Users',
        help="Only these people can give this badge")

    @api.depends('owner_ids')
    def _compute_get_owners_info(self):
        """Return:
            the list of unique res.users ids having received this badge
            the total number of time this badge was granted
            the total number of users this badge was granted to
        """
        defaults = {
            'granted_count': 0,
            'granted_users_count': 0,
            'unique_owner_ids': [],
        }
        if not self.ids:
            self.update(defaults)
            return

        self.env.cr.execute("""
            SELECT strike_id, count(user_id) as granted_count,
                count(distinct(user_id)) as granted_users_count,
                array_agg(distinct(user_id)) as unique_owner_ids
            FROM employee_strike_user
            WHERE strike_id in %s
            GROUP BY strike_id
            """, [tuple(self.ids)])

        mapping = {
            strike_id: {
                'granted_count': count,
                'granted_users_count': distinct_count,
                'unique_owner_ids': owner_ids,
            }
            for (strike_id, count, distinct_count, owner_ids) in self.env.cr._obj
        }
        for badge in self:
            badge.update(mapping.get(badge.id, defaults))

    owner_ids = fields.One2many(
        'employee.strike.user', 'strike_id',
        string='Owners',
        help='The list of instances of this badge granted to users')

    rule_auth_badge_ids = fields.Many2many(
        'employee.strike', 'strike1_id', 'strike2_id',
        string='Required Badges',
        help="Only the people having these badges can give this badge")

    def get_granted_employees(self):
        employee_ids = self.mapped('owner_ids.employee_id').ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Issued Employees',
            'view_mode': 'kanban,list,form',
            'res_model': 'hr.employee.public',
            'domain': [('id', 'in', employee_ids)]
        }

    granted_employees_count = fields.Integer(compute="_compute_granted_employees_count")

    def _can_grant_badge(self):
        """Check if a user can grant a badge to another user

        :param uid: the id of the res.users trying to send the badge
        :param badge_id: the granted badge id
        :return: integer representing the permission.
        """
        # if self.env.is_admin():
        #     return self.CAN_GRANT
        if self.rule_strike == 'manager' and not self.env.user.has_group('hr.group_hr_manager'):
            return self.NOT_MANAGER
        if self.rule_strike == 'users' and self.env.user not in self.rule_auth_user_ids:
            return self.USER_NOT_VIP

        # badge.rule_strike == 'everyone' -> no check
        return self.CAN_GRANT

    @api.depends('owner_ids.strike_id', 'owner_ids.create_date', 'owner_ids.user_id')
    def _compute_get_badge_user_stats(self):
        """Return stats related to badge users"""
        first_month_day = date.today().replace(day=1)

        for badge in self:
            owners = badge.owner_ids
            badge.stat_my = sum(o.user_id == self.env.user for o in owners)
            badge.stat_this_month = sum(o.create_date.date() >= first_month_day for o in owners)
            badge.stat_my_this_month = sum(
                o.user_id == self.env.user and o.create_date.date() >= first_month_day
                for o in owners
            )
            badge.stat_my_monthly_sending = sum(
                o.create_uid == self.env.user and o.create_date.date() >= first_month_day
                for o in owners
            )

    @api.depends('owner_ids.employee_id')
    def _compute_granted_employees_count(self):
        for badge in self:
            badge.granted_employees_count = self.env['employee.strike.user'].search_count([
                ('strike_id', '=', badge.id),
                ('employee_id', '!=', False)
            ])

    def check_granting(self):
        """Check the user 'uid' can grant the badge 'badge_id' and raise the appropriate exception
        if not

        Do not check for SUPERUSER_ID
        """
        status_code = self._can_grant_badge()
        if status_code == self.CAN_GRANT:
            return True
        if status_code == self.NOT_MANAGER:
            raise exceptions.UserError(_('You are not an Admin.'))
        if status_code == self.USER_NOT_VIP:
            raise exceptions.UserError(_('You are not in the user allowed list.'))
        _logger.error("Unknown strike status code: %s", status_code)
        return False


class StrikeBadgeUser(models.Model):
    """User having received a badge"""
    _name = "employee.strike.user"
    _description = 'Strike User'
    _order = "create_date desc"
    _rec_name = "strike_name"

    badge_id = fields.Many2one('gamification.badge', string='Badge', required=False, ondelete="cascade", index=True)
    user_id = fields.Many2one('res.users', string="User", required=True, ondelete="cascade", index=True)
    sender_id = fields.Many2one('res.users', string="Sender", help="The user who has send the badge")
    comment = fields.Text('Comment')
    employee_id = fields.Many2one('hr.employee', string='Employee')

    @api.constrains('employee_id')
    def _check_employee_related_user(self):
        for badge_user in self:
            if badge_user.employee_id not in badge_user.user_id.employee_ids:
                raise exceptions.ValidationError(_('The selected employee does not correspond to the selected user.'))

    def action_open_strike(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'employee.strike',
            'view_mode': 'form',
            'res_id': self.strike_id.id,
        }

    def _send_badge(self):
        """Send a notification to a user for receiving a badge

        Does not verify constraints on badge granting.
        The users are added to the owner_ids (create badge_user if needed)
        The stats counters are incremented
        """
        template = self.env.ref(
            'employee_strikes_badge.email_template_strike_received',
            raise_if_not_found=False
        )
        if template:
            for badge_user in self:
                template.sudo().send_mail(
                    badge_user.id,
                )

        return True

    strike_id = fields.Many2one('employee.strike', string='Strike',
                                required=True, ondelete="cascade", index=True)
    strike_name = fields.Char(related='strike_id.name', string="Strike Name",
                              readonly=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self.env['employee.strike'].browse(vals['strike_id']).check_granting()
        return super(StrikeBadgeUser, self).create(vals_list)
