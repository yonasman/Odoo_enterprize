from odoo import models, fields, api
from odoo.http import request


class droga_pharma_area_counsel(models.Model):
    _name = 'droga.pharma.area_counsel'
    _rec_name = "area_coun"

    area_coun=fields.Char('Area of counsel')
    descr=fields.Char('Description')
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

