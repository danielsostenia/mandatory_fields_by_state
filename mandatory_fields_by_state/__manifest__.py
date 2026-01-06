{
    "name": "Mandatory Fields by Document State",
    "summary": "Require fields depending on document state for Sales, Purchase and Invoices.",
    "version": "18.0.1.0.0",
    "category": "Operations",
    "license": "OPL-1",
    "author": "Daniel B",
    "depends": ["base", "sale", "purchase", "account"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/mandatory_fields_rule_views.xml",
    ],
    'price': 45,
    'currency': "EUR",
    "installable": True,
    "application": False,
}

