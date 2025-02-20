# -*- coding: utf-8 -*-
from odoo import http


class DrogaSales(http.Controller):
    @http.route('/', type='json', auth='none', cors='*')
    def index(self):
        return "Hello, world"
