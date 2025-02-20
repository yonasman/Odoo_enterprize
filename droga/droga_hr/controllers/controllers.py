# -*- coding: utf-8 -*-
# from odoo import http


# class DrogaHr(http.Controller):
#     @http.route('/droga_hr/droga_hr', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/droga_hr/droga_hr/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('droga_hr.listing', {
#             'root': '/droga_hr/droga_hr',
#             'objects': http.request.env['droga_hr.droga_hr'].search([]),
#         })

#     @http.route('/droga_hr/droga_hr/objects/<model("droga_hr.droga_hr"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('droga_hr.object', {
#             'object': obj
#         })
