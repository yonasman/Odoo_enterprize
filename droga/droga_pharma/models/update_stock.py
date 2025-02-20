from odoo import models, fields, api
from datetime import date

class droga_pharma_stock_card(models.TransientModel):
    _name = 'droga.pharma.update.stock'
    _descr = 'Update stock values'

    product_id=fields.Many2one('product.template',string='Product')
    current_uom=fields.Many2one('uom.uom',string='Current UOM',related='product_id.uom_id')
    new_uom = fields.Many2one('uom.uom', string='New UOM')

    code = fields.Selection([(('All', 'All')),('incoming', 'Receipt'), ('outgoing', 'Delivery'), ('internal', 'Internal Transfer')], 'Type of Operation')
    warehouse=fields.Many2many('stock.warehouse')
    results_move=fields.One2many('droga.pharma.update.stock.move','header')
    results_move_po = fields.One2many('droga.pharma.update.po', 'header')
    #results_move_so = fields.One2many('droga.pharma.update.so', 'header')
    results_move_line = fields.One2many('droga.pharma.update.stock.move.line', 'header')
    rate=fields.Float('rate (division)',default=1)
    date=fields.Date('Transaction date')
    date_to = fields.Date('Transaction date to')

    qty_from = fields.Float('Quantity from')
    qty_to = fields.Float('Quantity to')

    ref=fields.Char('Transaction reference')
    prod_id=fields.Many2one('product.product',compute='get_prod_id')
    batch=fields.Many2one('stock.lot',domain="[('product_id', '=', prod_id)]")
    def get_prod_id(self):
        for rec in self:
            rec.prod_id=self.env['product.product'].search([('product_tmpl_id', '=', rec.product_id.id)]).id
    def _inverse(self):
        pass

    @api.onchange('new_uom','current_uom')
    def _get_uom_rate(self):
        for rec in self:
            if rec.current_uom:
                rec.rate=rec.new_uom.factor/rec.current_uom.factor
            else:
                rec.rate=1
    def load(self):
        for rec in self:
            rec.results_move.unlink()
            rec.results_move_line.unlink()
            rec.results_move_po.unlink()
            if rec.warehouse:
                warehouses=rec.warehouse
            else:
                warehouses=self.env['stock.warehouse'].search([])

            prod_id=self.env['product.product'].search([('product_tmpl_id','=',rec.product_id.id)]).id
            if rec.code:
                moves=self.env['stock.move'].search([('picking_id.picking_type_id.code','=',rec.code),('product_id','=',prod_id),'|',('location_id.warehouse_id','in', warehouses.ids),('location_dest_id.warehouse_id','in', warehouses.ids)])
                origins=self.env['stock.move'].search([('picking_id.picking_type_id.code','=',rec.code),('product_id','=',prod_id),'|',('location_id.warehouse_id','in', warehouses.ids),('location_dest_id.warehouse_id','in', warehouses.ids)]).mapped('origin')
            else:
                moves = self.env['stock.move'].search(
                    [('product_id', '=', prod_id), '|',('location_id.warehouse_id', 'in', warehouses.ids), ('location_dest_id.warehouse_id', 'in',  warehouses.ids)])
                origins=self.env['stock.move'].search(
                    [('product_id', '=', prod_id), '|',('location_id.warehouse_id', 'in', warehouses.ids), ('location_dest_id.warehouse_id', 'in',  warehouses.ids)]).mapped('origin')

            #Filter by date
            if rec.date and rec.date_to:
                moves = moves.filtered(lambda x: (x.date.date() >= rec.date and x.date.date() <= rec.date_to))
                origins = moves.mapped('origin')
            # Filter by reference
            if rec.ref:
                moves = moves.filtered(lambda x: (x.reference == rec.ref))
                origins = moves.mapped('origin')
            # Filter by quantity
            if rec.qty_to:
                moves = moves.filtered(lambda x: (x.quantity_done >= rec.qty_from and x.quantity_done<=rec.qty_to))
                origins = moves.mapped('origin')

            moves=moves.ids

            moves_line = self.env['stock.move.line'].search([('move_id','in',moves)]).ids
            po_lines=[]
            if len(moves)>0:
                po_lines=self.env['purchase.order.line'].search([('product_id','=',prod_id),('order_id.name','in',origins)]).ids


            for r in moves:
                mv={'header':rec.id,
                    'move_line':r}
                self.env['droga.pharma.update.stock.move'].create(mv)
            for r in moves_line:
                mv={'header':rec.id,
                    'move_line':r}
                self.env['droga.pharma.update.stock.move.line'].create(mv)
            for r in po_lines:
                mv={'header':rec.id,
                    'po_line':r}
                self.env['droga.pharma.update.po'].create(mv)

    def update_batch(self):
        for rec in self:
            for mv in rec.results_move_line:
                self.env.cr.execute(
                    """ update stock_move_line set lot_id=%s where id=%s""",
                    (rec.batch.id,mv.move_line.id))
            self.load()
    def update_trans(self):
        for rec in self:
            for mv in rec.results_move:
                self.env.cr.execute(
                    """ update stock_move set unit_price=unit_price/%s,tot_price=(unit_price/%s)*quantity_done,product_qty=product_uom_qty*%s,product_uom_qty=product_uom_qty*%s,quantity_done=quantity_done*%s,product_uom=%s where id=%s""",
                    (rec.rate,rec.rate,rec.rate,rec.rate,rec.rate, rec.new_uom.id, mv.move_line.id))
            for mv in rec.results_move_line:
                self.env.cr.execute(
                    """ update stock_move_line set reserved_qty=reserved_qty*%s,reserved_uom_qty=reserved_uom_qty*%s,qty_done=qty_done*%s,product_uom_id=%s where id=%s""",
                    (rec.rate,rec.rate,rec.rate,rec.new_uom.id,mv.move_line.id))
            for mv in rec.results_move_po:
                self.env.cr.execute(
                    """update purchase_order_line set product_uom=%s,product_qty=product_qty*%s,price_unit=price_unit/%s,qty_received=qty_received*%s,qty_to_invoice=qty_to_invoice*%s,qty_invoiced=qty_invoiced*%s where id=%s""",
                    (rec.new_uom.id,rec.rate,rec.rate,rec.rate,rec.rate,rec.rate, mv.po_line.id))

            #Update valuation table
            #Update stock.quant table
            #update ir_property set value_float=47.568 where res_id='product.product,32319';
            self.load()

    def round_whole_no(self):
        for rec in self:
            for mv in rec.results_move:
                self.env.cr.execute(
                    """ update stock_move set product_qty=round(product_qty::numeric, 0),product_uom_qty=round(product_uom_qty::numeric, 0),quantity_done=round(quantity_done::numeric, 0) where id=%s""",
                    (mv.move_line.id,))
            for mv in rec.results_move_line:
                self.env.cr.execute(
                    """ update stock_move_line set reserved_qty=round(reserved_qty::numeric, 0),reserved_uom_qty=round(reserved_uom_qty::numeric, 0),qty_done=round(qty_done::numeric, 0) where id=%s""",
                    ( mv.move_line.id,))
        self.load()

    def update_uom(self):
        for rec in self:
            if not rec.new_uom:
                return

            prod_id = self.env['product.product'].search([('product_tmpl_id', '=', rec.product_id.id)]).id
            #rec.product_id.write({'uom_id':rec.new_uom})

            self.env.cr.execute(
                """delete from stock_quant where product_id=%s""",
                (prod_id,))

            self.env.cr.execute(
                """insert into stock_quant (product_id,company_id,location_id,lot_id,create_uid,write_uid,inventory_date,quantity,reserved_quantity,inventory_diff_quantity,inventory_quantity_set,in_date,create_date,write_date,removal_date,warehouse_id,wh_type,branch_id)
                    select product_id,company_id,location_id,lot_id,2,2,'2023-12-31',0,0,0,false,'2023-06-30','2023-06-30','2023-06-30',(select i.removal_date from stock_lot i where i.id=stock_quant_summary.lot_id),
                    (select y.warehouse_id from stock_location y where y.id=stock_quant_summary.location_id),'PH',(select m.linked_analytic from stock_warehouse m where m.id=(select y.warehouse_id from stock_location y where y.id=stock_quant_summary.location_id)) from stock_quant_summary where product_id=%s""",
            (prod_id ,))

            self.env.cr.execute(
                """update stock_quant set wh_type=(select i.wh_type from stock_warehouse i where i.id=stock_quant.warehouse_id),inventory_diff_quantity=0, quantity=
                (select coalesce(sum(y.qty_done),0) from stock_move_line y where y.product_id=stock_quant.product_id and coalesce(y.lot_id,0)=coalesce(stock_quant.lot_id,0) and 
                y.location_dest_id=stock_quant.location_id and y.state='done')-(select coalesce(sum(y.qty_done),0) from stock_move_line y where y.product_id=
                stock_quant.product_id and coalesce(y.lot_id,0)=coalesce(stock_quant.lot_id,0) and y.location_id=stock_quant.location_id and y.state='done') where product_id=%s""",
                (prod_id,))

            self.env.cr.execute(
                """update stock_move_line set reserved_qty=0,reserved_uom_qty=0 where state in ('assigned','partially_available') and product_id=%s
                """,(prod_id,)
            )


            quants=self.env['stock.quant'].search([('product_id','=',prod_id)])
            for qu in quants:
                qu._get_on_hand()

            self.env.cr.execute(
                """ update product_template set uom_id=%s where id=%s""",
                (rec.new_uom.id,rec.product_id.id ))
        self.load()

class droga_update_stock_move(models.TransientModel):
    _name = 'droga.pharma.update.stock.move'
    header = fields.Many2one('droga.pharma.update.stock')
    move_line=fields.Many2one('stock.move')
    reference = fields.Char('reference',related='move_line.reference')
    product_uom_qty = fields.Float('Demand',related='move_line.product_uom_qty')
    product_uom = fields.Many2one('uom.uom', string='UOM',related='move_line.product_uom')
    quantity_done = fields.Float('Qty done',related='move_line.quantity_done')
    trans_date=fields.Datetime('Transaction date',related='move_line.date')
    from_loc = fields.Char('stock.warehouse',related='move_line.picking_id.from_wh')
    to_loc = fields.Char('stock.warehouse', related='move_line.picking_id.from_wh')
    origin = fields.Char(related='move_line.origin')
class droga_update_stock_move_line(models.TransientModel):
    _name = 'droga.pharma.update.stock.move.line'
    header = fields.Many2one('droga.pharma.update.stock')
    move_line = fields.Many2one('stock.move.line')
    reference = fields.Char('reference',related='move_line.move_id.reference')
    reserved_uom_qty = fields.Float('Reserved qty',related='move_line.reserved_uom_qty')
    product_uom = fields.Many2one('uom.uom', string='UOM',related='move_line.product_uom_id')
    qty_done = fields.Float('Qty done',related='move_line.qty_done')
    trans_date = fields.Datetime('Transaction date', related='move_line.move_id.date')
    from_loc = fields.Char('stock.warehouse', related='move_line.move_id.picking_id.from_wh')
    to_loc = fields.Char('stock.warehouse', related='move_line.move_id.picking_id.from_wh')
    lot_Name=fields.Many2one('stock.lot',realted='move_line.lot_id')
class droga_update_stock_move_po(models.TransientModel):
    _name = 'droga.pharma.update.po'
    header = fields.Many2one('droga.pharma.update.stock')
    po_line=fields.Many2one('purchase.order.line')
    reference=fields.Char('Reference',related='po_line.order_id.name')
    product_qty=fields.Float('Product quantity',related='po_line.product_qty')
    product_uom=fields.Many2one('uom.uom',string='UOM',related='po_line.product_uom')
    price_unit=fields.Float('Unit price',related='po_line.price_unit')
    qty_received = fields.Float('Qty received',related='po_line.qty_received')
    qty_to_invoice = fields.Float('Qty to invoice',related='po_line.qty_to_invoice')
    qty_invoiced = fields.Float('Qty invoiced',related='po_line.qty_invoiced')
