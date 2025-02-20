from odoo import models, fields
from odoo.exceptions import UserError, ValidationError


class droga_raw_items_model(models.Model):
    _name='droga.export.raw.items'
    item=fields.Many2one('product.template')
    qty=fields.Float('Quantity')
    po_id=fields.Many2one('purchase.order')


class drogapoinherit(models.Model):
    _inherit = 'purchase.order'
    sub_cont_sent=fields.Boolean('Subcontractor sent',default=False)
    raw_items=fields.One2many('droga.export.raw.items','po_id')
    show_sub_contractor_price=fields.Boolean('Show cleaning unit price',default=False)
    def fill_po(self):
        by_products = []
        waste = []
        self.show_sub_contractor_price=False
        self.write({'raw_items': False})
        for ord_line in self.order_line:
            qty=ord_line['product_qty']
            p_unit=ord_line['price_unit']
            raw_details = self.env['droga.export.items.composition.fin.goods'].search(
                [('item', '=', ord_line.product_id.product_tmpl_id.id), ('type', '=', 'finish')])
            if len(raw_details) > 0:
                self.show_sub_contractor_price = True
                # Get header of the finalized good
                raw = raw_details[0].items_header

                ri={'po_id':self.id,
                    'item':raw_details[0].items_header.raw_item.id,
                    'qty':ord_line['product_qty']}
                self.env['droga.export.raw.items'].sudo().create(ri)

                # Iterate through the detailed products
                for det_goods in raw.items_detail:
                    if self.env['product.product'].search([('product_tmpl_id','=',det_goods['item'].id)])[0].id==ord_line['product_id'].id:
                        ord_line['product_qty']=ord_line['product_qty']*det_goods['rate_in_pct'] / 100
                        ord_line['price_unit']=p_unit
                        ord_line['raw_item']=raw.raw_item.id
                    elif det_goods['type'] == 'byproduct':
                        by_products.append({
                            'order_id': self.id,
                            'product_qty': qty * det_goods['rate_in_pct'] / 100,
                            'name': det_goods['item'].name,
                            'product_id': self.env['product.product'].search([('product_tmpl_id','=',det_goods['item'].id)])[0].id,
                            'product_uom': det_goods['item'].uom_id.id,
                            'price_unit':p_unit,
                            'company_id': self.env.company.id,
                            'date_planned': ord_line['date_planned'],
                            'raw_item':raw.raw_item.id,
                            'sub_cont_price': p_unit
                        })
                    elif det_goods['type'] == 'waste':
                        waste.append({
                            'order_id': self.id,
                            'product_qty': qty * det_goods['rate_in_pct'] / 100,
                            'name': det_goods['item'].name,
                            'product_id': self.env['product.product'].search([('product_tmpl_id','=',det_goods['item'].id)])[0].id,
                            'product_uom': det_goods['item'].uom_id.id,
                            'price_unit':p_unit,
                            'company_id': self.env.company.id,
                            'date_planned': ord_line['date_planned'],
                            'raw_item': raw.raw_item.id,
                            'sub_cont_price':p_unit
                        })
            ord_line.sub_cont_price=ord_line.price_unit

        max_sequence = max(self.order_line.mapped('sequence')) if len(self.order_line)>0 else 10
        if len(by_products) > 0:
            max_sequence += 1
            order_lines = {
                'order_id': self.id,
                'product_qty': 0,
                'name': 'By-Products',
                'display_type': 'line_section',
                'company_id': self.env.company.id,
                'sequence': max_sequence,
            }
            self.order_line.fill_po(order_lines)
            for bp in by_products:
                max_sequence += 1
                bp['sequence']=max_sequence
                self.order_line.fill_po(bp)

        if len(waste) > 0:
            max_sequence += 1
            order_lines = {
                'order_id': self.id,
                'product_qty': 0,
                'name': 'Waste',
                'display_type': 'line_section',
                'company_id': self.env.company.id,
                'sequence': max_sequence,
            }
            self.order_line.fill_po(order_lines)
            for ws in waste:
                max_sequence += 1
                ws['sequence']=max_sequence
                self.order_line.fill_po(ws)

    def button_confirm(self):
        res=super(drogapoinherit, self).button_confirm()

        for rec in self:
            wh=rec.picking_type_id.warehouse_id
            pick_type_id = self.env['stock.picking.type'].sudo().search(
                [('sequence_code', '=', 'SUBL'),('warehouse_id', '=', wh.id)]).id
            sub_locat = self.env['stock.location'].search([('con_type', '=', 'SUBL')]).id
            def_loc_id = self.env['stock.location'].search(
                [('complete_name', 'like', wh.code + '/%'), ('con_type', '=', False), ('usage', '=', 'internal')])[
                0].id
            if not def_loc_id:
                raise UserError("Store location not set for "+wh.name+" warehouse. Please configure accordingly.")
            if not pick_type_id:
                raise UserError("Picking type for subcontractor issue is not configured.")
            if not sub_locat:
                raise UserError(
                    "Subcontractor location for type 'SUBL' is not set. Please configure accordingly.")


            picking_vals = {
                'partner_id': self.partner_id.id,
                'company_id': self.company_id.id,
                'picking_type_id': pick_type_id,
                'location_id': def_loc_id,
                'location_dest_id': sub_locat,
                'origin': self.name,
                'state': 'confirmed',
                'scheduled_date': self.date_order
            }
            picking_id = self.env['stock.picking'].sudo().create(picking_vals)

            for rec_item in self.raw_items:

                move_vals = {
                    'picking_id': picking_id.id,
                    'picking_type_id': pick_type_id,
                    'name': picking_id.name,
                    'product_id': self.env['product.product'].search([('product_tmpl_id','=',rec_item['item'].id)])[0].id,
                    'product_uom': rec_item['item'].uom_id.id,
                    'product_uom_qty': rec_item['qty'],
                    'location_id': def_loc_id,
                    'location_dest_id': sub_locat,
                    'state': 'confirmed',
                    'company_id': self.company_id.id
                }

                self.env['stock.move'].sudo().create(move_vals)
            rec.sub_cont_sent=True
        return res

    def open_deliveries(self):
        return {
            'name': 'cleaning unit issue',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.picking',

            'views': [[self.env.ref('stock.vpicktree').id, 'tree'],
                          [self.env.ref('stock.view_picking_form').id, 'form']],
            'type': 'ir.actions.act_window',
            'domain': [('origin', '=', self.name),('picking_type_id.sequence_code','=','SUBL')],
            'context': {
                'default_origin': self.name,
                'default_from_reconcile_menu':True,
            }
        }

class drogapochildinherit(models.Model):
    _inherit = 'purchase.order.line'
    raw_item = fields.Many2one('product.template')
    sub_cont_price=fields.Float('Sub-cont. cost')
    def fill_po(self, line):
        self.create(line)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate_dont_run(self):
        #res=super(StockPicking, self).button_validate()
        for rec in self:

            if len(self.env['purchase.order'].search([('name','=',rec.origin)]))>0:
                if self.env['purchase.order'].search([('name','=',rec.origin)])[0]['sub_cont_sent']:
                    if len(self.env['stock.picking'].search([('origin','=',rec.origin),('state','=','done'),('picking_type_id.sequence_code','=','SUBL')]))==0 and rec.picking_type_id.sequence_code!='SUBL':
                        raise UserError("Items are not sent to contractor, please issue them before receiving items.")
                    else:
                        ref=self.env['stock.picking'].search([('origin','=',rec.origin),('state','=','done'),('picking_type_id.sequence_code','=','SUBL')])[0].name if len(self.env['stock.picking'].search([('origin','=',rec.origin),('state','=','done'),('picking_type_id.sequence_code','=','SUBL')]))>0 else False
                        for item in rec.move_ids:
                            if len(self.env['purchase.order.line'].search([('id','=',item.purchase_line_id.id)]))==0:
                                continue
                            raw_item=self.env['purchase.order.line'].search([('id','=',item.purchase_line_id.id)])[0]
                            val_up=self.env['stock.valuation.layer'].search([('reference','=',ref),('product_id','=',self.env['product.product'].search([('product_tmpl_id','=',raw_item.raw_item.id)])[0].id)])[0]['unit_cost']
                            raw_item.price_unit=raw_item.price_unit+(val_up) if raw_item.price_unit!=raw_item.sub_cont_price else raw_item.price_unit

        self.env.cr.commit()
        return super(StockPicking, self).button_validate()

