from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        self.env["mandatory.fields.rule"]._validate_records(self)
        return super().action_confirm()
