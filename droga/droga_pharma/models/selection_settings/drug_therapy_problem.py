from odoo import models, fields, api
from odoo.http import request


class droga_pharma_drug_therapy_problem(models.Model):
    _name = 'droga.pharma.drug.therapy.problem'
    _rec_name = "dtp"

    dtp=fields.Char('Drug therapy problem')
    descr=fields.Char('Description')
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    cause_id=fields.One2many('droga.pharma.drug.therapy.problem.cause','problem_id')
