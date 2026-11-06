from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        self.env["mandatory.fields.rule"]._validate_records(self)
        return super().button_confirm()
