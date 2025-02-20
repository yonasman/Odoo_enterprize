# -*- coding: utf-8 -*-
# from odoo import http


# class DrogaFleet(http.Controller):
#     @http.route('/droga_fleet/droga_fleet', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/droga_fleet/droga_fleet/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('droga_fleet.listing', {
#             'root': '/droga_fleet/droga_fleet',
#             'objects': http.request.env['droga_fleet.droga_fleet'].search([]),
#         })

#     @http.route('/droga_fleet/droga_fleet/objects/<model("droga_fleet.droga_fleet"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('droga_fleet.object', {
#             'object': obj
#         })
