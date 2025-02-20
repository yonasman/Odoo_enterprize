# -*- coding: utf-8 -*-
{
    'name': "Droga Tender",

    'summary': """
        Droga Pharma Pvt. Ltd.Co Tender module.""",

    'description': """
        This module is developed for Droga Pharma Pvt. Ltd.Co. It works as a stand-alone module to handle tender operations. It will be used as a registering, monitoring and follow-up tool to manage tender operations under Droga group.
    """,

    'author': "Afomsoft Technologies",
    'website': "https://afomsoft.com",

    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': 'Tender',
    'version': '1.0',

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/droga_tender_master.xml',
        'views/droga_tender_master_detail.xml',
        'views/droga_tender_security_detail.xml',
        'views/settings/media.xml',
        'views/settings/tender_uom.xml',
        'views/settings/sec_type.xml',
        'views/settings/incoterm.xml',
        'views/settings/competitors.xml',
        'views/settings/customers.xml',
        'views/settings/submission_place.xml',
        'views/settings/type_or_item.xml',
        'views/droga_tender_master_submission.xml',
        'views/droga_tender_competitors.xml',
        'views/droga_tender_tech_specs.xml',
        'views/droga_tender_module_extensions.xml',
        'views/droga_tender_contract_security_tree.xml',
        'views/reports/total_tenders.xml',
        'views/reports/failed_cancelled.xml',
        'views/reports/tender_sample.xml',
        'views/reports/security_grouped.xml',
        'views/reports/total_awarded.xml',
        'views/reports/total_performance.xml',
        'views/droga_tender_detail_input.xml',
        'views/droga_tender_bond_request.xml',
        'reports/excel_reports/financial_proposal.xml',
        'reports/excel_reports/technical_proposal.xml',
        'data/droga_tender_sequence.xml',
        'security/tender_scheduled_alerts.xml'
    ],

    # any module necessary for this one to work correctly

    'depends': ['base', 'hr', 'account','droga_crm',
                'mail', 'droga_crm', 'hr', 'droga_finance', 'droga_inventory','droga_sales',
                'resource', 'stock', 'sale',
                'web'],
    "license": "AGPL-3",
    # only loaded in demonstration mode
    'installable': True,
    'application': True
}
