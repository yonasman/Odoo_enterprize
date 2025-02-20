# -*- coding: utf-8 -*-
# from odoo import http


# class DrogaCrm(http.Controller):
#     @http.route('/droga_crm/droga_crm', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/droga_crm/droga_crm/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('droga_crm.listing', {
#             'root': '/droga_crm/droga_crm',
#             'objects': http.request.env['droga_crm.droga_crm'].search([]),
#         })

#     @http.route('/droga_crm/droga_crm/objects/<model("droga_crm.droga_crm"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('droga_crm.object', {
#             'object': obj
#         })
