# Mandatory Fields by Document State (Odoo 18)

Forces required fields depending on a document “state” (e.g., before confirming / posting), solving a common gap in standard Odoo.

## Problem solved
Users can confirm/post documents while key information is missing, such as:
- vendor reference
- delivery date
- analytic account
- responsible user

## Key features (MVP)
- Configure rules per:
  - **Model**: `sale.order`, `purchase.order`, `account.move`
  - **State key**: `draft`, `confirmed`, `done` (MVP mapping to actual transitions)
  - **Mandatory field technical names** (comma-separated)
  - **Custom error message**
- Validation is triggered on:
  - Sales Order: confirm
  - Purchase Order: confirm
  - Invoice/Journal Entry: post

## Configuration
1. Enable developer mode (recommended).
2. Go to **Mandatory Fields → Rules**.
3. Create a rule:
   - Select **Model**
   - Select **State**
   - Fill **Mandatory Field Names** (technical names)

## Usage
- Users proceed normally.
- On confirm/post, the module blocks the action if any configured fields are missing and shows an error.

## Odoo Apps page assets
- `static/description/index.html` (module description)
- `static/description/icon.png` (module icon)

## Notes / limitations
- MVP uses comma-separated technical field names.
- Extendable to a field picker UI (`ir.model.fields`) if needed.
