from odoo import models, fields, api
from odoo.http import request


class droga_pharma_intervention(models.Model):
    _name = 'droga.pharma.intervention'
    _rec_name = "intervention"

    intervention=fields.Char('Intervention')
    descr=fields.Char('Description')
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

