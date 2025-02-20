from odoo import fields, models, api
from odoo.exceptions import UserError


class droga_stock_adjustment_request(models.Model):
    _name = 'droga.stock.adjustment.request'
    _description = 'Store adjustment request'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', default='New')
    to_correct_ref = fields.Many2one('stock.picking', required=True)
    source_location_id = fields.Many2one(
        'stock.location', "Source location")
    dest_location_id = fields.Many2one(
        'stock.location', "Destination location")
    operation_type = fields.Many2one('stock.picking.type')
    request_date_time = fields.Datetime('Request Date', default=fields.Datetime.now)
    stock_adjustment_detail_entries = fields.One2many('droga.stock.adjustment.request.detail',
                                                      'stock_adjustment_header')
    order_from=fields.Char('Order from',default='IM')
    remark=fields.Char('Adjustment description',required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),  # When requester cancels it from draft
        ('stmg', 'Store manager'),  # Issue sent to store manager for warehouse allocation
        ('stmgp', 'Supply chain manager'),
        ('finmg', 'Finance approver'),
        ('finmgp', 'Finance pharmacy approver'),
        ('waiting', 'Requested'),  # When consignment is waiting for storekeeper to issue at warehouse
        ('reject', 'Rejected'),  # When request is rejected by issuer store keeper
        ('processed', 'Processed'),  # When request is processed
        ('done', 'Received'),  # When request is received
    ], string='Status', default="draft", readonly=True, tracking=True)
    store_manager = fields.Many2one('res.users', compute='_get_approvers')
    finance_wf_manager=fields.Many2one('res.users',compute='_get_approvers')
    finance_controller=fields.Many2one('res.users',compute='_get_approvers')
    def _get_approvers(self):
        for rec in self:
            if rec.order_from=="PH":
                rec.store_manager = self.env.ref("droga_pharma.pharma_supply_chain_manager").users.ids[0] if len(
                    self.env.ref("droga_pharma.pharma_supply_chain_manager").users.ids) > 0 else None

                rec.finance_wf_manager = self.env.ref("droga_pharma.pharma_fin").users.ids[0] if len(
                    self.env.ref("droga_pharma.pharma_fin").users.ids) > 0 else None

                rec.finance_controller = self.env.ref("droga_pharma.pharma_fin").users.ids[0] if len(
                    self.env.ref("droga_pharma.pharma_fin").users.ids) > 0 else None
            else:
                rec.store_manager = self.env.ref("droga_inventory.stores_manager").users.ids[0] if len(
                    self.env.ref("droga_inventory.stores_manager").users.ids) > 0 else None

                rec.finance_wf_manager=self.env.ref("droga_inventory.inv_prod_fin_wf").users.ids[0] if len(
                    self.env.ref("droga_inventory.inv_prod_fin_wf").users.ids) > 0 else None

                rec.finance_controller = self.env.ref("droga_inventory.inv_prod_fin").users.ids[0] if len(
                    self.env.ref("droga_inventory.inv_prod_fin").users.ids) > 0 else None

    @api.model
    def create(self, vals_list):
        if vals_list.get('name', 'New') == 'New':
            _name = self.env['ir.sequence'].next_by_code('droga.inventory.adjustment.request.sequence.all')
            if not _name:
                raise UserError("Order sequence not found.")
            vals_list['name'] = _name

        return super(droga_stock_adjustment_request, self).create(vals_list)

    def request(self):
        if len(self['stock_adjustment_detail_entries']) == 0:
            raise UserError("At least one product must be filled to request adjustement.")
        if len(self.env.ref("droga_inventory.stores_manager").users.ids)==0 or len(self.env.ref("droga_inventory.inv_prod_fin_wf").users.ids)==0 or len(self.env.ref("droga_inventory.inv_prod_fin").users.ids)==0:
            raise UserError("Stores manager or finance manger not configured, please contact IT for support.")
        self.set_activity_done()
        self.ensure_one()
        self.state = 'stmg'

    def amend(self):
        self.set_activity_done()
        self.ensure_one()
        self.state = 'draft'

    def action_cancel(self):
        self.state='cancel'

    def stmg_approve(self):
        self.set_activity_done()

        self.state = 'finmg'

    def fin_approve(self):
        self.set_activity_done()

        self.state = 'waiting'

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.name)])
        for act in activity:
            act.sudo().action_done()

    def action_open_adj(self):
        self.set_activity_done()

        mv_id=self.env['stock.picking'].search([('request_no','=',self.name)])
        if len(mv_id)==0:

            return {
                'name': 'Stock adjustement',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.picking',
                'view_id': self.env.ref('stock.view_picking_form').id,
                'type': 'ir.actions.act_window',
                'context': {
                    'default_origin': self.name,
                    'default_request_no': self.name,
                    'default_from_reconcile_menu':True,
                    'default_state':'draft',
                    'default_to_correct_pick':self.to_correct_ref.id
                }
            }
        else:
            return {
                'name': 'Stock adjustement',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.picking',
                'view_id': self.env.ref('stock.view_picking_form').id,
                'type': 'ir.actions.act_window',
                'res_id':mv_id[0].id,
                'context': {
                    'default_origin': self.name,
                    'default_request_no': self.name,
                    'default_from_reconcile_menu': True,
                    'default_state': 'draft',
                    'default_to_correct_pick': self.to_correct_ref.id
                }
            }

class droga_stock_adjustment_request_detail(models.Model):
    _name = 'droga.stock.adjustment.request.detail'
    _description = 'Store adjustment request detail'
    stock_adjustment_header = fields.Many2one('droga.stock.adjustment.request', required=True)

    product_id = fields.Many2one('product.product', index=True, required=True)
    product_uom = fields.Many2one('uom.uom', "UoM", store=True, compute='get_uom', inverse='set_uom', required=True,
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', store=True)
    lot_ser_no = fields.Many2one('stock.lot', string='Lot/Ser.No.')
    expiry_date = fields.Datetime('Expiry Date', related='lot_ser_no.expiration_date')
    ref=fields.Char(related='stock_adjustment_header.to_correct_ref.name')
    qty = fields.Float(
        'Quantity',
        digits='Product Unit of Measure', store=True,
        default=1.0, required=True, state={'done': [('readonly', True)]})

    @api.depends('product_id')
    def get_uom(self):
        for rec in self:
            rec.product_uom = rec.product_id.uom_id

    def set_uom(self):
        pass

    @api.model
    def create(self, vals):
        ref=self.env['droga.stock.adjustment.request'].search([('id','=',vals['stock_adjustment_header'] if vals else 0)]).to_correct_ref.name
        if len(self.env['stock.move'].search(
                [('reference', '=',ref ),
                 ('product_id', '=', vals['product_id'])])) == 0:
            item=self.env['product.product'].search([('id','=',vals['product_id'])])
            raise UserError("Item '%s' is not found under transaction %s." % (item.name, ref))
        return super(droga_stock_adjustment_request_detail, self).create(vals)
