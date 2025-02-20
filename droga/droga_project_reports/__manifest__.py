{
    'name': 'Droga Project Reports',
    'version': '16.0.1.0.0',
    'depends': ['droga_project', 'base','project','report_xlsx'],
    'category': 'Reporting',
    'summary': 'Custom reports for Droga Project',
    'description': 'Adds reporting menu and Excel reports for Droga Project.',
    'author': 'Yonas Negese M',
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'data': [
        'security/ir.model.access.csv',
        'views/project_progress_wizard.xml',
        'views/project_progress_report_action.xml',
        'views/project_progress_report_menu.xml',

    ],
    'report': [
        'reports/droga_project_progress_xlsx.py'
    ]
}
