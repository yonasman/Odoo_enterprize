# -*- coding: utf-8 -*-
{
    'name': "Droga Project",

    'summary': """
        Droga Pharma Pvt. Ltd.Co Project module extension.""",

    'description': """
        This module is developed for Droga Pharma Pvt. Ltd.Co. It works as an extension module to handle project operations. 
    """,

    'author': "Afomsoft Technologies",
    'website': "https://afomsoft.com",

    # Categories can be used to filter modules in modules listing
    # for the full list

    'version': '1.0',

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/droga_project_view.xml',
        'views/droga_project_inventory_menus.xml',
        'views/droga_subtask_veiw.xml',
        'views/droga_project_scope.xml',
        'views/droga_header_footer_template.xml',
        'report/droga_project_list.xml',
        'views/droga_contractor.xml',
        'views/droga_store_issue.xml',
        'views/analytic_inherit.xml',
        'views/droga_consultant.xml',
        'report/tasks.xml',
        'report/projects.xml',
        'report/droga_project_list.xml'
    ],
    # any module necessary for this one to work correctly

    'depends': ['base', 'droga_finance',
                'mail', 'project', 'stock', 'purchase', 'droga_inventory',
                'resource', 'droga_procurement',
                'web', 'crm'],
    "license": "AGPL-3",
    # only loaded in demonstration mode
    'installable': True,
    'application': True
}
