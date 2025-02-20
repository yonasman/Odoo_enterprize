from odoo import models, fields, api
from datetime import date

class droga_pharma_stock_card(models.TransientModel):
    _name = 'droga.pharma.itr'
    _descr = 'Inventory turn over rate'

    branch = fields.Many2one('stock.warehouse', 'Warehouse')
    product = fields.Many2one('product.product', 'Product')
    date_from = fields.Date('Date from', default=date(2022, 12, 20))
    date_to = fields.Date('Date to', default=fields.Date.today())

    results=fields.One2many('droga.pharma.itr.detail','header')
    def load_results(self):
        pass

class pharma_price_list(models.TransientModel):
    _name = 'droga.pharma.itr.detail'
    header = fields.Many2one('droga.pharma.itr')
    product=fields.Many2one('product.template',string='Product')
    cogs=fields.Float('COGS')
    av_inv=fields.Float('Average inventory')
    inv_tur=fields.Float('ITR')
    dsi = fields.Float('Days to sell')

