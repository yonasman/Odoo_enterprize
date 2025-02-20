from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class droga_criteria_header(models.Model):
    _name = "droga.bdr.analysis.criteria.header"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _rec_name = 'header'

    header = fields.Char(string='Configration name')
    type = fields.Selection(selection=[('product', 'Product'), ('supplier', 'Supplier')], string='Configration For')

    criteria_detail = fields.One2many('droga.bdr.analysis.criteria', 'criteria_header')

    def delete_record(self):
            self.unlink()

    @api.constrains('criteria_detail')
    def check_weight(self):
        if self.criteria_detail:
            total_weight = 0.0
            for criteria in self.criteria_detail:
                total_weight += criteria.weight
            if total_weight != 100.0:
                raise ValidationError('Sum of weights should be 100')


class droga_bond_requests(models.Model):
    _name = "droga.bdr.analysis.criteria"

    criteria_header=fields.Many2one('droga.bdr.analysis.criteria.header')
    header = fields.Char(related='criteria_header.header', required=True)

    criteria = fields.Char("Criteria Name", required=True)
    status = fields.Selection(selection=[('active', 'Active'), ('closed', 'Closed')])
    minimum_score = fields.Integer("Minimum Score")
    maximum_score = fields.Integer("Maximum Score")
    weight = fields.Float("Weight")
    score = fields.Float("Score", default=lambda self: self.minimum_score)


    def delete_record(self):
        self.unlink()



