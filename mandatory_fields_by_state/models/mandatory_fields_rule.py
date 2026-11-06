import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

SUPPORTED_MODELS = ("sale.order", "purchase.order", "account.move")


class MandatoryFieldsRule(models.Model):
    _name = "mandatory.fields.rule"
    _description = "Mandatory Fields Rule"
    _order = "model_id, id"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)

    model_id = fields.Many2one(
        "ir.model",
        required=True,
        domain=[("model", "in", SUPPORTED_MODELS)],
        ondelete="cascade",
    )
    model = fields.Char(string="Model Name", related="model_id.model", store=True, readonly=True)

    field_ids = fields.Many2many(
        "ir.model.fields",
        string="Mandatory Fields",
        required=True,
        domain="[('model_id', '=', model_id)]",
        help="Fields that must be filled in before the document is confirmed or posted.",
    )

    filter_domain = fields.Char(
        string="Apply On",
        default="[]",
        help="The rule only applies to documents matching this domain. "
        "Every kind of journal entry is posted through account.move, so "
        "rules on that model should normally be limited, for example to invoices.",
    )

    enforce_on_automated = fields.Boolean(
        string="Enforce on Automated Flows",
        help="By default the rule is skipped when the document is processed in "
        "superuser mode (scheduled actions, online payments, stock valuation, "
        "and any custom code using sudo()). Enable to enforce it there too; "
        "a missing field then interrupts that flow.",
    )

    error_message = fields.Char(
        default="Please fill in all mandatory fields before confirming/posting.",
        help="Shown when validation fails.",
    )

    @api.onchange("model_id")
    def _onchange_model_id(self):
        self.field_ids = False
        if self.model == "account.move" and self.filter_domain in (False, "", "[]"):
            self.filter_domain = "[('move_type', '!=', 'entry')]"

    @api.constrains("field_ids", "model_id")
    def _check_field_ids(self):
        for rule in self:
            foreign = rule.sudo().field_ids.filtered(lambda f: f.model_id != rule.model_id)
            if foreign:
                raise ValidationError(
                    _("Field(s) %(fields)s do not belong to model %(model)s.")
                    % {"fields": ", ".join(foreign.mapped("name")), "model": rule.model}
                )

    @api.constrains("filter_domain", "model_id")
    def _check_filter_domain(self):
        for rule in self:
            try:
                # _search builds the query without running it.
                self.env[rule.model].sudo()._search(rule._get_filter_domain())
            except (ValueError, KeyError, TypeError) as e:
                raise ValidationError(
                    _("Invalid domain on rule %(rule)s: %(error)s")
                    % {"rule": rule.name, "error": e}
                ) from e

    def _get_filter_domain(self):
        self.ensure_one()
        return safe_eval(
            self.filter_domain or "[]",
            {"uid": self.env.uid, "user": self.env.user},
        )

    def _applies_to(self, record):
        """A domain broken after saving (e.g. field removed) must not block documents."""
        self.ensure_one()
        try:
            return bool(record.filtered_domain(self._get_filter_domain()))
        except (ValueError, KeyError, TypeError):
            _logger.warning(
                "Ignoring mandatory fields rule %s: invalid domain %r",
                self.id,
                self.filter_domain,
                exc_info=True,
            )
            return False

    @api.model
    def _validate_records(self, records):
        """Raise if any of ``records`` misses a field required by an applicable rule.

        Users running this need no access to the rules, to ``ir.model.fields``
        or to the checked fields themselves, hence the sudo().
        """
        if not records:
            return
        domain = [("model", "=", records._name)]
        if self.env.su:
            domain.append(("enforce_on_automated", "=", True))
        rules = self.sudo().search(domain)
        if not rules:
            return

        for record in records.sudo():
            applicable = rules.filtered(lambda rule: rule._applies_to(record))
            missing = set()
            for fname in applicable.field_ids.mapped("name"):
                val = record[fname]
                if val in (False, None, "", []):
                    missing.add(fname)
                elif hasattr(val, "ids") and not val.ids:
                    missing.add(fname)

            if missing:
                labels = [record._fields[fname].string or fname for fname in sorted(missing)]
                base_msg = applicable[:1].error_message or _("Please fill in all mandatory fields.")
                raise ValidationError("%s\n\n%s: %s" % (base_msg, _("Missing"), ", ".join(labels)))
