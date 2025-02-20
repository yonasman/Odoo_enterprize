# -*- coding: utf-8 -*-
# from odoo import http


# class DrogaBd(http.Controller):
#     @http.route('/droga_bd/droga_bd', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/droga_bd/droga_bd/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('droga_bd.listing', {
#             'root': '/droga_bd/droga_bd',
#             'objects': http.request.env['droga_bd.droga_bd'].search([]),
#         })

#     @http.route('/droga_bd/droga_bd/objects/<model("droga_bd.droga_bd"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('droga_bd.object', {
#             'object': obj
#         })
