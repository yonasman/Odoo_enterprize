# -*- coding: utf-8 -*-
{
    'name': "Droga Self Service",

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
    'category': 'Droga Self Service',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account_budget', 'droga_procurement', 'droga_inventory', 'droga_hr','droga_fleet'],

    # always loaded
    'data': [
        'security/self_service_security.xml',
        'security/ir.model.access.csv',
        'views/actions.xml',
        'views/menu.xml',

    ],
    # only loaded in demonstration mode
    'demo': [

    ],
    'installable': True,
    'application': True,
}
