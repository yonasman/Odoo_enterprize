from odoo import models, fields, api


class Competitors(models.Model):
    _name = 'droga.purchase.competitors'

    _rec_name = "competitor_name"
    competitor_name = fields.Char("Competitor Name", required=True)
    competitor_descr = fields.Char("Competitor Description", required=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], required=True, default='Active')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
