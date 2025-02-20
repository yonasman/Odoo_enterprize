from odoo import models, fields, api
from odoo.http import request


class droga_pharma_drug_therapy_problem(models.Model):
    _name = 'droga.pharma.drug.therapy.problem.cause'
    _rec_name = "dtpc"

    dtpc=fields.Char('Cause')
    descr=fields.Char('Description')
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')],required=True,default='Active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    problem_id=fields.Many2one('droga.pharma.drug.therapy.problem', required=True)

    recommended_intervention=fields.Many2one('droga.pharma.intervention')
