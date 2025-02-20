from odoo import models, fields, api


class customer_grade(models.Model):
    _name='droga.cust.grade'
    _rec_name = "grade"
    grade=fields.Char('Grade')
    cont_include=fields.Boolean('Include in contacts',default=True)
    visit_times_per_month = fields.Integer('Visit per month')
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], required=True,default='Active')
