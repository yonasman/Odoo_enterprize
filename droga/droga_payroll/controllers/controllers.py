# -*- coding: utf-8 -*-
# from odoo import http


# class DrogaPayroll(http.Controller):
#     @http.route('/droga_payroll/droga_payroll', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/droga_payroll/droga_payroll/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('droga_payroll.listing', {
#             'root': '/droga_payroll/droga_payroll',
#             'objects': http.request.env['droga_payroll.droga_payroll'].search([]),
#         })

#     @http.route('/droga_payroll/droga_payroll/objects/<model("droga_payroll.droga_payroll"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('droga_payroll.object', {
#             'object': obj
#         })
