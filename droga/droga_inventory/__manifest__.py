# -*- coding: utf-8 -*-
{
    'name': "Droga Inventory",

    'summary': """
        Droga Pharma Pvt. Ltd.Co Inventory module extension.""",

    'description': """
        This module is developed for Droga Pharma Pvt. Ltd.Co. It works as an extension module to handle inventory operations. 
    """,

    'author': "Afomsoft Technologies",
    'website': "https://afomsoft.com",

    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': 'Inventory',
    'version': '1.0',

    # always loaded
    'data': [
        'security/security.xml',
        'views/module_menus.xml',
        'data/droga_inv_sequence.xml',
        'security/ir.model.access.csv',
        'views/droga_stock_transfer_custom.xml',
        'views/pharma_prod_categ.xml',
        'views/droga_stock_consignment_receipt.xml',
        'views/droga_stock_consignment_issue.xml',
        'views/droga_stock_extensions.xml',
        'views/droga_stock_product_extension.xml',
        'views/droga_stock_office_supplies_request.xml',
        'views/stock_res_users.xml',
        'views/reservation_list.xml',
        'views/droga_header_footer_template.xml',
        'views/droga_landed_cost.xml',
        'views/lock_period_views.xml',
        'views/stock_out_history.xml',
        'views/stock_valuation_finance_view.xml',
        'report/report_tree_extension.xml',
        'report/stock_adjustment_request_report.xml',
        'report/xls_stock_card.xml',
        'report/stock_take.xml',
        'report/cons_report.xml',
        'report/store_request.xml',
        'views/droga_stock_adjustment_request_view.xml',
        'views/droga_inv_trans_types.xml'
    ],

    # any module necessary for this one to work correctly

    'depends': ['base',
                'mail','stock',
                'resource', 'droga_procurement',
                'web', 'crm'],
    "license": "AGPL-3",
    # only loaded in demonstration mode
    'installable': True,
    'application': True
}
