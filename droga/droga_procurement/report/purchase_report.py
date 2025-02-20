from odoo import models, fields


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'

    grns = fields.Many2many('stock.picking', compute="get_grns_and_landed_cost")
    landed_cost = fields.Float("Landed Cost", compute="get_grns_and_landed_cost")
    po_and_lc_total = fields.Float("Grand Total",compute="get_grns_and_landed_cost")

    def get_grns_and_landed_cost(self):
        for record in self:
            record.landed_cost = 0
            # search done grns
            grns = self.env['stock.picking'].search([('origin', '=', record.order_id.name), ('state', '=', 'done')])
            landed_cost_total = 0
            # search landed costs
            if grns:
                landed_costs = self.env['stock.landed.cost'].search([('picking_ids', 'in', grns.ids)])

                for landed_cost in landed_costs.valuation_adjustment_lines:
                    if landed_cost.product_id == record.product_id:
                        landed_cost_total += landed_cost.additional_landed_cost

            record.grns = grns
            record.landed_cost = landed_cost_total
            record.po_and_lc_total=landed_cost_total+record.price_total
