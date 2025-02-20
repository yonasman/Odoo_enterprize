from odoo import models, fields, api

class MarketCompetitors(models.Model):
    _name = 'market.competitors'
    _description = 'Market Competitors'

    name = fields.Char(string='Name')
    phone = fields.Char(string='Phone')
    products_offered = fields.Many2many('product.product', string='Products Offered')
    website = fields.Char(string='Website')