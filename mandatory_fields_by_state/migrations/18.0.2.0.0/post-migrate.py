import logging

from odoo import SUPERUSER_ID, api
from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    table = "mandatory_fields_rule"

    # Only "confirmed" rules were ever enforced: keep the others from starting now.
    if column_exists(cr, table, "state"):
        cr.execute(f"UPDATE {table} SET active = FALSE WHERE state != 'confirmed' AND active")
        if cr.rowcount:
            _logger.warning("Archived %s rule(s) that were never enforced (draft/done).", cr.rowcount)

    if not column_exists(cr, table, "field_names"):
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute(f"SELECT id, field_names FROM {table} WHERE field_names IS NOT NULL")
    for rule_id, field_names in cr.fetchall():
        rule = env["mandatory.fields.rule"].browse(rule_id)
        names = {name.strip() for name in field_names.split(",") if name.strip()}
        rule_fields = env["ir.model.fields"].search(
            [("model_id", "=", rule.model_id.id), ("name", "in", list(names))]
        )
        rule.field_ids = [(6, 0, rule_fields.ids)]
        unknown = names - set(rule_fields.mapped("name"))
        if unknown:
            _logger.warning("Rule %s: dropped unknown field(s) %s", rule_id, sorted(unknown))
