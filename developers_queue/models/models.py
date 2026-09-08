import logging
from datetime import datetime

from odoo import models, fields

_logger = logging.getLogger(__name__)


class DeveloperAudit(models.Model):
    _name = 'developer.audit'
    _description = 'Developer Audit'

    name = fields.Char("Developer's Name", required=True, readonly=True)
    date = fields.Date(required=True, readonly=True, default=fields.Date.today())
    time = fields.Datetime(required=True, readonly=True, default=fields.Datetime.now())
    display_time = fields.Char(compute="_compute_display_time")

    def _compute_display_time(self):
        for rec in self:
            d = fields.Datetime.to_string(rec.time)
            # _logger.info('Time %s', d.split(' ')[1][0:5])
            d = datetime.strptime(d.split(' ')[1][0:5], "%H:%M")
            rec.display_time = d.strftime("%I:%M %p")
