# -*- coding: utf-8 -*-
{
    'name': "Droga Sales",

    'summary': """
        Droga Pharma Pvt. Ltd.Co Sales extension module.""",

    'description': """
        This module is developed for Droga Pharma Pvt. Ltd.Co. It works as an extension for sales module.
    """,

    'author': "Afomsoft Technologies",
    'website': "https://afomsoft.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'resource', 'stock', 'sale','sales_team', 'sale_stock', 'droga_crm', 'droga_inventory', 'uom',
                'hr'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'reports/sales_costing_excel_report.xml',
        'views/account_move.xml',
        'views/sale_order_extend.xml',
        'views/credit_limit.xml',
        'views/sales_discount_rules.xml',
        'views/extensions.xml',
        'views/employee.xml',
        'views/droga_header_footer_template.xml',
        'reports/sales_attachment.xml',
        'reports/daily_sales.xml',
        'reports/request_report.xml',
        'reports/account_form_readonly.xml',
        'views/module_menus.xml',
        'reports/sales_detail.xml',
        'reports/sales_detail_waiter.xml',
        'reports/sales_summary.xml',
        'wizard/sales_report_view.xml',
        'views/profit_margin.xml',
        'views/account_move_origin.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    "assets": {
        "web.assets_backend": [
             'droga_sales/static/src/js/*.js',
             'droga_sales/static/src/xml/*.xml',
        ],

    },

    'installable': True,
    'application': True,

}
