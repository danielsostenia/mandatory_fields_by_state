{
    "name": "Mandatory Fields by Document State",
    "summary": "Require fields before confirming or posting Sales, Purchase and Invoices.",
    "version": "18.0.2.0.1",
    "category": "Operations",
    "license": "LGPL-3",
    "author": "Banica Daniel",
    "depends": ["base", "sale", "purchase", "account"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/mandatory_fields_rule_views.xml",
    ],
    'images': [
        'static/description/banner.png',
    ],
    "installable": True,
    "application": False,
}
