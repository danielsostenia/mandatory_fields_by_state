from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        for order in self:
            self.env["mandatory.fields.rule"].validate_record_for_state(order, "confirmed")
        return super().action_confirm()
