# -*- coding: utf-8 -*-
# from odoo import http


# class DrogaRa(http.Controller):
#     @http.route('/droga_ra/droga_ra', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/droga_ra/droga_ra/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('droga_regulatory.listing', {
#             'root': '/droga_ra/droga_ra',
#             'objects': http.request.env['droga_regulatory.droga_ra'].search([]),
#         })

#     @http.route('/droga_ra/droga_ra/objects/<model("droga_regulatory.droga_ra"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('droga_regulatory.object', {
#             'object': obj
#         })
