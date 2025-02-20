from email.policy import default
from odoo import models, fields, api

class droga_pharma_compounding(models.Model):
    _name = 'droga.pharma.compounding'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    item_to_prepare=fields.Many2one('product.template',required=True)

    #Text fields
    calc_applied=fields.Text('Calculation applied')
    mixing_inst=fields.Text('Mixing instruction')
    container_used=fields.Selection([('Plastic','Plastic'),('Glass','Glass')])
    lb_expiry_date=fields.Date('Expiry date')
    lb_dur=fields.Char('Duration')
    lb_prec=fields.Char('Precaution')
    comp_detail = fields.One2many('droga.pharma.compounding.detail', 'comp_header')

class droga_pharma_compounding_detail(models.Model):
    _name = 'droga.pharma.compounding.detail'
    comp_header=fields.Many2one('droga.pharma.compounding')

    qty=fields.Float('Quantity')
    ingredient=fields.Many2one('product.template',string='Ingredient')
    product_uom_category_id = fields.Many2one(related='ingredient.uom_id.category_id', store=True)
    product_uom = fields.Many2one('uom.uom', "UoM", store=True, required=True,
                                  domain="[('category_id', '=', product_uom_category_id)]")
    uom_remark=fields.Char('UOM remark')
