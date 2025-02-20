# -*- coding: utf-8 -*-
{
    'name': "Droga treasury internal",

    'summary': """
        Droga Pharma Pvt. Ltd.Co Treasury extension module.""",

    'description': """
        This module is developed by Droga Pharma Pvt. Ltd.Co for Droga Pharma Pvt. Ltd.Co. It works as an extension to Droga_treasury module.
    """,

    'author': "Droga Pharma",
    'website': "www.drogapharma.com",

    'category': 'Treasury',
    'version': '1.0',

    'data': [
        'data/cron_interest.xml',
        'view.xml'
    ],

    # any module necessary for this one to work correctly

    'depends': ['droga_treasury'],
    "license": "AGPL-3",
    # only loaded in demonstration mode
    'installable': True,
    'application': True
}
