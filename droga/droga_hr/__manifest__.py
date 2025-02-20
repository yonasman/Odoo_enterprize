# -*- coding: utf-8 -*-
{
    'name': "Droga Human Resource",

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
    'category': 'Droga HR',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_attendance'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/hr_security.xml',
        'views/hr_job.xml',
        'views/hr_job_salary_payment.xml',
        'views/hr_head_count_request.xml',
        'views/employee.xml',
        'views/hr_letter.xml',
        'views/hr_attendance.xml',
        'views/hr_attendance_absence.xml',
        'views/hr_attendance_over_time_report.xml',
        'views/hr_division.xml',
        'report/letter.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [

    ],

    'installable': True,
    'application': True,
}
