from odoo import models, fields, api
from odoo.http import request


class droga_pharma_current_status(models.Model):
    _name = 'droga.pharma.current_status'
    _rec_name = "c_status"
    #This model is used to hold current status of the customer upon MTM, such as improved, worse...

    c_status=fields.Char('Current status')
    descr=fields.Char('Description')
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

