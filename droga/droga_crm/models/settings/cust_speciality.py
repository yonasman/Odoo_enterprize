from odoo import models, fields, api

class contact_speciality(models.Model):
    _name='droga.cust.specialty'
    _rec_name = "specialty"
    specialty=fields.Char('Specialty')
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], required=True,default='Active')
