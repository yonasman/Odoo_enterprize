# -*- coding: utf-8 -*-
# from odoo import http


# class DrogaTreasury(http.Controller):
#     @http.route('/droga_treasury/droga_treasury', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/droga_treasury/droga_treasury/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('droga_treasury.listing', {
#             'root': '/droga_treasury/droga_treasury',
#             'objects': http.request.env['droga_treasury.droga_treasury'].search([]),
#         })

#     @http.route('/droga_treasury/droga_treasury/objects/<model("droga_treasury.droga_treasury"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('droga_treasury.object', {
#             'object': obj
#         })
