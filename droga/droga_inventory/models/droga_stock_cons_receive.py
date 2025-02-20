from operator import mod
from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.tools.view_validation import READONLY


class droga_stock_cons_receive(models.Model):
    _name = 'droga.inventory.consignment.receive'
    _description = 'Store Receive'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', default='New')
    supplier=fields.Many2one('res.partner',string='Supplier')
    cons_ref = fields.One2many('stock.picking', 'cons_receive_request',string='Store reference')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),  # When requester cancels it from draft
        ('stmg', 'Store manager'),  # Issue sent to store manager for warehouse allocation
        ('mg', 'Export manager'),
        ('waiting', 'Requested'),  # When consignment is waiting for storekeeper to issue at warehouse
        ('sc', 'Sent to CU'),
        ('reject', 'Rejected'),  # When request is rejected by issuer store keeper
        ('processed', 'Processed'),  # When request is processed

        ('done', 'Received'),  # When request is received
    ], string='Status', default="draft", readonly=True, tracking=True,
        help=" * Requested: The consignment receive order is sent to warehouse.\n"
             " * Done: The consignment items are received by warehouse.\n")

    detail_entries = fields.One2many('droga.inventory.cons.receive.detail', 'cons_header')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id)
    remark = fields.Char('Remark')
    receipt_date = fields.Datetime('Receipt Date', default=fields.Datetime.now,
                                   state={'draft': [('readonly', False)]})

    consignment_reference = fields.Char(string='Order reference', default='', readonly=True)

    issue_type = fields.Selection([('CONR', 'Consignment recieve'), ('SIR', 'Sample return'),('SUBL','Cleaning unit return')],
                                  string='Return type', required=True)
    marketting_manager = fields.Many2one('res.users', compute='_get_approvers',store=True)
    store_manager = fields.Many2one('res.users', compute='_get_approvers',store=True)
    menu_from = fields.Char('Menu opened from')
    def _get_approvers(self):
        for rec in self:
            rec.marketting_manager = self.env.ref("droga_inventory.marketing_manager").users.filtered(
                lambda m: self.env.company.id in m.company_ids.ids).ids[0] if len(
                self.env.ref("droga_inventory.marketing_manager").users.filtered(
                lambda m: self.env.company.id in m.company_ids.ids).ids) > 0 else None
            if rec.detail_entries[0].warehouse_id.wh_type == 'WS':
                rec.store_manager = self.env.ref("droga_inventory.stores_manager_ws").users.filtered(
                lambda m: self.env.company.id in m.company_ids.ids).ids[0] if len(
                    self.env.ref("droga_inventory.stores_manager_ws").users.filtered(
                lambda m: self.env.company.id in m.company_ids.ids).ids) > 0 else None
            else:
                rec.store_manager = self.env.ref("droga_inventory.stores_manager").users.filtered(
                lambda m: self.env.company.id in m.company_ids.ids).ids[0] if len(
                    self.env.ref("droga_inventory.stores_manager").users.filtered(
                lambda m: self.env.company.id in m.company_ids.ids).ids) > 0 else None

    @api.model
    def create(self, vals_list):
        self._get_approvers()
        if vals_list.get('name', 'New') == 'New':
            if len(vals_list['detail_entries'])==0:
                raise UserError("At least one product must be requested to save record.")
            _name = self.env['ir.sequence'].next_by_code('droga.inventory.consignment.receipt.sequence')
            if not _name:
                raise UserError("Order sequence not found.")
            vals_list['name']=_name
        return super(droga_stock_cons_receive, self).create(vals_list)

    def action_cancel(self):
        self.state = 'cancel'

    def request(self):
        self.set_activity_done()
        self.ensure_one()
        self.state = 'stmg'

    def amend(self):
        self.set_activity_done()
        self.ensure_one()
        self.state = 'draft'
        self._get_approvers()

    def stmg_approve(self):
        self.set_activity_done()
        warehouse_list=set(self.detail_entries['warehouse_id'])
        for wh in warehouse_list:
            pick_type_id = self.env['stock.picking.type'].sudo().search(
                [('sequence_code', '=','CONR'), ('warehouse_id', '=', wh.id)]).id
            if not pick_type_id :
                raise UserError("Picking type is not configured for one of the warehouses.")

        cons_vendor=self.env['stock.location'].search([('con_type', '=', self.issue_type)]).id

        if not cons_vendor:
            raise UserError("Consignment vendor location not set. Please configure accordingly.")

        for wh in warehouse_list:
            pick_type_id = self.env['stock.picking.type'].sudo().search(
                [('sequence_code', '=','CONR'), ('warehouse_id', '=', wh.id)]).id
            def_loc_id = self.env['stock.location'].search(
                [('complete_name', 'like', wh.code + '/%'), ('con_type', '=', False), ('usage', '=', 'internal')])[
                0].id
            if not def_loc_id:
                raise UserError("Store location not set for receiver warehouse. Please configure accordingly.")

            picking_vals = {
                'partner_id': self.supplier.id,
                'company_id': self.env.company.id,
                'picking_type_id': pick_type_id,
                'location_id': cons_vendor,
                'location_dest_id': def_loc_id,
                'cons_receive_request': self.id,
                #'auto_generated': True,
                #'origin': self.name,
                'state': 'confirmed',
                'scheduled_date': self.receipt_date
            }
            picking_id = self.env['stock.picking'].sudo().create(picking_vals)

            if not self.consignment_reference:
                self.consignment_reference = picking_id.name + '\n'
            else:
                self.consignment_reference = self.consignment_reference + picking_id.name + '\n'

            for rec in self.detail_entries:

                if(rec['warehouse_id']==wh):
                    move_vals = {
                        'picking_id': picking_id.id,
                        'picking_type_id': pick_type_id,
                        'name': picking_id.name,
                        'product_id': rec['product_id'].id,
                        'product_uom': rec['product_uom'].id,
                        'product_uom_qty': rec['product_uom_qty'],
                        'price_unit': rec['price_unit_cons'],
                        'location_id': cons_vendor,
                        'location_dest_id': def_loc_id,
                        'state': 'confirmed',
                        'company_id': self.env.company.id
                    }

                    self.env['stock.move'].sudo().create(move_vals)

            #picking_id.sudo().action_confirm()
            #picking_id.sudo().action_assign()

        self.state = 'waiting'

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.name)])
        for act in activity:
            act.sudo().action_done()


class droga_stock_cons_receive_detail(models.Model):
    _name = 'droga.inventory.cons.receive.detail'
    cons_header = fields.Many2one('droga.inventory.consignment.receive', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse', "Receipt warehouse",
        required=True, check_company=True,
        state={'draft': [('readonly', False)]})

    product_id = fields.Many2one(
        'product.product', 'Product',
        check_company=True,
        domain="[('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        index=True, required=True,
        state={'done': [('readonly', True)]})
    product_uom_qty = fields.Float(
        'Request',
        digits='Product Unit of Measure', store=True,
        default=1.0, required=True, state={'done': [('readonly', True)]})
    price_unit_cons = fields.Float('Unit price before VAT',store=True)

    amount = fields.Float('Amount',compute='compute_amount')

    product_uom = fields.Many2one('uom.uom', "UoM", store=True, compute='get_uom', inverse='set_uom', required=True,
                                  domain="[('category_id', '=', product_uom_category_id)]")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),  # When requester cancels it from draft
        ('stmg', 'Store manager'),  # Issue sent to store manager for warehouse allocation
        ('mg', 'Export manager'),
        ('waiting', 'Requested'),  # When consignment is waiting for storekeeper to issue at warehouse
        ('sc', 'Sent to CU'),
        ('reject', 'Rejected'),  # When request is rejected by issuer store keeper
        ('processed', 'Processed'),  # When request is processed

        ('done', 'Received'),  # When request is received
    ], string='Status', default="draft", readonly=True, tracking=True,related='cons_header.state',
        help=" * Requested: The consignment receive order is sent to warehouse.\n"
             " * Done: The consignment items are received by warehouse.\n")
    @api.depends('price_unit_cons', 'product_uom_qty')
    def compute_amount(self):
        for rec in self:
            try:
                rec.amount = rec.price_unit_cons*rec.product_uom_qty

            except Exception as e:
                rec.amount = 0

    @api.depends('product_id')
    def get_uom(self):
        for rec in self:
            if rec.product_id.import_uom_new:
                rec.product_uom = rec.product_id.import_uom_new
            else:
                rec.product_uom = rec.product_id.uom_id

    def set_uom(self):
        pass

    # product_uom = fields.Many2one('uom.uom', "UoM", required=True, domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', store=True)
    available_qty = fields.Float('Available', readonly=True, compute="get_count")

    @api.depends('state', 'product_id', 'product_uom', 'warehouse_id')
    def get_count(self):
        for rec in self:
            rate = rec.product_uom.factor / (
                rec.product_id.uom_id.factor if rec.product_id.uom_id.factor != 0 else (
                    rec.product_uom.factor if rec.product_uom.factor != 0 else 1))
            rec.available_qty = rec.available_qty + ((self._get_avail_qty_per_warehouse(rec.product_id,
                                                                                        rec.warehouse_id) - self._get_outgoing_qty_per_warehouse(
                rec.product_id, rec.warehouse_id)) * (rate))

    def _get_outgoing_qty_per_warehouse(self, product_id, warehouse_id):
        selfsud = self.sudo()
        moves = selfsud.env['stock.move'].search(
            [('product_id', '=', product_id.id), ('location_id.warehouse_id', '=', warehouse_id.id),
             ('location_id.usage', '=', 'internal'), ('location_dest_id.usage', '!=', 'internal'),
             ('state', 'not in', ['done', 'cancel', 'draft'])])
        return sum(moves.mapped('reserved_qty'))

    def _get_avail_qty_per_warehouse(self, product_id, warehouse_id):

        selfsud = self.sudo()
        tot_quantity = 0.0
        for location_id in selfsud.env['stock.location'].search(
                [('warehouse_id', '=', warehouse_id.id), ('usage', '=', 'internal')]):
            quants = selfsud.env['stock.quant'].search(
                [('product_id', '=', product_id.id), ('location_id', '=', location_id.id)])
            tot_quantity = tot_quantity + sum(quants.mapped('quantity'))
        return tot_quantity
