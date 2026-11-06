from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        # _post, not action_post: reversals, auto-post and other core flows call it directly.
        to_check = self.filtered(lambda move: move.state == "draft")
        if soft:
            # Soft posting only schedules future-dated moves, it does not post them.
            today = fields.Date.context_today(self)
            to_check = to_check.filtered(lambda move: move.date <= today)
        self.env["mandatory.fields.rule"]._validate_records(to_check)
        return super()._post(soft=soft)
