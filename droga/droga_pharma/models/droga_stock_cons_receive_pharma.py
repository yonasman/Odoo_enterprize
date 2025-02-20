from operator import mod
from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.tools.view_validation import READONLY


class droga_stock_cons_receive_pharma(models.Model):
    _name = 'droga.inventory.consignment.receive.pharma'
    _description = 'Store Receive'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', default='New')
    supplier=fields.Many2one('res.partner',string='Supplier')
    cons_ref = fields.One2many('stock.picking', 'cons_receive_request_pharma',string='Store reference')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),  # When requester cancels it from draft
        ('scm', 'Supply chain manager'),  # Issue sent to supply chain manager for warehouse allocation
        ('waiting', 'Requested'),  # When consignment is waiting for storekeeper to issue at warehouse
        ('reject', 'Rejected'),  # When request is scm
        ('processed', 'Processed'),  # When request is processed
        ('done', 'Received'),  # When request is received
    ], string='Status', default="draft", readonly=True, tracking=True,
        help=" * Requested: The consignment receive order is sent to warehouse.\n"
             " * Done: The consignment items are received by warehouse.\n")

    detail_entries = fields.One2many('droga.inventory.cons.receive.detail.pharma', 'cons_header')
    warehouse_id = fields.Many2one(
        'stock.warehouse', "Receipt warehouse",
        required=True, check_company=True,
        state={'draft': [('readonly', False)]})

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id)
    remark = fields.Char('Remark')
    receipt_date = fields.Datetime('Receipt Date', default=fields.Datetime.now,
                                   state={'draft': [('readonly', False)]})

    consignment_reference = fields.Char(string='Order reference', default='', readonly=True)

    issue_type = fields.Selection([('CONR', 'Consignment recieve')],
                                  string='Return type', required=True,default='CONR')
    supply_chain_manager = fields.Many2one('res.users', compute='_get_approvers_pharma',store=True)

    @api.depends('state')
    def _get_approvers_pharma(self):
        for rec in self:

            rec.supply_chain_manager = self.env.ref("droga_pharma.pharma_supply_chain_manager").users.filtered(
            lambda m: self.env.company.id in m.company_ids.ids).ids[0] if len(
                self.env.ref("droga_pharma.pharma_supply_chain_manager").users.filtered(
            lambda m: self.env.company.id in m.company_ids.ids).ids) > 0 else None


    @api.model
    def create(self, vals_list):
        #self._get_approvers_pharma()
        if vals_list.get('name', 'New') == 'New':
            if len(vals_list['detail_entries'])==0:
                raise UserError("At least one product must be requested to save record.")
            _name = self.env['ir.sequence'].next_by_code('droga.inventory.consignment.receipt.sequence')
            if not _name:
                raise UserError("Order sequence not found.")
            vals_list['name']=_name
        return super(droga_stock_cons_receive_pharma, self).create(vals_list)

    def action_cancel(self):
        self.state = 'cancel'

    def request(self):
        self.set_activity_done()
        self.ensure_one()
        self.state = 'scm'

    def amend(self):
        self.set_activity_done()
        self.ensure_one()
        self.state = 'draft'
        self._get_approvers_pharma()

    def scm_approve(self):
        self.set_activity_done()

        pick_type_id = self.env['stock.picking.type'].sudo().search(
            [('sequence_code', '=','CONR'), ('warehouse_id', '=', self.warehouse_id.id)]).id
        if not pick_type_id :
            raise UserError("Picking type is not configured for one of the warehouses.")

        cons_vendor=self.env['stock.location'].search([('con_type', '=', self.issue_type)]).id

        if not cons_vendor:
            raise UserError("Consignment vendor location not set. Please configure accordingly.")


        pick_type_id = self.env['stock.picking.type'].sudo().search(
            [('sequence_code', '=','CONR'), ('warehouse_id', '=', self.warehouse_id.id)]).id
        def_loc_id = self.env['stock.location'].search(
            [('complete_name', 'like', self.warehouse_id.code + '/%'), ('con_type', '=', False), ('usage', '=', 'internal')])[
            0].id
        if not def_loc_id:
            raise UserError("Store location not set for receiver warehouse. Please configure accordingly.")

        picking_vals = {
            'partner_id': self.supplier.id,
            'company_id': self.env.company.id,
            'picking_type_id': pick_type_id,
            'location_id': cons_vendor,
            'location_dest_id': def_loc_id,
            'cons_receive_request_pharma': self.id,
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

            move_vals = {
                'picking_id': picking_id.id,
                'picking_type_id': pick_type_id,
                'name': picking_id.name,
                'product_id': rec['product_id'].id,
                'product_uom': rec["product_id"].uom_id.id,
                'product_uom_qty': rec['product_uom_qty']*(rec["product_id"].uom_id.factor/rec["product_uom"].factor),
                'price_unit': rec['price_unit_cons'],
                'location_id': cons_vendor,
                'location_dest_id': def_loc_id,
                'state': 'confirmed',
                'company_id': self.env.company.id
            }

            self.env['stock.move'].sudo().create(move_vals)

        #picking_id.sudo().action_confirm()
        picking_id.sudo().action_assign()

        self.state = 'waiting'

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.name)])
        for act in activity:
            act.sudo().action_done()


class droga_stock_cons_receive_detail_pharma(models.Model):
    _name = 'droga.inventory.cons.receive.detail.pharma'
    cons_header = fields.Many2one('droga.inventory.consignment.receive.pharma', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

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
    selling_price=fields.Float('Selling price',compute='get_sell_price',store=True)
    amount = fields.Float('Amount',compute='compute_amount')

    product_uom = fields.Many2one('uom.uom', "UoM", store=True, compute='get_uom', inverse='set_uom', required=True,
                                  domain="[('category_id', '=', product_uom_category_id)]")

    @api.depends('product_id')
    def get_sell_price(self):
        for rec in self:
            rec.selling_price=rec.product_id.product_tmpl_id.list_price_phar
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
            rec.product_uom = rec.product_id.import_uom_new

    def set_uom(self):
        pass

    # product_uom = fields.Many2one('uom.uom', "UoM", required=True, domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', store=True)


class droga_stock_picking_extension_pharma(models.Model):
    _inherit = 'stock.picking'

    cons_receive_request_pharma = fields.Many2one('droga.inventory.consignment.receive.pharma','Consignment receive request')