# -*- coding: utf-8 -*-
# from odoo import http


# class DrogaTender(http.Controller):
#     @http.route('/droga_tender/droga_tender', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/droga_tender/droga_tender/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('droga_tender.listing', {
#             'root': '/droga_tender/droga_tender',
#             'objects': http.request.env['droga_tender.droga_tender'].search([]),
#         })

#     @http.route('/droga_tender/droga_tender/objects/<model("droga_tender.droga_tender"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('droga_tender.object', {
#             'object': obj
#         })
