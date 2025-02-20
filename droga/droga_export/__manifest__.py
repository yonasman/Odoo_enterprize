# -*- coding: utf-8 -*-
{
    'name': "Droga Export",

    'summary': """
        Droga Pharma Pvt. Ltd.Co Export extension module.""",

    'description': """
        This module is developed for Droga Pharma Pvt. Ltd.Co. It works as stand-alone module for Export.
    """,

    'author': "Afomsoft Technologies",
    'website': "https://afomsoft.com",

    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': 'Export Extension',
    'version': '1.0',

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/droga_status_list_cost_build.xml',
        'views/droga_export_cost_types.xml',
        'views/droga_sales_status_list.xml',
        'views/droga_export_inventory_menus.xml',
        'views/items_composition.xml',
        'views/droga_sub_contractor_send.xml',
        'views/droga_sales_extension.xml',
        'views/droga_sub_contractor_receipt.xml'
    ],

    # any module necessary for this one to work correctly

    'depends': ['base', 'hr',
                'mail', 'stock', 'http_routing', 'sale',
                'resource', 'stock', 'droga_inventory',
                'web', 'crm'],
    "license": "AGPL-3",
    # only loaded in demonstration mode
    'installable': True,
    'application': True,
}
