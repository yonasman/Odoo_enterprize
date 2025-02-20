from odoo import models,fields

class droga_price_discount_per_branch_group(models.Model):
    _name = 'droga.price.discount.per.branch.group'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    branch=fields.Many2many('stock.warehouse',tracking=True)
    prod_grp=fields.Many2many('droga.prod.categ.pharma','droga_discount_group_rel','droga_categ_id','pharmacy_branch_id',tracking=True)
    percent = fields.Float(string='Percentage (+ve or -ve)', tracking=True,required=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], required=True, default='Active',
                              tracking=True)

