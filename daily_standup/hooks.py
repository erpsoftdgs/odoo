# -*- coding: utf-8 -*-
import logging
from odoo import api

_logger = logging.getLogger(__name__)


def post_load():
    """Executed after all modules are loaded."""
    def _update_after_registry(env):
        model_name = 'business.analyst'
        if model_name not in env.registry:
            _logger.warning(f"Model {model_name} not found — skipping barcode sync.")
            return
        analysts = env[model_name].search([])
        for record in analysts:
            record.barcode = record.name
        _logger.info(f"Synced {len(analysts)} {model_name} records successfully.")

    # Schedule it to run once the registry and env are ready
    @api.model
    def _run_post_load_sync(env):
        try:
            _update_after_registry(env)
        except Exception as e:
            _logger.exception(f"Error during delayed sync: {e}")
