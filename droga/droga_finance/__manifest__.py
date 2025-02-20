# -*- coding: utf-8 -*-
{
    'name': "Droga Finance",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Afomsoft Technologies",
    'website': "https://afomsoft.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Droga Finance',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'purchase', 'hr', 'resource'],

    # always loaded
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'report/withholding_report.xml',
        'report/paper_format.xml',
        'views/account_payment.xml',
        'views/account_transaction_type.xml',
        'views/account.move.xml',
        'views/payment_request.xml',
        'views/account_fiscal_year.xml',
        'views/account_journal.xml',
        'views/branch_address.xml',
        'views/account_move_crv.xml',
        'report/payment_request.xml',
        'report/account_move.xml',

        'report/account_payment.xml',
        'report/account_payment_check_printout.xml',
        'report/customer_outstanding_balance_report.xml',
        'report/payment_report.xml',
        'report/trial_balance.xml',

        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
}
