from odoo import models, fields, api

class droga_pharma_high_value_purchase(models.Model):
    _name = 'droga.pharma.high.value.pruchase'

    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']

    from_amt = fields.Float(string='From amount', tracking=True)
    to_amt = fields.Float(string='To amount', tracking=True)
    prod_group = fields.Many2many('product.category', string='Reward product groups', tracking=True)
    discount = fields.Float(string='Discount', tracking=True)
    remark = fields.Char('Remark')
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], required=True, default='Active',
                              tracking=True)