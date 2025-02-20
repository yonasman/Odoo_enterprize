# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Droga Fleet',
    'version': '1.0',
    'author': "Afomsoft Technologies",
    'website': "https://afomsoft.com",
    'summary': 'Manage your fleet and track car costs',
    'description': """
Vehicle, leasing, insurances, cost
==================================
With this module, Odoo helps you managing all your vehicles, the
contracts associated to those vehicle as well as services, costs
and many other features necessary to the management of your fleet
of vehicle(s)

Main Features
-------------
* Add vehicles to your fleet
* Manage contracts for vehicles
* Reminder when a contract reach its expiration date
* Add services, odometer values for all vehicles
* Show all costs associated to a vehicle or to a type of service
* Analysis graph for costs
""",
    'depends': ['base', 'hr',
                'mail', 'stock', 'http_routing', 'sale',
                'resource', 'stock','droga_crm',
                'fleet'
                ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'views/droga_fleet_task_kanban.xml',

        'views/rejection_reasons.xml',
        'views/droga_fleet_request_task_views.xml',
        'views/fleet_report.xml',
        'views/droga_fleet_request_menus.xml',


        'views/droga_fleet_vehicle_register_views.xml',
        'views/sale_order_fleet_request.xml',


    ],
    "assets": {
        "web.assets_backend": [
            'droga_fleet/static/src/js/driver_location.js',
            'droga_fleet/static/src/xml/driver.xml',

        ],

    },

    'installable': True,
    'application': True,
    # 'assets': {
    #     'web.assets_backend': [
    #         'fleet/static/src/**/*',
    #     ],
    # },
    # 'license': 'LGPL-3',
}
