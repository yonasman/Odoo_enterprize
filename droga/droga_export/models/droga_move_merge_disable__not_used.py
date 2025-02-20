from odoo import api, fields, models
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate_dont_run(self):
        for rec in self:

            initial_moves = self.env['stock.picking'].search([('origin', '=', rec.name)]).mapped('group_id.id')

            mrp_items = self.env['mrp.production'].search(
                [('procurement_group_id', 'in', initial_moves), ('state', '!=', 'done')])
            for mrp in mrp_items:
                mrp.button_mark_done()

        return super(StockPicking, self).button_validate()

    def _subcontracted_produce_dont_run(self, subcontract_details):
        self.ensure_one()
        prior_id = False
        prior_pick_id=False
        for move, bom in subcontract_details:
            if float_compare(move.product_qty, 0, precision_rounding=move.product_uom.rounding) <= 0:
                # If a subcontracted amount is decreased, don't create a MO that would be for a negative value.
                continue
            if not prior_pick_id:
                prior_pick_id=move.picking_id

            move.picking_id=prior_pick_id
            mo = self.env['mrp.production'].with_company(move.company_id).create(
                    self._prepare_subcontract_mo_vals(move, bom))

            if not prior_id:
                prior_id = mo.procurement_group_id
            mo.procurement_group_id = prior_id

            self.env['stock.move'].create(mo._get_moves_raw_values())
            self.env['stock.move'].create(mo._get_moves_finished_values())
            mo.date_planned_finished = move.date  # Avoid to have the picking late depending of the MO

            mo.action_confirm()

            # Link the finished to the receipt move.
            finished_move = mo.move_finished_ids.filtered(lambda m: m.product_id == move.product_id)
            finished_move.write({'move_dest_ids': [(4, move.id, False)]})
            mo.action_assign()

