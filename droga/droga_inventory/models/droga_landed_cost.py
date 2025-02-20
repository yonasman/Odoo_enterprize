from odoo import models, fields, api
from odoo.exceptions import ValidationError
import json


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    lc = fields.Many2one('account.analytic.account', domain=[
        ('plan_id', '=', 'LC')])

    def button_update_analytics(self):
        for record in self:
            for move in record.account_move_id:
                # update lc analytics
                # data = {str(record.lc.id): 100.00}

                data = {}
                data[str(record.lc.id)] = 100.00
                json_data = json.dumps(data)

                self.env.cr.execute(
                    """ update account_move_line set analytic_distribution=%s where move_id=%s and company_id=%s """,
                    (json_data, move.id, move.company_id.id))

                # for move_line in move.line_ids:
                # move_line.analytic_distribution = data

    # def button_validate(self):
    # raise ValidationError("The LC is already linked with another landed cost")

    # one LC can be linked to one landed cost
    # @api.constrains('lc')
    def validate_lc(self):
        for record in self:
            # search lc in landed costs
            landed_cost = self.env['stock.landed.cost'].search_count([('lc', '=', record.lc.id)])

            if landed_cost > 1:
                raise ValidationError("The LC is already linked with another landed cost")


class LandedCostLines(models.Model):
    _inherit = 'stock.landed.cost.lines'
