# -*- coding: utf-8 -*-

{
    'name': "Droga CRM",
    'summary': """
    Droga Pharma Pvt. Ltd.Co CRM extension module.""",
    'description': """
    This module is developed for Droga Pharma Pvt. Ltd.Co. It works as an extension for CRM module.
    """,

    'author': "Afomsoft Technologies",
    'website': "https://afomsoft.com",

    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': 'CRM Extension',
    'version': '1.0',

    # always loaded
    'data': [
        'security/security.xml',
        'reports/leads_report.xml',
        'views/module_menus.xml',
        'security/ir.model.access.csv',
        'reports/excel_reports/visit_plan.xml',
        'reports/core_products.xml',
        'data/grade_updater_cron.xml',
        'views/cust_extension.xml',
        'views/customer_visits.xml',
        'views/sales_target.xml',
        'views/settings/cust_grade.xml',
        'views/settings/specialty.xml',
        'views/settings/job_position.xml',
        'views/settings/cust_type.xml',
        'views/inventory_extension.xml',
        'views/settings/region.xml',
        'views/settings/crm_prod_group.xml',
        'views/settings/city.xml',
        'views/settings/area.xml',
        'views/lead_extension.xml',
        'reports/plan_analysis.xml',
        'reports/doctors_schedule.xml',
        'reports/done_activities.xml',
        'wizards/lead2opp_ext.xml',
        'views/settings/promotor_sales_master.xml',
        'views/settings/pro_sales_entry.xml',
    ],

    # any module necessary for this one to work correctly

    'depends': ['base', 'hr',
                'mail', 'stock', 'http_routing', 'sale','web_map',
                'resource', 'stock', 'droga_inventory',
                'web', 'crm'],

    "assets": {
        "web.assets_backend": [
            'droga_crm/static/src/droga_set_cust_location.js',
            'droga_crm/static/src/res_partner_button.xml',
            'droga_crm/static/src/check_in.js',
            'droga_crm/static/src/check_in_template.xml',
        ],

    },
    "license": "AGPL-3",
    # only loaded in demonstration mode
    'installable': True,
    'application': True,
    'post_init_hook': 'create_days'
}
