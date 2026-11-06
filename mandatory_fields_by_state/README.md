# Mandatory Fields by Document State (Odoo 18)

Forces required fields before a document is confirmed or posted, solving a common gap in standard Odoo.

## Problem solved
Users can confirm/post documents while key information is missing, such as:
- vendor reference
- delivery date
- analytic account
- responsible user

## Key features
- Configure rules per:
  - **Model**: `sale.order`, `purchase.order`, `account.move`
  - **Mandatory fields**, picked from the fields of that model
  - **Apply on**: optional domain limiting the documents covered by the rule
  - **Custom error message**
- Validation is triggered on:
  - Sales Order: confirm
  - Purchase Order: confirm
  - Invoice/Journal Entry: every posting (`_post`), including reversals

## Configuration
1. Enable developer mode (required: the menu is under Settings > Technical).
2. Add yourself to the **Mandatory Fields Manager** group.
3. Go to **Settings > Technical > Mandatory Fields > Rules** and create a rule.

On `account.move`, keep the suggested domain unless you really want to cover every journal entry: bank statements, POS closing and stock valuation also post through this model.

## Automated flows
By default rules are skipped in superuser mode (scheduled actions, online payments, stock valuation, custom code using `sudo()`), so a missing field cannot interrupt a flow nobody is watching. Enable **Enforce on Automated Flows** on a rule to apply it there too.

## Usage
- Users proceed normally.
- On confirm/post, the module blocks the action if any configured field is missing and shows an error.

## Upgrading from 1.0
- Rules set to `draft` or `done` were never enforced: they are archived.
- `field_names` is converted to the new field list; unknown names are dropped and logged.
- Validation of `account.move` now also runs outside `action_post`, so review existing rules on it and add a domain where needed.

## Odoo Apps page assets
- `static/description/index.html` (module description)
- `static/description/icon.png` (module icon)
