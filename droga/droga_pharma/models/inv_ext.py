import json
from datetime import datetime

import simplejson
from lxml import etree

from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.tools import get_lang


class droga_pharma_prod_ext(models.Model):
    _inherit = 'product.template'

    pharma_prod_categ=fields.Many2one('droga.pharma.prod.categ',string='Product category')
    pharma_filler=fields.Char(compute='_fill_fields')
    pharma_detailed_type = fields.Selection([
        ('counselling', 'Counselling'),('consu', 'Consumable'),('membershipcard', 'Membership E-Card'),('hthscreen','Health screening'),('mtmcard', 'MTM E-Card'),('Compounding','Compounding'),('product', 'Storable product'),
        ('service', 'Service')], string='Pharmacy Type', default='product', required=True)

    duration=fields.Integer('Membership duration in months')
    min_amt = fields.Integer('Membership minimum amount')
    mtm_discount=fields.Integer('Membership discount in %')

    no_of_sessions = fields.Integer('Number of sessions')
    tf_in_months = fields.Integer('Timeframe in months')

    screening_reagents= fields.Many2many('product.template', 'prod_screening', 'id',
                     string='Screening reagents')

    @api.depends('pharma_prod_categ','pharma_uom')
    def _fill_fields(self):
        for record in self:
            record.pharma_filler='-'
            record.detailed_type=record.pharma_detailed_type if not record.detailed_type else record.detailed_type
            record.categ_id = record.pharma_prod_categ.categ_id if not record.categ_id else record.categ_id
            record.uom_id = record.pharma_uom if not record.uom_id else record.uom_id
            record.order_type='ALL' if not record.order_type else record.order_type

    @api.model
    def create(self, vals_list):
        res = super(droga_pharma_prod_ext, self).create(vals_list)
        if not vals_list['categ_id']:
            raise UserError("Product category is mandatory.")
        if not vals_list['default_code']:
            raise UserError("Default code can not be empty.")
        return res

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):

        res = super().get_view(view_id, view_type, **options)

        doc = etree.XML(res['arch'])

        if view_type == 'form':
            if 'default_read_only' in self.env.context:
                if self.env.context['default_read_only']:

                    for node in doc.xpath("//field"):
                        if type(node.get("modifiers")) is str:
                            modifiers = json.loads(node.get("modifiers"))
                            modifiers['readonly'] = True
                            node.set("modifiers", json.dumps(modifiers))
                        else:
                            modifiers={}
                            modifiers['readonly'] = True
                            node.set("modifiers", json.dumps(modifiers))
                    res['arch'] = etree.tostring(doc, encoding='unicode')

        return res

class droga_pharma_dispensary_type(models.Model):
    _inherit = 'stock.location'

    pharmacy_location_type=fields.Selection([('Dispensary', 'Dispensary'), ('Store', 'Store'), ('Mix Location', 'Mix Location')],
                            default='Dispensary',string='Pharmacy Location')
    parent_loc_type=fields.Selection([
        ('IM','Import'),
        ('WS', 'Wholesale'),('PT','Physiotherapy'),
    ('PH', 'Pharmacy'),], string='Warehouse type.',related='warehouse_id.wh_type')

class droga_pharma_wh_has_dispensary(models.Model):
    _inherit = 'stock.warehouse'
    linked_analytic = fields.Many2one('account.analytic.account')

class droga_pharma_lot_extension(models.Model):
    _inherit = 'stock.lot'
    _rec_name='lot_descr'
    _order = 'expiration_date asc, name, id'
    lot_descr = fields.Char('Lot', compute='_get_lot_descr')

    def _get_lot_descr(self):
        for rec in self:
            if rec.expiration_date:
                rec.lot_descr=rec.name+' - '+str(rec.expiration_date.strftime("%b %d, %Y"))+' - '+str((rec.expiration_date - datetime.today()).days) +' days left'
            else:
                rec.lot_descr = rec.name

class droga_purchase_uom_extension(models.Model):
    _inherit = 'purchase.order.line'
    import_uom = fields.Many2one(related='product_id.import_uom_new', store=True)
    pharma_uom = fields.Many2one(related='product_id.uom_id', store=True)
    request_type=fields.Selection(related='order_id.request_type')

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To',related='order_id.picking_type_id')

    itemcode = fields.Char(related='product_id.default_code', store=True, string="Product")
    itemdesc = fields.Char(related='product_id.name', store=True, string="Description")

    product_uom_pharma=fields.Many2one('uom.uom')

    def open_purchase(self):
        return {
            'name': 'Purchase order',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'view_id': self.env.ref('purchase.purchase_order_form').id,
            'type': 'ir.actions.act_window',

            'res_id': self.order_id.id,
        }
    @api.onchange('product_uom_pharma', 'product_id')
    def _on_change_uom(self):
        for rec in self:
            if rec.order_id.request_type=='Pharmacy':
                rec.product_uom=rec.product_uom_pharma

    def _product_id_change(self):
        if not self.product_id:
            return

        # TODO: Remove when onchanges are replaced with computes
        if not (self.env.context.get('origin_po_id') and self.product_uom and self.product_id.uom_id.category_id == self.product_uom_category_id):
            if self.order_id.request_type=='Pharmacy':
                self.product_uom=self.product_uom_pharma
                self.product_uom_pharma=False
            else:
                self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.partner_id.lang).code,
            partner_id=self.partner_id.id,
            company_id=self.company_id.id,
        )
        self.name = self._get_product_purchase_description(product_lang)

        self._compute_tax_id()

class droga_stock_quant(models.Model):
    _inherit = 'stock.quant'
    warehouse_id = fields.Many2one('stock.warehouse', related='location_id.warehouse_id',store=True)
    branch_id=fields.Many2one('account.analytic.account', related='warehouse_id.linked_analytic',store=True)
    wh_type = fields.Selection([
        ('IM','Import'),
        ('WS', 'Wholesale'),('PT','Physiotherapy'),
    ('PH', 'Pharmacy'),('PR','Project')], related='warehouse_id.wh_type',store=True)
    unit_cost=fields.Float('Unit price',compute='get_cost')
    total_amount=fields.Float('Amount',compute='get_cost')
    selling_price=fields.Float(related='product_id.product_tmpl_id.list_price_phar')
    pharmacy_group_id = fields.Many2one('droga.prod.categ.pharma', related='product_id.product_tmpl_id.pharmacy_group_id')
    def get_cost(self):
        for rec in self:
            rec.unit_cost=rec.product_id.standard_price
            rec.total_amount=rec.unit_cost*rec.quantity

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(droga_stock_quant, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby,
                                                 lazy=lazy)
        if 'total_amount' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    total_amt = 0.0
                    for record in lines:
                        total_amt += record.total_amount
                    line['total_amount'] = total_amt

        return res

class droga_stock_move_line(models.Model):
    _inherit = 'stock.move'
    type=fields.Char('Type',compute='_get_type',store=True)
    unit_price=fields.Float('Unit price',compute='_get_up',store=True)
    tot_price=fields.Float('Total amount',compute='_get_up',store=True)
    warehouse_id = fields.Many2one('stock.warehouse', related='location_id.warehouse_id', store=True)
    warehouse_dest_id = fields.Many2one('stock.warehouse', related='location_dest_id.warehouse_id', store=True)
    branch_id = fields.Many2one('account.analytic.account',string='Branch', related='trans_warehouse.linked_analytic', store=True)
    branch_dest_id = fields.Many2one('account.analytic.account', related='warehouse_dest_id.linked_analytic', store=True)
    branch=fields.Many2one('account.analytic.account', compute='get_branch', store=True)

    @api.depends('branch_id', 'branch_dest_id')
    def get_branch(self):
        for record in self:
            if record.branch_id:
                record.branch=record.branch_id
            else:
                record.branch = record.branch_dest_id
    @api.depends('state')
    def _get_up(self):
        for rec in self:
            layer=self.env['stock.valuation.layer'].search([('stock_move_id','=',rec.id)])
            rec.unit_price=layer[0].unit_cost if layer else 0
            rec.tot_price=rec.unit_price*rec.quantity_done

    @api.depends('location_id','location_dest_id','state')
    def _get_type(self):
        for rec in self:
            if rec.location_id.usage=='internal' and rec.location_dest_id.usage=='customer':
                rec.type='Sales issue'
            elif rec.location_id.usage=='internal' and rec.location_dest_id.usage=='supplier':
                rec.type = 'Return'
            elif (rec.location_id.usage=='internal' and rec.location_dest_id.usage=='inventory') or (rec.location_id.usage=='inventory' and rec.location_dest_id.usage=='internal'):
                rec.type = 'Adjustement'
            elif rec.location_id.usage=='supplier' and rec.location_dest_id.usage=='internal':
                rec.type = 'Purchase receipt'
            elif rec.location_id.usage == 'internal' and rec.location_dest_id.usage == 'internal':
                rec.type = 'Transfer'
            elif rec.location_id.usage=='internal' and rec.location_dest_id.usage=='internal' and rec.location_dest_id.con_type=='SRL':
                rec.type = 'Transfer issue'
            elif rec.location_id.usage=='internal' and rec.location_dest_id.usage=='internal' and rec.location_id.con_type=='SRL':
                rec.type = 'Transfer receive'
            elif rec.location_id.usage=='internal' and rec.location_dest_id.usage=='internal' and rec.location_dest_id.con_type=='DIL':
                rec.type = 'Dispatch issue'
            elif rec.location_id.usage=='internal' and rec.location_dest_id.usage=='internal' and rec.location_id.con_type=='DIL':
                rec.type = 'Dispatch return'
            elif rec.location_id.usage=='internal' and rec.location_dest_id.con_type=='CONI':
                rec.type = 'Consigment issue'
            elif rec.location_id.usage=='internal' and rec.location_dest_id.con_type=='SAR':
                rec.type = 'Sample issue to return'
            elif rec.location_id.usage=='internal' and rec.location_dest_id.con_type=='SIR':
                rec.type = 'Sample issue'
            elif rec.location_id.usage=='internal' and rec.location_dest_id.con_type=='INC':
                rec.type = 'Internal transaction'
            elif rec.location_dest_id.usage=='internal' and rec.location_id.con_type=='SIR':
                rec.type = 'Sales return'
            else:
                rec.type='-'

class free_sample_issue_ext(models.Model):
    _inherit = 'droga.inventory.consignment.issue'
    points_to_deduct=fields.Float('Points to deduct')
    def dispense_products(self):

        #Check stock balance here
        order_lines_negative = self.detail_entries.filtered(
            lambda x: x.is_prod_available == 'False')
        if (len(order_lines_negative) > 0):
            raise UserError("There's no available item on hand to process the reward.")

        for rec in self.detail_entries:
            rec.product_uom=rec.product_uom_pharma
        self.set_activity_done()
        warehouse_list = set(self.detail_entries['warehouse_id'])

        for wh in warehouse_list:
            pick_type_id = self.env['stock.picking.type'].sudo().search(
                [('sequence_code', '=', 'RWD')]).id
            cust_locat = self.env['stock.location'].search([('con_type', '=', 'RWD')]).id
            if not pick_type_id:
                raise UserError("Picking type is not configured for one of the warehouses.")
            if not cust_locat:
                raise UserError(
                    "Customer location for type RWD not set. Please configure accordingly.")

        for wh in warehouse_list:
            # Get picking type for issue type per warehouse.
            # Issue type will be configured per warehouse.
            pick_type_id = self.env['stock.picking.type'].sudo().search(
                [('sequence_code', '=', 'RWD')]).id
            # Get default location for the warehouse
            def_loc_id = self.env['stock.location'].search(
                [('complete_name', 'like', wh.code + '/%'), ('con_type', '=', False), ('usage', '=', 'internal')])[
                0].id
            if not def_loc_id:
                raise UserError("Store location not set for issuer warehouse. Please configure accordingly.")

            picking_vals = {
                'partner_id': self.customer.id,
                'company_id': self.env.company.id,
                'picking_type_id': pick_type_id,
                'location_id': def_loc_id,
                'location_dest_id': cust_locat,
                'origin': self.name,
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
                        'product_uom': rec["product_id"].uom_id.id,
                        'product_uom_qty': rec['product_uom_qty'] ,
                        'location_id': def_loc_id,
                        'location_dest_id': cust_locat,
                        'state': 'confirmed',
                        'company_id': self.env.company.id
                    }

                    self.env['stock.move'].sudo().create(move_vals)

            picking_id.sudo().action_confirm()
            picking_id.sudo().action_assign()
            for move in picking_id.move_ids:
                move.quantity_done = move.product_uom_qty
            #picking_id.sudo().action_confirm()

            picking_id.button_validate()

        self.state = 'processed'

        if self.issue_type=='RWDB':
            points = {
                'type': 'Referral reward',
                'customer': self.customer.id,
                'earned_date': self.issue_date,
                'points_earned': self.points_to_deduct * -1,
            }

            self.env['droga.pharma.points.earned'].create(points)
        else:
            points = {
                'type': 'Discount for referral',
                'customer': self.customer.id,
                'earned_date': self.issue_date,
                'points_earned': self.points_to_deduct * -1,
            }

            self.env['droga.pharma.points.earned'].create(points)

class droga_stock_cons_issue_detail_inherit(models.Model):
    _inherit = 'droga.inventory.cons.issue.detail'
    is_prod_available = fields.Char(compute='is_prod_available_method',precompute=True)
    avail_char=fields.Char('Available')

    def _get_outgoing_qty_per_warehouse(self, product_id, warehouse_id):
        selfsud = self.sudo()
        moves = selfsud.env['stock.move'].search(
            [('product_id', '=', product_id.id), ('location_id.warehouse_id', '=', warehouse_id.id),
             ('location_id.usage', '=', 'internal'),('state', 'not in', ['done', 'cancel', 'draft','waiting','confirmed']),('location_dest_id.usage', '!=', 'internal')])
        return sum(moves.mapped('reserved_qty'))

    def _get_avail_qty_per_warehouse(self, product_id, warehouse_id):

        selfsud = self.sudo()
        tot_quantity = 0.0
        for location_id in selfsud.env['stock.location'].search(
                [('warehouse_id', '=', warehouse_id.id), ('usage', '=', 'internal'),('con_type','!=','SRL')]):
            quants = selfsud.env['stock.quant'].search(
                [('product_id', '=', product_id.id), ('location_id', '=', location_id.id)])
            tot_quantity = tot_quantity + sum(quants.mapped('quantity'))
        return tot_quantity

    @api.depends('product_id')
    def is_prod_available_method(self):
        selfsud = self.sudo()
        for rec in selfsud:
            available_qty = 0

            wh = rec.warehouse_id


            rate = round(rec.product_uom.factor / (
                rec.product_id.uom_id.factor if rec.product_id.uom_id.factor != 0 else (
                    rec.product_uom.factor if rec.product_uom.factor != 0 else 1)),6)
            available_qty = available_qty + ((selfsud._get_avail_qty_per_warehouse(rec.product_id,
                                                                                           wh) - selfsud._get_outgoing_qty_per_warehouse(
                rec.product_id, wh)) * (rate))

            rec.avail_char = str(available_qty)


            if rec.product_id.detailed_type == 'service':
                rec.is_prod_available = 'True'
                return
            prodqty = sum(self.cons_header.detail_entries.filtered(lambda x: x.product_id.id == rec.product_id.id).mapped(
                'product_uom_qty'))
            if available_qty < prodqty:
                rec.is_prod_available = 'False'
            elif available_qty >= prodqty:
                rec.is_prod_available = 'True'

class free_sample_detail(models.Model):
    _inherit = 'droga.inventory.cons.issue.detail'
    product_uom_pharma=fields.Many2one('uom.uom',string='UOM')
