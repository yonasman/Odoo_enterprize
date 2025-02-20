from odoo import models, fields, api
from odoo.exceptions import UserError

class droga_export_detail_ext(models.Model):
    _inherit = 'droga.inventory.cons.receive.detail'
    product_uom_qty_esti = fields.Float(
        'Request',
        digits='Product Unit of Measure', store=True,
        default=1.0, required=True)
    prodct_id_esti=fields.Many2one('product.product',store=True,string='Product from setup')
    @api.model
    def create(self, vals):
        if 'product_uom' not in vals:
            vals["product_uom"]=self.env["product.product"].search([('id','=',vals["product_id"])])[0].uom_id.id
        return super(droga_export_detail_ext, self).create(vals)

class inventory_return_extension(models.Model):
    _inherit = 'droga.inventory.consignment.receive'
    subcontractor_return_origin_form = fields.Many2one('droga.inventory.consignment.issue', readonly=True)
    export_manager = fields.Many2one('res.users', compute='_get_approvers')

    def _get_approvers(self):
        for rec in self:
            rec.export_manager = self.env.ref("droga_export.export_manager").users.ids[0] if len(
                self.env.ref("droga_export.export_manager").users.ids) > 0 else None

    def request_mg(self):
        self.set_activity_done()
        self.ensure_one()
        self.state = 'mg'

    def mg_approve(self):
        self.set_activity_done()
        warehouse_list = set(self.detail_entries['warehouse_id'])
        for wh in warehouse_list:
            pick_type_id = self.env['stock.picking.type'].sudo().search(
                [('sequence_code', '=', 'SUBL'), ('warehouse_id', '=', wh.id)]).id
            if not pick_type_id:
                raise UserError("Picking type SUBL is not configured for one of the warehouses.")

        cons_vendor = self.env['stock.location'].search([('con_type', '=', self.issue_type)]).id

        if not cons_vendor:
            raise UserError("SUBL location not set. Please configure accordingly.")

        for wh in warehouse_list:
            pick_type_id = self.env['stock.picking.type'].sudo().search(
                [('sequence_code', '=', 'SUBL'), ('warehouse_id', '=', wh.id)]).id
            def_loc_id = self.env['stock.location'].search(
                [('complete_name', 'like', wh.code + '/%'), ('con_type', '=', False), ('usage', '=', 'internal')])[
                0].id
            if not def_loc_id:
                raise UserError("Store location not set for receiver warehouse. Please configure accordingly.")

            picking_vals = {
                'partner_id': self.supplier.id,
                'company_id': self.company_id.id,
                'picking_type_id': pick_type_id,
                'location_id': cons_vendor,
                'location_dest_id': def_loc_id,
                'cons_receive_request': self.id,
                # 'auto_generated': True,
                'origin': self.subcontractor_return_origin_form.subcontract_issue_origin_form.name,
                'state': 'confirmed',
                'scheduled_date': self.receipt_date
            }
            picking_id = self.env['stock.picking'].sudo().create(picking_vals)

            if not self.consignment_reference:
                self.consignment_reference = picking_id.name + '\n'
            else:
                self.consignment_reference = self.consignment_reference + picking_id.name + '\n'

            for rec in self.detail_entries:

                if (rec['warehouse_id'] == wh):
                    move_vals = {
                        'picking_id': picking_id.id,
                        'picking_type_id': pick_type_id,
                        'name': picking_id.name,
                        'product_id': rec['product_id'].id,
                        'product_uom': rec['product_uom'].id,
                        'product_uom_qty': round(rec['product_uom_qty'],4),
                        'price_unit': rec['price_unit_cons'],
                        'location_id': cons_vendor,
                        'origin': self.subcontractor_return_origin_form.subcontract_issue_origin_form.name,
                        'location_dest_id': def_loc_id,
                        'state': 'confirmed',
                        'company_id': self.company_id.id
                    }

                    self.env['stock.move'].sudo().create(move_vals)

            # picking_id.sudo().action_confirm()
            # picking_id.sudo().action_assign()

        self.state = 'waiting'


class payment_request_export_extension(models.Model):
    _inherit = 'droga.account.payment.request'
    export_origin_form = fields.Many2one('sale.order', readonly=True)
    issue_export_origin_form = fields.Many2one('droga.inventory.consignment.issue', readonly=True)

class purchase_order_extension(models.Model):
    _inherit = 'purchase.order'
    export_origin_form = fields.Many2one('sale.order', readonly=True)

class droga_cost_buildup(models.Model):
    _name = 'droga.export.cost.buildup'
    type=fields.Many2one('droga.export.cost.type')
    type_apply=fields.Selection([('Finished', 'Finished'), ('By-product', 'By-product'),('All','All')],related='type.type_apply')
    issue_export_origin_form = fields.Many2one('droga.inventory.consignment.issue', readonly=True)
    payment_ref = fields.Many2one('account.move')
    currency_id = fields.Many2one('res.currency',related='payment_ref.currency_id')
    amount = fields.Monetary(related='payment_ref.amount_total_in_currency_signed',string='Amount',currency_field='currency_id')
    amount_for_order = fields.Float('Amount for order', required=True)
    remark = fields.Char('Remark')

    @api.onchange("payment_ref")
    def _on_ref_change(self):
        for record in self:
            record.amount_for_order = record.amount

class droga_cons_inherit(models.Model):
    _inherit = 'droga.inventory.consignment.issue'

    subcontract_issue_origin_form = fields.Many2one('sale.order', readonly=True,string='Cleaning unit origin')
    bag_issue_order = fields.Many2one('sale.order', readonly=True, string='Bag issue order')

    def cost_buildup(self):
        return {
            'name': 'Cost build-up (do not include processing cost)',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'droga.export.cost.buildup',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {
                'default_issue_export_origin_form': self.id,
            },
            'domain':
                ([('issue_export_origin_form', '=', self.id)])
        }

    def pay_req_open(self):
        return {
            'name': 'Payment request',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'droga.account.payment.request',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {
                'default_issue_export_origin_form': self.id,
            },
            'domain':
                ([('issue_export_origin_form', '=', self.id)])
        }

    def request_mg(self):
        self.set_activity_done()
        self.ensure_one()
        self.state = 'mg'

    def mg_approve(self):
        self.set_activity_done()
        warehouse_list = set(self.detail_entries['warehouse_id'])

        for wh in warehouse_list:

            if self.issue_type == 'BAGI':
                pick_type_id = self.env['stock.picking.type'].sudo().search(
                    [('sequence_code', '=', 'OUT'), ('warehouse_id', '=', wh.id)]).id
                if not pick_type_id:
                    raise UserError("Picking type delivery order is not configured for one of the warehouses.")
            else:
                pick_type_id = self.env['stock.picking.type'].sudo().search(
                    [('sequence_code', '=', 'SUBL'), ('warehouse_id', '=', wh.id)]).id
                if not pick_type_id:
                    raise UserError("Picking type SUBL is not configured for one of the warehouses.")

            if self.issue_type == 'BAGI':
                cust_locat = 5  # 5 is customers location
            else:
                cust_locat = self.env['stock.location'].search([('con_type', '=', self.issue_type)]).id

            if not cust_locat:
                raise UserError(
                    "Cleaning unit location for type " + self.issue_type + " not set. Please configure accordingly.")

        for wh in warehouse_list:
            # Get picking type for issue type per warehouse.
            # Issue type will be configured per warehouse.
            if self.issue_type == 'BAGI':
                pick_type_id = self.env['stock.picking.type'].sudo().search(
                    [('sequence_code', '=', 'OUT'), ('warehouse_id', '=', wh.id)]).id
                def_loc_id = 5
            else:
                pick_type_id = self.env['stock.picking.type'].sudo().search(
                    [('sequence_code', '=', 'SUBI'), ('warehouse_id', '=', wh.id)]).id
                def_loc_id = self.env['stock.location'].search(
                    [('complete_name', 'like', wh.code + '/%'), ('con_type', '=', False), ('usage', '=', 'internal')])[
                    0].id

            # Get default location for the warehouse

            if not def_loc_id:
                raise UserError("Store location not set for issuer warehouse. Please configure accordingly.")

            picking_vals = {
                'partner_id': self.customer.id,
                'company_id': self.company_id.id,
                'picking_type_id': pick_type_id,
                'location_id': def_loc_id,
                'location_dest_id': cust_locat,
                'origin': self.subcontract_issue_origin_form.name,
                'cons_sample_issue_request': self.id,
                'state': 'confirmed',
                'scheduled_date': self.issue_date
            }
            picking_id = self.env['stock.picking'].sudo().create(picking_vals)

            if not self.consignment_reference:
                self.consignment_reference = picking_id.name + '\n'
            else:
                self.consignment_reference = self.consignment_reference + picking_id.name + '\n'

            for rec in self.detail_entries:

                if (rec['warehouse_id'] == wh):
                    move_vals = {
                        'picking_id': picking_id.id,
                        'picking_type_id': pick_type_id,
                        'name': picking_id.name,
                        'product_id': rec['product_id'].id,
                        'product_uom': rec['product_uom'].id,
                        'product_uom_qty': round(rec['product_uom_qty'],4),
                        'location_id': def_loc_id,
                        'origin': self.subcontract_issue_origin_form.name,
                        'location_dest_id': cust_locat,
                        'state': 'confirmed',
                        'company_id': self.company_id.id
                    }

                    self.env['stock.move'].sudo().create(move_vals)

            # picking_id.sudo().action_confirm()
            # picking_id.sudo().action_assign()

        self.state = 'waiting'

    def sub_cont_return(self):
        if len(self.cons_ref.filtered(lambda x: (x.state=='done')))==0:
            raise UserError("Please send items to cleaning unit first before receving them.")

        items = []
        for det in self.detail_entries:
            raw_details = self.env['droga.export.items.composition'].search(
                [('raw_item', 'in', det.product_id.product_tmpl_id.ids)])
            if len(raw_details)==0:
                total_qty_finished=0
                total_qty_byproduct=0
            else:
                #Total number of finished goods
                total_qty_finished=det.product_uom_qty*sum(self.env['droga.export.items.composition.fin.goods'].search(
                    [('id', 'in', raw_details[0].items_detail.ids),('type','=','finish')]).mapped('rate_in_pct'))/100
                # Total number of byproduct goods
                total_qty_byproduct = det.product_uom_qty * sum(self.env['droga.export.items.composition.fin.goods'].search(
                    [('id', 'in', raw_details[0].items_detail.ids), ('type', '=', 'byproduct')]).mapped('rate_in_pct')) / 100
                #Total number sent to cleaning unit
            total_qty = det.product_uom_qty

            # Total cost for finished goods
            total_cost_build_finish=sum(self.env['droga.export.cost.buildup'].search([('issue_export_origin_form','=',self.id),('type_apply','=','Finished')]).mapped('amount_for_order'))
            # Total cost for byproduct goods
            total_cost_build_byproduct = sum(self.env['droga.export.cost.buildup'].search(
                [('issue_export_origin_form', '=', self.id), ('type_apply', '=', 'By-product')]).mapped('amount_for_order'))
            # Total cost for common costs
            total_cost_common = sum(self.env['droga.export.cost.buildup'].search(
                [('issue_export_origin_form', '=', self.id), ('type_apply', '=', 'All')]).mapped(
                'amount_for_order'))

            if total_qty_finished+total_qty_byproduct!=0:
                #This variable is used to add markup and accomodate waste material cost and priorate them to finished and by-products
                waste_increase_rate=total_qty/(total_qty_finished+total_qty_byproduct)

            if len(raw_details) > 0:
                for it in raw_details[0].items_detail:
                    if it['type'] == 'waste':
                        continue
                    if it['type'] == 'finish':
                        unit_cost=(it.items_header[0].raw_item.standard_price*waste_increase_rate) +(det.proc_cost*waste_increase_rate)+(total_cost_build_finish/total_qty_finished)+(total_cost_common/(total_qty_finished+total_qty_byproduct))
                    else:
                        unit_cost = (it.items_header[0].raw_item.standard_price*waste_increase_rate) + (det.proc_cost*waste_increase_rate) +(total_cost_build_byproduct/total_qty_byproduct)+(total_cost_common/(total_qty_finished+total_qty_byproduct))

                    uom_rate=det.product_id.product_tmpl_id.uom_id.factor/det.product_uom.factor

                    items.append({
                        'product_id': self.env['product.product'].search([('product_tmpl_id', '=', it['item'].id)])[
                            0].id,
                        'prodct_id_esti': self.env['product.product'].search([('product_tmpl_id', '=', it['item'].id)])[
                            0].id,
                        'product_uom_qty': uom_rate*det.product_uom_qty * it['rate_in_pct'] / 100,
                        'product_uom_qty_esti':uom_rate*det.product_uom_qty * it['rate_in_pct'] / 100,
                        'product_uom': it['item'].uom_id.id,


                        'price_unit_cons': unit_cost/uom_rate,

                        'company_id': self.env.company.id,
                        'warehouse_id': det['warehouse_id'].id,
                    })

        return {
            'name': 'cleaning unit items return',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'droga.inventory.consignment.receive',
            'views': [[self.env.ref('droga_export.droga_sub_contract_receive_view_tree').id, 'tree'],
                      [self.env.ref('droga_export.droga_sub_contract_receive_view_form').id, 'form']],
            'type': 'ir.actions.act_window',
            'context': {
                'default_issue_type': 'SUBL',
                'default_supplier':self.customer.id,
                'default_subcontractor_return_origin_form': self.id,
                'default_detail_entries': items
            },
            'domain': [('subcontractor_return_origin_form', '=', self.id)],
        }

class droga_cons_inherit_detail(models.Model):
    _inherit = 'droga.inventory.cons.issue.detail'
    proc_cost = fields.Float('Processing cost')
    tot_cost= fields.Float('Total',compute='_compute_tot_cost')
    product_amt=fields.Float('Total',compute='_compute_bag_cost')
    @api.depends('product_id','product_uom_qty')
    def _compute_bag_cost(self):
        for rec in self:
            rec.product_amt=rec.product_id.product_tmpl_id.standard_price*rec.product_uom_qty
    @api.onchange("product_id")
    def _on_change_fiscal_year(self):
        for rec in self:
            if rec.company_id.id==2:
                rec.warehouse_id=9
    @api.depends('product_uom_qty','proc_cost')
    def _compute_tot_cost(self):
        for rec in self:
            rec.tot_cost=rec.proc_cost*rec.product_uom_qty
    def write(self, vals):
        if self.company_id!=2:
            return super(droga_cons_inherit_detail, self).write(vals)
        result = super(droga_cons_inherit_detail, self).write(vals)
        if result.cons_header.subcontract_issue_origin_form:
            sale_details = result.subcontract_issue_origin_form.order_line
            raw_materials = self.env['droga.export.items.composition.fin.goods'].search([('item', 'in',
                                                                                          sale_details.product_id.product_tmpl_id.ids)]).items_header.raw_item.ids
            for sub_item in result.cons_header.detail_entries:
                if sub_item.product_id.product_tmpl_id.id not in raw_materials:
                    raise UserError(
                        "Item " + sub_item.product_id.default_code + ' - ' + sub_item.product_id.name + " is not raw material for any sales item.")
        return result

    @api.model
    def create(self, vals):
        if self.company_id!=2:
            return super(droga_cons_inherit_detail, self).create(vals)
        result = super(droga_cons_inherit_detail, self).create(vals)
        if result.cons_header.subcontract_issue_origin_form:
            sale_details = result.cons_header.subcontract_issue_origin_form.order_line
            raw_materials = self.env['droga.export.items.composition.fin.goods'].search([('item', 'in',
                                                                                          sale_details.product_id.product_tmpl_id.ids)]).items_header.raw_item.ids
            for sub_item in result.cons_header.detail_entries:
                if sub_item.product_id.product_tmpl_id.id not in raw_materials:
                    raise UserError(
                        "Item " + sub_item.product_id.default_code + ' - ' + sub_item.product_id.name + " is not raw material for any sales item.")
        return result


class droga_sale_inherit(models.Model):
    _inherit = 'sale.order'

    def subcontract_issue_open(self):
        itemsdetail=[]
        for ord in self.order_line:
            if len(self.env['droga.export.items.composition.fin.goods'].search([('item','=',ord.product_template_id.id),('type','=','finish')]))>0:
                prod_template=self.env['droga.export.items.composition.fin.goods'].search(
                    [('item', '=', ord.product_template_id.id), ('type', '=', 'finish')])[0].items_header.raw_item.id
                itemsdetail.append({
                    'company_id':self.company_id.id,
                    'product_id':self.env['product.product'].search(
                    [('product_tmpl_id', '=', prod_template)])[0].id,
                    'product_uom_qty':(ord.product_uom_qty*100)/self.env['droga.export.items.composition.fin.goods'].search([('item','=',ord.product_template_id.id),
                                                                                                   ('type','=','finish')])[0]['rate_in_pct']

                })
        return {
            'name': 'Cleaning unit issue',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'droga.inventory.consignment.issue',
            'views': [[self.env.ref('droga_export.droga_sales_subcontractor_issue_view_tree').id, 'tree'],
                      [self.env.ref('droga_export.droga_sales_subcontractor_issue_view_form').id, 'form']],
            'type': 'ir.actions.act_window',
            'context': {
                'default_issue_type': 'SUBL',
                'default_subcontract_issue_origin_form': self.id,
                'default_detail_entries':itemsdetail,
                'default_warehouse_id':9
            },
            'domain': [('subcontract_issue_origin_form', '=', self.id)],
        }

    def items_issue_order(self):
        return {
            'name': 'Bag items inventory issue order',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'droga.inventory.consignment.issue',
            'views': [[self.env.ref('droga_export.droga_sales_bag_issue_view_tree').id, 'tree'],
                      [self.env.ref('droga_export.droga_sales_bag_issue_view_form').id, 'form']],
            'type': 'ir.actions.act_window',
            'context': {
                'default_issue_type': 'BAGI',
                'default_bag_issue_order': self.id
            },
            'domain': [('bag_issue_order', '=', self.id)],
        }
    def export_status_list(self):
        if len(self.env['droga.export.status'].search([('status_origin_sales','=',self.id)]))==0:
            status_list=self.env['droga.export.status.list'].search([('status','=','Active')])
            for status in status_list:
                self.env['droga.export.status'].sudo().create({
                    'status_origin_sales':self.id,
                    'status':status.status_list,
                })
        return {
            'name': 'Export status',
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'droga.export.status',
            'type': 'ir.actions.act_window',
            'domain': [('status_origin_sales', '=', self.id)],
        }
    def pay_req_open(self):
        return {
            'name': 'Payment request',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'droga.account.payment.request',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {
                'default_export_origin_form': self.id,
            },
            'domain':
                ([('export_origin_form', '=', self.id)])
        }

    def po_open(self):
        return {
            'name': 'Purchase order',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {
                'default_export_origin_form': self.id,
                'default_request_type':'Local'
            },
            'domain':
                ([('export_origin_form', '=', self.id)])
        }
