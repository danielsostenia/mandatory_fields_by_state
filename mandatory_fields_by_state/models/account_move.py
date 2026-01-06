from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        for move in self:
            # MVP mapping: validate "confirmed" rules when posting
            self.env["mandatory.fields.rule"].validate_record_for_state(move, "confirmed")
        return super().action_post()
