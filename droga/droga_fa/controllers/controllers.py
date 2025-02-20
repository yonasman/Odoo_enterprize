# # -*- coding: utf-8 -*-
# from odoo import http
#
#
# class DrogaFa(http.Controller):
#     @http.route('/droga_fa/droga_fa', auth='public')
#     def index(self, **kw):
#         print("Hello world")
#         return "Hello, world"
#
#     @http.route('/droga_fa/droga_fa/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('droga_fa.listing', {
#             'root': '/droga_fa/droga_fa',
#             'objects': http.request.env['droga_fa.droga_fa'].search([]),
#         })
#
#     @http.route('/droga_fa/droga_fa/objects/<model("droga_fa.droga_fa"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('droga_fa.object', {
#             'object': obj
#         })
