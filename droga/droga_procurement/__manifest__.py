# -*- coding: utf-8 -*-
{
    'name': "Droga Procurement",

    'summary': """
       Local and Foreign Purchase Management""",

    'description': """
        Local and Foreign Purchase Management
    """,

    'author': "Afomsoft Technologies",
    'website': "https://afomsoft.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory/Purchase',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'stock', 'hr', 'web_studio', 'droga_finance'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/procurement_security.xml',
        'views/purchase_order.xml',
        'views/pre_import_permit.xml',
        'views/rfq.xml',
        'views/rfq_local.xml',
        'views/purchase_request.xml',
        'views/purchase_request_local.xml',

        'views/market_analysis_and_competitors.xml',
        'views/purchase_foregin_status.xml',
        'views/lc.xml',
        'views/foreign_currency_request.xml',
        'views/configuration.xml',
        'views/competitors.xml',
        'views/estimated_landed_cost.xml',
        'report/paper_format.xml',
        'report/purchase_request.xml',
        'report/purchase_request_local.xml',
        'report/purchase_request_foreign.xml',
        'report/rfq.xml',
        'report/rfq_local.xml',
        'report/purchase_order.xml',
        'report/estimated_landed_cost.xml',
        'report/procurement_lead_time.xml',
        'data/mail_template.xml',
        'views/menu.xml',
        'report/purchase_items_list.xml',
        'report/purchase_report.xml'

    ],
    # only loaded in demonstration mode
    'demo': [

    ],

    'installable': True,
    'application': True,
}
