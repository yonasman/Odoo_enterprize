# -*- coding: utf-8 -*-
{
    'name': "Droga Fixed Asset",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Afomsoft Technologies",
    'website': "https://www.afomsoft.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account_asset'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/droga_fixed_asset_account.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    'installable': True,
    'application': True,
}
