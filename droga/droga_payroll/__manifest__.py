# -*- coding: utf-8 -*-
{
    'name': "Droga Payroll",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_contract', 'hr_payroll', 'droga_hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payslip_run.xml',
        'views/hr_contract.xml',
        'views/hr_payroll_payment_deduction.xml',
        'views/hr_payroll_rate.xml',
        'views/hr_payroll_variable_payment.xml',
        'report/hr_payslip_line.xml',
        'data/mail_template.xml',
        'views/hr_payslip.xml',
        'views/Menu.xml',
        'views/hr_payslip_employees.xml',
        'report/hr_payslip_run.xml',

    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
