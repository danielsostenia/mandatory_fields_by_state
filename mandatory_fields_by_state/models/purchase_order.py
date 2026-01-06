from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        for po in self:
            self.env["mandatory.fields.rule"].validate_record_for_state(po, "confirmed")
        return super().button_confirm()
