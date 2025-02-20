from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.http import request


class droga_pharma_current_status(models.Model):
    _name = 'droga.pharma.prod.categ'
    _rec_name = "prod_categ"
    #This model is used to hold current status of the customer upon MTM, such as improved, worse...

    prod_categ=fields.Char('Product category')
    descr=fields.Char('Description')
    categ_id = fields.Many2one(
        'product.category', 'Product Category', required=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

