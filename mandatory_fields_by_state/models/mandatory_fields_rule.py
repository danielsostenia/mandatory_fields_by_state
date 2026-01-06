from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MandatoryFieldsRule(models.Model):
    _name = "mandatory.fields.rule"
    _description = "Mandatory Fields Rule (by model + state)"
    _order = "model_id, state, id"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)

    model_id = fields.Many2one(
        "ir.model",
        required=True,
        domain=[("model", "in", ("sale.order", "purchase.order", "account.move"))],
        ondelete="cascade",
    )
    model = fields.Char(related="model_id.model", store=True, readonly=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("done", "Done"),
        ],
        required=True,
        default="draft",
    )

    # MVP: comma-separated technical field names
    field_names = fields.Char(
        string="Mandatory Field Names",
        help="Comma-separated technical field names, e.g.: partner_ref,date_planned,invoice_user_id",
    )

    error_message = fields.Char(
        default="Please fill in all mandatory fields before confirming/posting.",
        help="Shown when validation fails.",
    )

    @api.constrains("field_names", "model_id")
    def _check_field_names(self):
        for rec in self:
            if not rec.field_names or not rec.model:
                continue
            model = self.env[rec.model]
            unknown = []
            for fn in [x.strip() for x in rec.field_names.split(",") if x.strip()]:
                if fn not in model._fields:
                    unknown.append(fn)
            if unknown:
                raise ValidationError(
                    _("Unknown field(s) for model %(model)s: %(fields)s")
                    % {"model": rec.model, "fields": ", ".join(unknown)}
                )

    def _get_required_field_names(self):
        self.ensure_one()
        return [x.strip() for x in (self.field_names or "").split(",") if x.strip()]

    @api.model
    def validate_record_for_state(self, record, state_key):
        rules = self.search(
            [
                ("active", "=", True),
                ("model", "=", record._name),
                ("state", "=", state_key),
            ]
        )
        if not rules:
            return True

        missing = set()
        for rule in rules:
            for fname in rule._get_required_field_names():
                val = record[fname]
                if val in (False, None, "", []):
                    missing.add(fname)
                elif hasattr(val, "ids") and not val.ids:
                    missing.add(fname)

        if missing:
            # show user-friendly labels where possible
            labels = []
            for fname in sorted(missing):
                fld = record._fields.get(fname)
                labels.append(fld.string if fld and getattr(fld, "string", False) else fname)

            base_msg = rules[:1].error_message or _("Please fill in all mandatory fields.")
            raise ValidationError("%s\n\n%s: %s" % (base_msg, _("Missing"), ", ".join(labels)))

        return True

