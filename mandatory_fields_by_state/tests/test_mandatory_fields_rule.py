from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import Form, new_test_user, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestMandatoryFieldsRule(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.groups_id += cls.env.ref("mandatory_fields_by_state.group_mandatory_fields_manager")

    @classmethod
    def _rule(cls, model, fname, **vals):
        return cls.env["mandatory.fields.rule"].create({
            "name": f"{model} {fname}",
            "model_id": cls.env["ir.model"]._get_id(model),
            "field_ids": [(6, 0, cls.env["ir.model.fields"]._get(model, fname).ids)],
            **vals,
        })

    def _sale_order(self):
        return self.env["sale.order"].create({
            "partner_id": self.partner_a.id,
            "order_line": [(0, 0, {"product_id": self.product_a.id})],
        })

    def _purchase_order(self):
        return self.env["purchase.order"].create({
            "partner_id": self.partner_a.id,
            "order_line": [(0, 0, {"product_id": self.product_a.id})],
        })

    def _entry(self):
        account = self.company_data["default_account_revenue"]
        return self.env["account.move"].create({
            "move_type": "entry",
            "line_ids": [
                (0, 0, {"account_id": account.id, "debit": 10}),
                (0, 0, {"account_id": account.id, "credit": 10}),
            ],
        })

    def test_sale_order(self):
        self._rule("sale.order", "client_order_ref")
        order = self._sale_order()
        with self.assertRaises(ValidationError):
            order.action_confirm()
        order.client_order_ref = "REF"
        order.action_confirm()
        self.assertEqual(order.state, "sale")

    def test_purchase_order(self):
        self._rule("purchase.order", "partner_ref")
        order = self._purchase_order()
        with self.assertRaises(ValidationError):
            order.button_confirm()
        order.partner_ref = "REF"
        order.button_confirm()
        self.assertEqual(order.state, "purchase")

    def test_direct_post_is_validated(self):
        self._rule("account.move", "ref")
        invoice = self.init_invoice("out_invoice", amounts=[100])
        with self.assertRaises(ValidationError):
            invoice._post(soft=False)
        invoice.ref = "REF"
        invoice._post(soft=False)
        self.assertEqual(invoice.state, "posted")

    def test_soft_post_skips_future_moves(self):
        self._rule("account.move", "ref")
        invoice = self.init_invoice("out_invoice", amounts=[100])
        invoice.date = fields.Date.context_today(invoice) + timedelta(days=30)
        invoice._post(soft=True)
        self.assertEqual(invoice.state, "draft")

    def test_filter_domain_limits_rule(self):
        self._rule("account.move", "ref", filter_domain="[('move_type', '!=', 'entry')]")
        entry = self._entry()
        entry.action_post()
        self.assertEqual(entry.state, "posted")
        with self.assertRaises(ValidationError):
            self.init_invoice("out_invoice", amounts=[100]).action_post()

    def test_invalid_domain_rejected_on_save(self):
        with self.assertRaises(ValidationError):
            self._rule("sale.order", "client_order_ref", filter_domain="[('nope', '=', 1)]")

    def test_broken_domain_does_not_block_documents(self):
        rule = self._rule("sale.order", "client_order_ref")
        self.env.cr.execute(
            "UPDATE mandatory_fields_rule SET filter_domain = %s WHERE id = %s",
            ("[('nope', '=', 1)]", rule.id),
        )
        rule.invalidate_recordset()
        order = self._sale_order()
        with self.assertLogs("odoo.addons.mandatory_fields_by_state.models.mandatory_fields_rule", "WARNING"):
            order.action_confirm()
        self.assertEqual(order.state, "sale")

    def test_field_of_other_model_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["mandatory.fields.rule"].create({
                "name": "wrong",
                "model_id": self.env["ir.model"]._get_id("sale.order"),
                "field_ids": [(6, 0, self.env["ir.model.fields"]._get("purchase.order", "partner_ref").ids)],
            })

    def test_deleted_field_does_not_block_documents(self):
        field = self.env["ir.model.fields"].sudo().create({
            "name": "x_mandatory_test",
            "model_id": self.env["ir.model"]._get_id("sale.order"),
            "ttype": "char",
            "state": "manual",
        })
        rule = self._rule("sale.order", "x_mandatory_test")
        order = self._sale_order()
        with self.assertRaises(ValidationError):
            order.action_confirm()
        field.unlink()
        self.assertFalse(rule.field_ids)
        order.action_confirm()
        self.assertEqual(order.state, "sale")

    def test_automated_flow_skipped_by_default(self):
        self._rule("sale.order", "client_order_ref")
        order = self._sale_order()
        order.sudo().action_confirm()
        self.assertEqual(order.state, "sale")

    def test_automated_flow_enforced_on_request(self):
        self._rule("sale.order", "client_order_ref", enforce_on_automated=True)
        with self.assertRaises(ValidationError):
            self._sale_order().sudo().action_confirm()

    def test_user_without_technical_access(self):
        self._rule("sale.order", "client_order_ref")
        user = new_test_user(self.env, login="mandatory_sales", groups="sales_team.group_sale_salesman_all_leads")
        order = self._sale_order().with_user(user)
        with self.assertRaises(ValidationError):
            order.action_confirm()

    def test_form_suggests_domain_on_account_move(self):
        with Form(self.env["mandatory.fields.rule"]) as form:
            form.name = "Invoices"
            form.model_id = self.env["ir.model"]._get("account.move")
            self.assertEqual(form.filter_domain, "[('move_type', '!=', 'entry')]")
            form.field_ids.add(self.env["ir.model.fields"]._get("account.move", "ref"))

    def test_archived_rule_ignored(self):
        self._rule("sale.order", "client_order_ref", active=False)
        order = self._sale_order()
        order.action_confirm()
        self.assertEqual(order.state, "sale")
