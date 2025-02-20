# -*- coding: utf-8 -*-
{
    'name': "Droga BD regulatory",
    'sequence': '2',
    'summary': """
        Droga Pharma Pvt. Ltd.Co Buisness development and regulatory affairs module.""",

    'description': """
        This module is developed for Droga Pharma Pvt. Ltd.Co. It works as a stand-alone module to handle Buisness development and regulatory affairs operations. It will be used as a registering, monitoring and follow-up tool to manage requested items for buisness developemnt and the regulatory followup.
    """,

    'author': "Afomsoft Technologies",
    'website': "https://afomsoft.com",

    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': 'Buisness development and regulatory affairs',
    'version': '1.0',

    # always loaded
    'data': [

        'security/ir.model.access.csv',
        'static/security.xml',

        'views/product_requests.xml',
        'views/sequence_file.xml',
        'views/analysis_criteria_views.xml',
        'views/product_analysis_views.xml',
        'views/product_criteria_views.xml',
        'views/competitors.xml',
        'views/grading_model_views.xml',
        'views/supplier.xml',

        'views/market_analysis.xml',
        'views/market_analysis_category_report.xml',



        'views/agents.xml',

        'views/agency_agreement.xml',
        'views/product_registration.xml',


        'views/release_permit.xml',
        'views/pre_import_permit.xml',

        'views/gmp_follow_up.xml',

        'views/registered_list.xml',
        'views/registration_follow_up.xml',
        'views/qc_follow_up.xml',



        'views/menus.xml',

    ],

    # any module necessary for this one to work correctly

    'depends': ['base', 'hr', 'account',
                'mail', 'hr',
                'resource', 'stock', 'sale',
                'web'],
    "license": "AGPL-3",
    # only loaded in demonstration mode
    'installable': True,
    'application': True
}
