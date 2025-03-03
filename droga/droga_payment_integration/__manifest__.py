{
    'name': 'Droga Payment Integration',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Integrates different Payment Gateway with Odoo Sales',
    'author': 'Yonas Negese M',
    'website': '',
    'depends': ['droga_sales', 'payment'],
    'data': [
        # 'views/telebirr_payment_acquirer_form.xml',
        # 'data/telebirr_payment_acquirer_data.xml',
        'security/ir.model.access.csv',
        'wizards/payment_options_wizard_views.xml',
        'views/account_move_inherit_views.xml',



    ],
    'images':['static/description/icon.png'],
    'installable': True,
    'application': True,
}
