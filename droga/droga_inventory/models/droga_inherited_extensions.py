from ast import literal_eval
from collections import defaultdict
from datetime import timedelta,datetime

import simplejson
from lxml import etree
#from pkg_resources import _

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, OrderedSet, float_compare


class droga_stock_move_line_extension(models.Model):
    _inherit = 'stock.move.line'

    location_id = fields.Many2one(
        'stock.location', 'From', domain="[('usage', '!=', 'view')]", check_company=True, required=True,
        compute="_compute_location_id", store=True, readonly=False, precompute=True,
    )
    location_dest_id = fields.Many2one('stock.location', 'To', domain="[('usage', '!=', 'view')]", check_company=True,
                                       required=True, compute="_compute_location_id", store=True, readonly=False,
                                       precompute=True)
    source_wh_type = fields.Selection([
        ('IM','Import'),('EX','Export'),
        ('WS', 'Wholesale'), ('PT', 'Physiotherapy'),
        ('PH', 'Pharmacy'), ('PR', 'Project')], compute='_get_source_type',store=True)

    @api.depends('location_id','location_dest_id')
    def _get_source_type(self):
        for rec in self:
            if rec.picking_type_id.code=='internal':
                rec.source_wh_type = 'IM'
            elif rec.location_id.usage == 'internal':
                rec.source_wh_type = rec.location_id.warehouse_id.wh_type
            else:
                rec.source_wh_type = rec.location_dest_id.warehouse_id.wh_type
    has_access = fields.Boolean('is_move_line_accessible', default=False, compute='_compute_has_access',
                                search='_search_has_access')
    has_read_access = fields.Boolean('is_move_line_accessible', default=False, compute='_compute_has_read_access',
                                search='_search_has_read_access')
    trans_type_detail = fields.Many2one('droga.inventory.transaction.types', 'Stock Move Detail',
                                        compute='_get_trans_type', store=True)
    trans_type = fields.Many2one('droga.inventory.transaction.types', 'Stock Move',
                                 compute='_get_trans_type', store=True)
    trans_warehouse = fields.Many2one('stock.warehouse', compute='_get_trans_type',store=True)
    import_quant = fields.Float('Quantity',compute='_get_on_hand',store=True)
    import_uom=fields.Many2one('uom.uom',related='product_id.import_uom_new')

    reserved_uom_qty_done = fields.Float('Reserved', compute='_get_on_hand')
    pharmacy_unit = fields.Boolean('Pharmacy unit', default=False, compute='_get_pharma_unit',store=True)
    fs_number=fields.Char('FS Number',compute='_get_fs_num',store=True,default=' ')

    def _get_fs_num(self):
        for rec in self:
            sale=self.env['account.move'].search([('invoice_origin','=',rec.move_id.origin)])
            if len(sale)>0:
                rec.fs_number=sale[0].FSInvoiceNumber
    @api.depends('move_id.pharmacy_unit')
    def _get_pharma_unit(self):
        for rec in self:
            if rec.move_id.pharmacy_unit:
                rec.pharmacy_unit = True
            else:
                rec.pharmacy_unit = False
    @api.onchange('import_quant')
    def _prod_qty_change(self):
        for rec in self:
            if rec.company_id.id==1 and rec.product_id.import_uom_new.factor!=0:
                rec.qty_done = rec.import_quant * (rec.product_id.uom_id.factor / rec.product_id.import_uom_new.factor)
            else:
                rec.qty_done = rec.import_quant

    @api.depends('qty_done','product_id.import_uom_new','reserved_uom_qty')
    def _get_on_hand(self):
        for rec in self:
            if rec.company_id.id==1 and rec.product_id.import_uom_new.factor!=0:
                rec.import_quant = rec.qty_done / (rec.product_id.uom_id.factor / rec.product_id.import_uom_new.factor)
                rec.reserved_uom_qty_done = rec.reserved_uom_qty / (
                        rec.product_id.uom_id.factor / rec.product_id.import_uom_new.factor)
            else:
                rec.import_quant = rec.qty_done
                rec.reserved_uom_qty_done = rec.reserved_uom_qty

    @api.depends('move_id.trans_type', 'move_id.trans_type_detail')
    def _get_trans_type(self):
        for rec in self:
            if rec.move_id:
                rec.trans_type = rec.move_id.trans_type
                rec.trans_type_detail = rec.move_id.trans_type_detail
                rec.trans_warehouse=rec.move_id.trans_warehouse
            else:
                rec.trans_type = False
                rec.trans_type_detail = False
                rec.trans_warehouse=False
    @api.onchange('result_package_id', 'product_id', 'product_uom_id', 'qty_done')
    def _onchange_putaway_location(self):
        if not self.id and self.user_has_groups(
                'stock.group_stock_multi_locations') and self.product_id and self.qty_done:
            qty_done = self.product_uom_id._compute_quantity(self.qty_done, self.product_id.uom_id)
            default_dest_location = self.location_dest_id
            self.location_dest_id = default_dest_location.with_context(exclude_sml_ids=self.ids)._get_putaway_strategy(
                self.product_id, quantity=qty_done, package=self.result_package_id,
                packaging=self.move_id.product_packaging_id)

    def _search_has_access(self, operator, value):

        if operator == '=':

            has_access = self.env['stock.move.line'].sudo().search(
                ['|',('location_id.has_access', '=', True),('location_dest_id.has_access', '=', True)])
            return [('id', 'in', [x.id for x in has_access] if has_access else False)]
        else:
            return [('id', 'in', [])]

    def _compute_has_access(self):
        for rec in self:

            if rec.location_id.has_access or rec.location_dest_id.has_access:
                rec.has_access = True
            else:
                rec.has_access = False

    def _search_has_read_access(self, operator, value):

        if operator == '=':

            has_read_access = self.env['stock.move.line'].sudo().search(
                ['|',('location_id.has_read_access', '=', True),('location_dest_id.has_read_access', '=', True)])
            return [('id', 'in', [x.id for x in has_read_access] if has_read_access else False)]
        else:
            return [('id', 'in', [])]

    def _compute_has_read_access(self):
        for rec in self:

            if rec.location_id.has_read_access or rec.location_dest_id.has_read_access:
                rec.has_read_access = True
            else:
                rec.has_read_access = False


    def _get_aggregated_product_quantities(self, **kwargs):
        aggregated_move_lines = super()._get_aggregated_product_quantities(**kwargs)
        for aggregated_move_line in aggregated_move_lines:
            rate = aggregated_move_lines[aggregated_move_line]['product'].product_tmpl_id.uom_id.factor/aggregated_move_lines[aggregated_move_line]['product'].product_tmpl_id.import_uom_new.factor
            aggregated_move_lines[aggregated_move_line]['qty_done'] = aggregated_move_lines[aggregated_move_line]['qty_done']/rate
            aggregated_move_lines[aggregated_move_line]['qty_ordered'] = aggregated_move_lines[aggregated_move_line][
                                                                          'qty_ordered'] / rate
            aggregated_move_lines[aggregated_move_line]['product_uom']=aggregated_move_lines[aggregated_move_line]['product'].product_tmpl_id.import_uom_new
        return aggregated_move_lines
class droga_warehouse_extension(models.Model):
    _inherit = 'stock.warehouse'
    has_access = fields.Boolean('is_loc_accessible', default=False, compute='_compute_has_access',
                                search='_search_has_access')
    has_no_access=fields.Boolean('is_loc_not_accessible', default=False, compute='_compute_has_access',
                                search='_search_has_no_access')
    has_dispensary_location = fields.Boolean("Has dispensary location")
    wh_type=fields.Selection([
        ('IM','Import'),('EX','Export'),
        ('WS', 'Wholesale'),('PT','Physiotherapy'),
    ('PH', 'Pharmacy'),('PR','Project')], string='Warehouse type.')

    def _search_has_no_access(self, operator, value):

        compiled_wh_domain=self.env.user.warehouse_ids_im_ws.mapped('code')+self.env.user.warehouse_ids_ph.mapped('code')

        if operator == '=':
            if len(compiled_wh_domain) == 0:
                return [('id', 'in', self.env['stock.warehouse'])]
            else:
                has_access = self.env['stock.warehouse'].sudo().search(
                    [('code', 'in', compiled_wh_domain)])
                return [('id', 'not in', [x.id for x in has_access] if has_access else False)]
        else:
            return [('id', 'in', self.env['stock.warehouse'])]

    def _search_has_access(self, operator, value):

        compiled_wh_domain=self.env.user.warehouse_ids_im_ws.mapped('code')+self.env.user.warehouse_ids_ph.mapped('code')

        if operator == '=':
            if len(compiled_wh_domain) == 0:
                return [('id', 'in', [])]
            else:
                has_access = self.env['stock.warehouse'].sudo().search(
                    [('code', 'in', compiled_wh_domain)])
                return [('id', 'in', [x.id for x in has_access] if has_access else False)]
        else:
            return [('id', 'in', [])]

    def _compute_has_access(self):
        compiled_wh_domain = []
        compiled_wh_domain=self.env.user.warehouse_ids_im_ws.mapped('code')+self.env.user.warehouse_ids_ph.mapped('code')

        for rec in self:
            if rec.code in compiled_wh_domain:
                rec.has_access = True
                rec.has_no_access = False
            else:
                rec.has_access = False
                rec.has_no_access = True

    def write(self, vals):
        for rec in self:
            if not self.env.user.has_group('droga_inventory.inv_prod_fin_wareloc'):
                raise UserError("You can not edit warehouse.")
        return super(droga_warehouse_extension, self).write(vals)

class droga_location_extension(models.Model):
    _inherit = 'stock.location'
    con_type = fields.Selection([
        ('CONI', 'Consignment customer location'),
        ('CONR', 'Consignment vendor location'),
        ('SIF', 'Free sample'),
        ('SIR', 'Sample issue to be returned'),
        ('SAR', 'Sample being returned'),
        ('DIL', 'Dispatch location'),
        ('RWD', 'Rewards location'),
        ('ATL', 'Asset transit location'),
        ('SAP','Sales placement location'),
        ('SRL', 'Inter-store receive transit location'),
        ('INC', 'Internal consumption'),
        ('SUBL', 'Cleaning unit location')
        ], string='Cons/sample Type')
    wcode=fields.Char(related='warehouse_id.code')
    has_access = fields.Boolean('is_loc_accessible', default=False, compute='_compute_has_access',
                                search='_search_has_access')
    has_read_access = fields.Boolean('is_loc_accessible', default=False, compute='_compute_has_read_access',
                                search='_search_has_read_access')
    def _search_has_access(self, operator, value):

        compiled_wh_domain=self.env.user.warehouse_ids_im_ws.mapped('code')+self.env.user.warehouse_ids_ph.mapped('code')

        if operator == '=':
            if len(compiled_wh_domain) == 0:
                return [('id', 'in', [])]
            else:
                has_access=self.env['stock.location']
                if self.env.user.has_group('droga_inventory.inventory_stk'):
                    has_access+= self.env['stock.location'].sudo().search(
                        [('wcode', 'in', compiled_wh_domain) ,('con_type','!=','DIL')])
                if self.env.user.has_group('droga_inventory.inventory_dm') :
                    has_access+= self.env['stock.location'].sudo().search(
                        [('wcode', 'in', compiled_wh_domain), ('con_type', '=', 'DIL')])

                return [('id', 'in', [x.id for x in has_access] if has_access else False)]
        else:
            return [('id', 'in', [])]

    def _search_has_read_access(self, operator, value):

        compiled_wh_domain=self.env.user.warehouse_ids_im_ws.mapped('code')+self.env.user.warehouse_ids_ph.mapped('code')+self.env.user.warehouse_ids_ph_disp.mapped('code')

        if operator == '=':
            if len(compiled_wh_domain) == 0 or not self.env.user.has_group('droga_inventory.inventory_report'):
                return [('id', 'in', [])]
            else:
                has_read_access=self.env['stock.location']
                has_read_access= self.env['stock.location'].sudo().search(
                    [('wcode', 'in', compiled_wh_domain)])

                return [('id', 'in', [x.id for x in has_read_access] if has_read_access else False)]
        else:
            return [('id', 'in', [])]

    def _compute_has_access(self):
        compiled_wh_domain=self.env.user.warehouse_ids_im_ws.mapped('code')+self.env.user.warehouse_ids_ph.mapped('code')

        for rec in self:
            if rec.wcode in compiled_wh_domain and ((self.env.user.has_group('droga_inventory.inventory_dm') and rec.con_type=='DIL') or
                                                    (self.env.user.has_group('droga_inventory.inventory_stk') and rec.con_type!='DIL')):
                rec.has_access = True
            else:
                rec.has_access = False

    def _compute_has_read_access(self):
        compiled_wh_domain=self.env.user.warehouse_ids_im_ws.mapped('code')+self.env.user.warehouse_ids_ph.mapped('code')

        for rec in self:
            if rec.wcode in compiled_wh_domain and self.env.user.has_group('droga_inventory.inventory_report'):
                rec.has_read_access = True
            else:
                rec.has_read_access = False

    def write(self, vals):
        for rec in self:
            if not self.env.user.has_group('droga_inventory.inv_prod_fin_wareloc') and (len(vals)!=1 or 'last_inventory_date' not in vals):
                raise UserError("You can not edit location.")
        return super(droga_location_extension, self).write(vals)

class droga_stock_picking_type_extension(models.Model):
    _inherit = 'stock.picking.type'
    warehouse_code=fields.Char(related='warehouse_id.code',store=True)
    dispatch_location = fields.Selection([
        ('IM', 'Import'),
        ('WS', 'Wholesale'), ], string='Dispatch location.')

    has_access=fields.Boolean('is_type_accessible',default=False,compute='_compute_has_access',search='_search_has_access')

    request_type = fields.Selection(
        [("Local", "Local"), ("Foregin", "Foregin"), ("Pharmacy", "Pharmacy")], default="Local")

    #Overridden to add domain to picking type openings
    def _get_action(self, action_xmlid):
        action = self.env["ir.actions.actions"]._for_xml_id(action_xmlid)
        if self:
            action['display_name'] = self.display_name

        default_immediate_tranfer = True
        if self.env['ir.config_parameter'].sudo().get_param('stock.no_default_immediate_tranfer'):
            default_immediate_tranfer = False

        context = {
            'search_default_picking_type_id': [self.id],
            'default_picking_type_id': self.id,
            'default_immediate_transfer': default_immediate_tranfer,
            'default_company_id': self.env.company.id,
        }
        domain = [('has_access','=',True)]

        action_context = literal_eval(action['context'])
        context = {**action_context, **context}
        action['context'] = context


        action['domain'] = domain
        return action
    def _search_has_access(self, operator, value):

        compiled_wh_domain = self.env.user.warehouse_ids_im_ws.mapped('code') + self.env.user.warehouse_ids_ph.mapped(
            'code')

        if operator=='=':
            if len(compiled_wh_domain)==0:
                return [('id','in',[])]
            else:
                has_access = self.env['stock.picking.type']
                if self.env.user.has_group('droga_inventory.inventory_stk'):
                    has_access+=self.env['stock.picking.type'].sudo().search([('warehouse_code','in',compiled_wh_domain),('dispatch_location','=',False)])
                if self.env.user.has_group('droga_inventory.inventory_dm'):
                    has_access+=(self.env['stock.picking.type'].sudo().search([('warehouse_code','in',compiled_wh_domain),('dispatch_location','!=',False)]))

                return [('id', 'in', [x.id for x in has_access] if has_access else False)]
        else:
            return [('id','in',[])]

    def _compute_has_access(self):
        compiled_wh_domain = self.env.user.warehouse_ids_im_ws.mapped('code') + self.env.user.warehouse_ids_ph.mapped(
            'code')

        for rec in self:
            if rec.warehouse_code in compiled_wh_domain:
                rec.has_access=True
            else:
                rec.has_access=False

class droga_stock_uom_extension(models.Model):
    _inherit = 'uom.uom'
    uom_title=fields.Char('UOM invoice name')

    @api.model
    def create(self, vals_list):
        if not self.env.user.has_group('droga_inventory.inv_uom_manager'):
            raise UserError("You can not create a unit of measure. Please contact your supervisor.")
        return super(droga_stock_uom_extension,self).create(vals_list)


    def write(self,vals_list):
        if not self.env.user.has_group('droga_inventory.inv_uom_manager'):
            raise UserError("You can not update a unit of measure. Please contact your supervisor.")
        return super(droga_stock_uom_extension, self).write(vals_list)

    def name_get(self):
        result = []
        for record in self:
            if self.env.context.get('show_title', False):
                # Only goes off when the custom_search is in the context values.
                result.append((record.id, record.uom_title))
            else:
                result.append((record.id, record.name))
        return result

class val_layer(models.Model):
    _inherit = 'stock.valuation.layer'
    reference = fields.Char(related='stock_move_id.reference',store=True)
    trans_type_detail = fields.Many2one('droga.inventory.transaction.types', 'Stock Move Detail', compute='_get_trans_type',store=True)
    trans_type = fields.Many2one('droga.inventory.transaction.types', 'Stock Move',
                                        compute='_get_trans_type', store=True)
    move_date=fields.Date('Stock move date',store=True)
    date_month = fields.Char(string='Date Month', compute='_get_date_month', store=True, readonly=True)
    warehouse=fields.Many2one('stock.warehouse',store=True,compute='_get_trans_type')
    origin=fields.Char(related='stock_move_id.origin',store=True)
    cr_date=fields.Datetime('Create date with adjustment',default=datetime.now())
    @api.depends('stock_move_id.trans_type','stock_move_id.trans_type_detail')
    def _get_trans_type(self):
        for rec in self:
            if rec.stock_move_id:
                rec.trans_type=rec.stock_move_id.trans_type
                rec.trans_type_detail = rec.stock_move_id.trans_type_detail
                rec.warehouse=rec.stock_move_id.trans_warehouse
            else:
                rec.trans_type = False
                rec.trans_type_detail = False
                rec.warehouse = False

    @api.depends('move_date')
    def _get_date_month(self):
        for rec in self:
            if rec.move_date:
                rec.date_month = rec.move_date.month
            else:
                rec.date_month='0'

    @api.model
    def create(self, vals):
        ret = super(val_layer, self).create(vals)

        for res in ret:
            if res.product_id.product_tmpl_id.adj_date:
                vals['cr_date']=res.product_id.product_tmpl_id.adj_date
                res.write({'cr_date':datetime.combine(res.product_id.product_tmpl_id.adj_date, datetime.min.time())})
                #res.account_move_id.write({'date':datetime.combine(res.product_id.product_tmpl_id.adj_date, datetime.min.time())})
                #for mv in res.account_move_id.line_ids:
                #    mv.write({'date':datetime.combine(res.product_id.product_tmpl_id.adj_date, datetime.min.time())})

        if ret.origin:
            if ret.origin.startswith('SOD'):
                acc_move = self.env['account.move'].search([('invoice_origin', '=', ret.origin)])
                for mv in acc_move:
                    mv.sales_cost = abs(
                        sum(self.env['stock.valuation.layer'].search([('origin', '=', ret.origin)]).mapped('value')))
        return ret

class droga_inv_account_move(models.Model):
    _inherit = 'account.move'
    @api.model
    def create(self,vals):
        to_ret=super(droga_inv_account_move, self).create(vals)
        if to_ret.stock_move_id:
            to_ret.date=to_ret.stock_move_id.date
            for mv in to_ret.line_ids:
                mv.date=to_ret.stock_move_id.date
        return to_ret

class stock_move_mail_added(models.Model):
    _name = "stock.move"
    _inherit = ['stock.move','mail.thread', 'mail.activity.mixin', 'image.mixin']

class droga_stock_move_extension(models.Model):
    _inherit = 'stock.move'
    from_reconcile_menu=fields.Boolean(related='picking_id.from_reconcile_menu')
    reservation_discard_time=fields.Datetime(string='Reservation cancel time',compute='_compute_res_discard',inverse='_inverse_res_discard')
    reserve_indef=fields.Boolean('Reserve indefinitely',default=False,tracking=True)
    source_wh=fields.Char(related='location_id.warehouse_id.name')
    source_wh_type = fields.Selection([
        ('IM','Import'),('EX','Export'),
        ('WS', 'Wholesale'),('PT','Physiotherapy'),
    ('PH', 'Pharmacy'),('PR','Project')],compute='_get_source_type',store=True)
    pharmacy_unit = fields.Boolean('Pharmacy unit', default=False,compute='_get_pharma_unit',store=True)
    cons_price=fields.Float('Consignment payable')



    @api.depends('picking_id.pharmacy_unit')
    def _get_pharma_unit(self):
        for rec in self:
            if rec.picking_id.pharmacy_unit:
                rec.pharmacy_unit=True
            else:
                rec.pharmacy_unit = False

    @api.depends('location_id', 'location_dest_id')
    def _get_source_type(self):
        for rec in self:
            if rec.picking_type_id.code=='internal':
                rec.source_wh_type='IM'
            elif rec.location_id.usage=='internal':
                rec.source_wh_type=rec.location_id.warehouse_id.wh_type
            else:
                rec.source_wh_type = rec.location_dest_id.warehouse_id.wh_type

    trans_type=fields.Many2one('droga.inventory.transaction.types',string='Type',compute='_get_trans_type',store=True)
    trans_type_detail = fields.Many2one('droga.inventory.transaction.types', string='Type Detail', compute='_get_trans_type',
                                 store=True)
    trans_warehouse=fields.Many2one('stock.warehouse',compute='_get_wareh',store=True)
    from_to=fields.Many2one('stock.warehouse',string='From/To (Inter-store)',compute='_get_trans_type',store=True)

    itemcode = fields.Char(related='product_id.default_code', store=True,string="Product")
    itemdesc = fields.Char(related='product_id.name', store=True,string="Description")

    import_quant = fields.Float('Demand',compute='_get_on_hand',store=True)
    import_quant_done = fields.Float('Done', compute='_get_on_hand', store=True)
    reserved_availability_done=fields.Float('Reserved', compute='_get_on_hand')
    import_uom = fields.Many2one('uom.uom', related='product_id.import_uom_new')

    @api.depends('product_uom_qty','product_id.import_uom_new')
    def _get_on_hand(self):
        for rec in self:
            if rec.company_id.id==1 and rec.product_id.import_uom_new.factor!=0:
                rec.import_quant = rec.product_uom_qty / (rec.product_id.uom_id.factor / rec.product_id.import_uom_new.factor)
                rec.import_quant_done = rec.quantity_done / (rec.product_id.uom_id.factor / rec.product_id.import_uom_new.factor)
                rec.reserved_availability_done=rec.reserved_availability / (rec.product_id.uom_id.factor / rec.product_id.import_uom_new.factor)
            else:
                rec.import_quant = rec.product_uom_qty
                rec.import_quant_done = rec.quantity_done
                rec.reserved_availability_done = rec.reserved_availability
    @api.depends('state')
    def _get_wareh(self):
        for rec in self:
            if rec.location_id.usage=='internal' and rec.location_dest_id.usage!='internal':
                rec.trans_warehouse=rec.location_id.warehouse_id.id
            elif rec.location_id.usage!='internal' and rec.location_dest_id.usage=='internal':
                rec.trans_warehouse = rec.location_dest_id.warehouse_id.id
            #If sender has con_type, it's probably store issue return else it's consigment... so warehouse will be set accordingly
            elif rec.location_id.con_type:
                rec.trans_warehouse = rec.location_dest_id.warehouse_id.id
            else:
                rec.trans_warehouse = rec.location_id.warehouse_id.id

    def get_nth_char(self,type_str, n):
        if n < 1:
            return 'L'

        if n > len(type_str):
            return 'L'

        return type_str[n - 1]

    @api.depends('state')
    def _get_trans_type(self):
        for rec in self:
            trans_type = self.env["droga.inventory.transaction.types"].search(
                [('from_loc', '=', rec.location_id.usage),('to_loc', '=', rec.location_dest_id.usage),('summary_detail','=','summary'),('id','not in',(45,47))])
            if len(trans_type)==0:
                rec.trans_type=False
                rec.trans_type_detail = False
            else:
                rec.trans_type=trans_type[0].id
                if trans_type[0].has_detail:
                    if trans_type[0].id==26:
                        if rec.origin:
                            if self.get_nth_char(rec.origin, 5)== 'F':
                                rec.trans_type_detail = 43
                            else:
                                rec.trans_type_detail = 44
                        else:
                            rec.trans_type_detail = 44
                    elif trans_type[0].id==29:
                        if rec.origin:
                            if self.get_nth_char(rec.origin,5)=='F':
                                rec.trans_type_detail = 41
                            else:
                                rec.trans_type_detail = 42
                        else:
                            rec.trans_type_detail = 42
                    elif trans_type[0].id == 25 or trans_type[0].id == 28:
                        trans_type_det = self.env["droga.inventory.transaction.types"].search(
                            [('to_con_type', '=', rec.location_dest_id.con_type)])
                        if len(trans_type_det) == 0:
                            rec.trans_type_detail = trans_type[0].id
                        else:
                            rec.trans_type_detail = trans_type_det[0].id
                    else:
                        trans_type_det = self.env["droga.inventory.transaction.types"].search(
                            [('from_loc', '=', rec.location_id.usage), ('to_loc', '=', rec.location_dest_id.usage),
                             ('summary_detail', '=', 'detail'),'|',('from_con_type','=',rec.location_id.con_type),('to_con_type','=',rec.location_dest_id.con_type)])
                        if len(trans_type_det)==0:
                            rec.trans_type_detail = trans_type[0].id
                        else:
                            rec.trans_type_detail = trans_type_det[0].id
                else:
                    rec.trans_type_detail = trans_type[0].id

            if rec.trans_type_detail.id==31:
                #If it's inter store issue, other warehouse is receiver
                rec.from_to=rec.location_dest_id.warehouse_id.id
            elif rec.trans_type_detail.id==30:
                #Get sender moves cause it's inter-store receive
                origin=self.env["stock.move"].search(
                    [('reference','=',rec.origin)]
                )
                if len(origin)==0:
                    rec.from_to = rec.location_id.warehouse_id.id
                else:
                    rec.from_to = origin[0].location_id.warehouse_id.id     #Sender location
                rec.from_to = rec.location_dest_id.warehouse_id.id
            else:
                rec.from_to=False

    def _inverse_res_discard(self):
        pass

    def view_reg_hist(self):
        return {
            'name': 'Reservation log',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'view_id': self.env.ref('droga_inventory.droga_inventory_stock_move_reservation_form').id,
            'type': 'ir.actions.act_window',

            # This will pass the detail ID if a record is present
            'res_id': self.id,
        }

    def _compute_res_discard(self):
        for rec in self:
            rec.reservation_discard_time=rec.date+timedelta(hours=rec.product_id.categ_id.reservation_period)

    def create_dont_run(self, vals_list):
        res=super(droga_stock_move_extension, self).create(vals_list)

        so = self.env['sale.order'].search([('name', '=', res.origin)])
        show = so[0].payment_term_id.deliv_after_payment if len(so) > 0 else False
        if show:
            res.do_unreserve()
        return res

    def unreserve_discarded_entries(self):
        moves=self.env['stock.move'].search([('state','!=','done'),('reservation_discard_time','<',datetime.now()),('reserved_availability','>',0.0)])
        for move in moves:
            move._do_unreserve()

    has_access = fields.Boolean('is_move_accessible', default=False, compute='_compute_has_access',
                                search='_search_has_access')
    has_read_access = fields.Boolean('is_move_accessible', default=False, compute='_compute_has_read_access',
                                search='_search_has_read_access')

    reserved_qty=fields.Float('Reserved qty',default=0,tracking=True)

    def update_stock_res_qty(self):
        to_update=self.env['stock.move'].search([('reserve_indef','=',False),('reserved_qty','!=',0),
                                                 ('state','not in',['done','cancel','draft'])])
        for upd in to_update:
            if upd['reservation_discard_time']<datetime.now():
                upd.write({'reserved_qty':0})

    def _search_has_access(self, operator, value):

        if operator == '=':
            has_access = self.env['stock.move'].sudo().search(
                #['|',('location_id.has_access', '=', True),('location_dest_id.has_access', '=', True)])
                ['|','&', ('location_id.has_access', '=', True),('location_id.con_type', '!=', 'SRL'), '&',('location_dest_id.con_type', '!=', 'SRL'),('location_dest_id.has_access', '=', True)])

            if self.env.user.has_group('droga_inventory.inventory_dmi'):
                has_access += (self.env['stock.move'].sudo().search([('picking_type_id.dispatch_location', '=', 'IM')]))
            if self.env.user.has_group('droga_inventory.inventory_dmw'):
                has_access += (self.env['stock.move'].sudo().search([('picking_type_id.dispatch_location', '=', 'WS')]))


            return [('id', 'in', [x.id for x in has_access] if has_access else False)]
        else:
            return [('id', 'in', [])]


    def _compute_has_access(self):
        for rec in self:

            if rec.location_id.has_access or rec.location_dest_id.has_access:
                rec.has_access = True
            else:
                rec.has_access = False

    def _search_has_read_access(self, operator, value):

        if operator == '=':
            has_read_access = self.env['stock.move'].sudo().search(
                ['|', ('location_id.has_read_access', '=', True),('location_dest_id.has_read_access', '=', True)])

            return [('id', 'in', [x.id for x in has_read_access] if has_read_access else False)]
        else:
            return [('id', 'in', [])]

    def _compute_has_read_access(self):
        for rec in self:

            if rec.location_id.has_read_access or rec.location_dest_id.has_read_access:
                rec.has_read_access = True
            else:
                rec.has_read_access = False

    def write(self,vals_list):
        if 'date' in vals_list:
            for res in self:
                if res.location_id.name == 'Inventory adjustment' or res.location_dest_id.name == 'Inventory adjustment' and res.product_id.product_tmpl_id.adj_date:
                    try:
                        vals_list['date'] = datetime.combine(res.product_id.product_tmpl_id.adj_date, datetime.min.time())
                        for mv_line in res.move_line_ids:
                            mv_line.date = datetime.combine(res.product_id.product_tmpl_id.adj_date, datetime.min.time())
                    except:
                        raise ValidationError("Please use excel file template with FINANCE for posting shortage and overage transactions.")
        return super(droga_stock_move_extension, self).write(vals_list)

    @api.model
    def create(self, vals_list):
        vals_list['reserved_qty']=vals_list['product_uom_qty']
        if 'origin' in vals_list:
            if type(vals_list['origin']) is str:
                if vals_list["origin"].startswith('PO-'):
                    sup = self.env['purchase.order'].search(
                    [('name', '=', vals_list["origin"])])
                    vals_list["partner_id"]=sup[0]["partner_id"].id

        return super(droga_stock_move_extension, self).create(vals_list)

    def unlink_(self):
        raise ValidationError(
            "You can't delete inventory transaction, either cancel it or pass a correcting entry.")

    def _search_picking_for_assignation_domain(self):
        domain = [
            ('group_id', '=', self.group_id.id),
            ('location_id', '=', self.location_id.id),
            ('location_dest_id', '=', self.location_dest_id.id),
            ('picking_type_id', '=', self.picking_type_id.id),
            ('printed', '=', False),
            ('immediate_transfer', '=', False),
            ('state', 'in', ['draft', 'confirmed', 'waiting', 'partially_available', 'assigned'])]
        if self.partner_id and (self.location_id.usage == 'transit' or self.location_dest_id.usage == 'transit'):
            domain += [('partner_id', '=', self.partner_id.id)]
        return domain

    def _search_picking_for_assignation(self):
        if self.location_id.con_type=='SRL' or  self.location_dest_id.con_type=='SRL':
            return False
        else:
            return super(droga_stock_move_extension,self)._search_picking_for_assignation()


class droga_stock_picking_extension(models.Model):
    _inherit = 'stock.picking'

    trans_issue_request=fields.Many2one('droga.inventory.transfer.custom','Transfer request')
    office_request = fields.Many2one('droga.inventory.office.supplies.request', 'Office supplies request')
    cons_sample_issue_request = fields.Many2one('droga.inventory.consignment.issue','Cons/sample issue request')
    cons_receive_request = fields.Many2one('droga.inventory.consignment.receive','Consignment receive request')
    state = fields.Selection(selection_add=[('processed', 'Processed')])
    delivery_order_show=fields.Boolean(default=True)
    warehouse_list=fields.Many2many('stock.warehouse')
    from_wh = fields.Char('From location',compute='_get_loc_descr')
    to_wh = fields.Char('To location',compute='_get_loc_descr')
    has_access = fields.Boolean('is_pick_accessible', default=False, compute='_compute_has_access',
                                search='_search_has_access')
    from_reconcile_menu=fields.Boolean('Menu is opened from reconciliation menu',default=False)
    to_correct_ref=fields.Char('To correct reference')
    to_correct_pick = fields.Many2one('stock.picking',string='To correct reference')
    request_no=fields.Char('Request No')
    remark = fields.Char('Remark')
    requested_by=fields.Char('Requested by')
    location_id_type=fields.Selection([
        ('CONI', 'Consignment customer location'),
        ('CONR', 'Consignment vendor location'),
        ('SIF', 'Free sample'),
        ('SIR', 'Sample issue to be returned'),
        ('SAR', 'Sample being returned'),
        ('SAP','Sales placement location'),
        ('SRL', 'Inter-store receive transit location'),
        ], string='Cons/sample Type',related='location_id.con_type')
    location_dest_id_type = fields.Selection([
        ('CONI', 'Consignment customer location'),
        ('CONR', 'Consignment vendor location'),
        ('SIF', 'Free sample'),
        ('SIR', 'Sample issue to be returned'),
        ('SAR', 'Sample being returned'),
        ('SAP','Sales placement location'),
        ('SRL', 'Inter-store receive transit location'),
        ], string='Cons/sample Type',related='location_dest_id.con_type')
    pharmacy_unit=fields.Boolean('Pharmacy unit',default=False,store=True)

    def _check_expired_lots(self):
        return False

    def _get_loc_descr(self):
        for rec in self:
            rec.from_wh=rec.location_id.warehouse_id.name if rec.location_id.warehouse_id else rec.location_id.name
            rec.to_wh = rec.location_dest_id.warehouse_id.name if rec.location_dest_id.warehouse_id else rec.location_dest_id.name
    def unlink(self):
        raise ValidationError(
            "You can't delete inventory transactions.")
    def _search_has_access(self, operator, value):

        if operator == '=':
            has_access = self.env['stock.picking'].sudo().search(
                #['|',('location_id.has_access', '=', True),('location_dest_id.has_access', '=', True)])
                ['|','&', ('location_id.has_access', '=', True),('location_id.con_type', '!=', 'SRL'), '&',('location_dest_id.con_type', '!=', 'SRL'),('location_dest_id.has_access', '=', True)])

            if self.env.user.has_group('droga_inventory.inventory_dmi'):
                has_access += (self.env['stock.picking'].sudo().search([('picking_type_id.dispatch_location', '=', 'IM')]))
            if self.env.user.has_group('droga_inventory.inventory_dmw'):
                has_access += (self.env['stock.picking'].sudo().search([('picking_type_id.dispatch_location', '=', 'WS')]))


            return [('id', 'in', [x.id for x in has_access] if has_access else False)]
        else:
            return [('id', 'in', [])]

    def _compute_has_access(self):
        compiled_wh_domain = []
        user_groups_list = self.env.user.groups_id
        for user_group in user_groups_list:
            given_ules = user_group.rule_groups
            for rule in given_ules:
                if 'Warehouse' in rule.model_id.name:
                    compiled_wh_domain.append(
                        rule.domain_force.strip().replace("[('code', '=', ", '').replace("'", '').replace(')]', ''))

        for rec in self:

            if rec.location_id.has_access or rec.location_dest_id.has_access:
                rec.has_access = True
            else:
                rec.has_access = False

    @api.model
    def create(self, vals_list):
        res=super(droga_stock_picking_extension, self).create(vals_list)
        so=self.env['sale.order'].search([('name','=',res.origin)])
        show=so[0].payment_term_id.deliv_after_payment if len(so)>0 else False
        res.do_unreserve()
        if show:
            res.delivery_order_show=False
        return res

    def action_purchase_request(self):
        return {
            'name': 'Purchase request',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.purhcase.request',
            'view_id': self.env.ref('droga_procurement.droga_purhcase_request_view_form').id,
            'type': 'ir.actions.act_window',

            # This will pass the detail ID if a record is present
            #'res_id': self.performance_security.id,

            # When target is new, it will popup else it will use it's own form, wow ferenj
            #'target': 'new',

            # Context is used to pass information, on another note domain is used to filter information
            'context': {
                'default_store_origin_form': self.id,
            }
        }

    def button_validate(self):
        if self.trans_issue_request:
            self.trans_issue_request.write({'state': 'processed'})
        sender=self.env['stock.picking'].search([('name','=',self.origin)])
        if len(sender)>0:
            if sender[0].trans_issue_request.state=="processed":
                sender[0].trans_issue_request.write({'state': 'done'})
        if self.office_request:
            self.office_request.write({'state': 'processed'})
        if self.cons_sample_issue_request:
            self.cons_sample_issue_request.write({'state': ('done' if 'issue_type'=='SAP' else 'processed')})
        if self.cons_receive_request:
            self.cons_receive_request.write({'state': 'done'})

        to_update = self.env['droga.stock.adjustment.request'].search(
            [('name', '=', self['origin'])]
        )
        if len(to_update)>0:
            to_update[0]['state'] = 'processed'

        return super(droga_stock_picking_extension, self).button_validate()

class purchase_request_extension(models.Model):
    _inherit = 'droga.purhcase.request'
    store_origin_form=fields.Many2one('stock.picking',readonly=True)

class droga_stock_product_extension(models.Model):
    _inherit = 'product.template'
    name = fields.Char('Name', index='trigram', required=True, translate=True,tracking=True)
    company_id = fields.Many2one('res.company', string='Company',index=True, default=lambda self: self.env.company, required=False)
    order_type = fields.Selection([
        ('IM', 'Import and pharmacy'),
        ('WS', 'Wholesale and pharmacy'),
        ('BT', 'Import and wholesale'),
    ('PT', 'Physiotherapy only'),('PH', 'Pharmacy only'),('ALL','ALL')], string='Product used under')
    from_pharma=fields.Boolean('Created from pharmacy menu',default=False,store=False)
    bought_locally=fields.Boolean('Bought Locally',default=False)
    pharmacy_group_id=fields.Many2one('droga.prod.categ.pharma')
    list_price = fields.Float(
        'Sales Price', default=1.0,
        digits='Product Price',tracking=True,
        help="Price at which the product is sold to customers.",
    )
    def _compute_show_qty_status_button(self):
        for template in self:
            template.show_on_hand_qty_status_button = False
            template.show_forecasted_qty_status_button = template.type == 'product'

    qty_available_import=fields.Float('Quantity On Hand', compute='_compute_quantities_import')
    def _compute_quantities_import(self):
        for rec in self:
            rec.qty_available_import=rec.qty_available*(rec.import_uom_new.factor / rec.uom_id.factor)
    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        change_default=True, default='', group_expand='_read_group_categ_id',
        help="Select category for the current product")
    detailed_type = fields.Selection(selection=[
        ('product', 'Storable Product'),
        ('consu','Consumables'),
        ('service', 'Service')], string='Product Type', default='product', required=True,store=True,
        help='A storable product is a product for which you manage stock. The Inventory app has to be installed.\n'
             'A service is a non-material product you provide.')
    old_ref=fields.Char('Old reference')
    sub_categ_id=fields.Many2one(
        'product.category', 'Product Sub-Category',
        change_default=True, default='', group_expand='_read_group_categ_id',
         help="Select sub-category for the current product")
    default_code = fields.Char('Internal Reference',compute='_compute_default_code',
        inverse='_inverse_default_code',
         store=True,required=False)
    prod_read_only=fields.Boolean(compute='is_prod_readonly')
    product_id_db=fields.Integer('Product product db id',compute='_get_prod_id')
    list_price_phar = fields.Float(
        'Sales price pharmacy', default=1.0,
        digits='Product Price',
        help="Price at which the product is sold to pharmacy customers.",tracking=True
    )
    manufacturing=fields.Char('Manufacturer')
    origin = fields.Many2one('res.country',string='Origin')
    reg_status=fields.Selection([('draft', 'draft'), ('waiting', 'waiting'),('rejected', 'rejected'),('approved', 'approved')],
                            default='draft')

    def _get_prod_id(self):
        for rec in self:
            prods=self.env['product.product'].search([('product_tmpl_id','=',rec.id)])
            if len(prods)>0:
                rec.product_id_db=self.env['product.product'].search([('product_tmpl_id','=',rec.id)])[0].id
            else:
                rec.product_id_db=0
    def _inverse_default_code(self):
        pass
    def _compute_default_code(self):
        pass

    def  is_prod_readonly(self):
        for rec in self:
            if len(self.env['product.template'].search([('default_code', '=', rec.default_code)])) > 0:
                rec.prod_read_only=True
            else:
                rec.prod_read_only = False

    def approve(self):
        self.set_activity_done()
        for res in self:
            res.reg_status = 'approved'
            prods = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', res.id),('active','=',False)])
            for pr in prods:
                pr.active = True

    def reject(self):
        self.set_activity_done()
        for res in self:
            res.reg_status = 'rejected'
            prods = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', res.id),('active','=',True)])
            for pr in prods:
                pr.active = False

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.display_name)])
        for act in activity:
            act.sudo().action_done()

    categ=fields.Many2one('uom.category',related='uom_id.category_id')
    pharma_uom = fields.Many2one('uom.uom', string='Pharma UOM',tracking=True)
    import_uom_new = fields.Many2one('uom.uom', string='Import UOM', tracking=True)
    default_warehouse=fields.Many2one('stock.warehouse','Inventory warehouse',
                                      company_dependent=True, check_company=True)
    emergency_order_point=fields.Float('Emergency order point')
    lead_time_in_days = fields.Integer('Lead time in days',default=120)
    maximum_stock_level = fields.Float('Maximum stock level')
    average_month_consumption = fields.Float('Avg. monthly cons.',store=True,help="Average monthly consumption")
    average_month_consumption_phar = fields.Float('Avg. monthly cons. pharmacy',store=True,help="Average monthly consumption")
    is_core_product = fields.Boolean('Is core product for promoters',tracking=True)
    prod_approver = fields.Many2one('res.users', store=True)


    has_access = fields.Boolean('is_wh_accessible', default=False, compute='_compute_has_access',
                                search='_search_has_access')

    def _search_has_access(self, operator, value):

        compiled_wh_domain = []
        user_groups_list = self.env.user.groups_id
        for user_group in user_groups_list:
            given_ules = user_group.rule_groups
            for rule in given_ules:
                if 'Warehouse' in rule.model_id.name:
                    compiled_wh_domain.append(
                        rule.domain_force.strip().replace("[('code', '=', ", '').replace("'", '').replace(')]', ''))

        if operator == '=':
            if len(compiled_wh_domain) == 0:
                return [('id', 'in', [])]
            else:
                has_access = self.env['stock.warehouse'].sudo().search(
                    [('code', 'in', compiled_wh_domain)])
                return [('id', 'in', [x.id for x in has_access] if has_access else False)]
        else:
            return [('id', 'in', [])]

    def _compute_has_access(self):
        compiled_wh_domain = []
        user_groups_list = self.env.user.groups_id
        for user_group in user_groups_list:
            given_ules = user_group.rule_groups
            for rule in given_ules:
                if 'Warehouse' in rule.model_id.name:
                    compiled_wh_domain.append(
                        rule.domain_force.strip().replace("[('code', '=', ", '').replace("'", '').replace(')]', ''))

        for rec in self:
            if rec.code in compiled_wh_domain:
                rec.has_access = True
            else:
                rec.has_access = False

    def write(self, vals_list):
        if not self.env.user.has_group('droga_inventory.droga_prod_app') and 'name' in vals_list:
            raise UserError("You can not update a product (only users with 'Product registration approver' role can edit. Please contact your supervisor.")

        if not self.env.user.has_group('droga_inventory.inv_prod_mi_manager') and not self.env.user.has_group('droga_inventory.inv_prod_sc_manager') and not self.env.user.has_group('droga_inventory.inv_prod_os_manager') and not self.env.user.has_group('droga_inventory.inv_prod_ex_manager') and 'seller_ids' not in vals_list and 'invoice_policy' not in vals_list and 'most_recent_trans_date' not in vals_list and 'stock_quantity_total' not in vals_list and 'crm_group' not in vals_list:
            raise UserError("You can not update a product. Please contact your supervisor.")
        for rec in self:
            if rec.reg_status=='rejected' and not self.env.user.has_group('droga_inventory.droga_prod_app'):
                raise UserError("You can not edit the product as it's rejected.")
            if 'tracking' in vals_list:
                done_moves = self.env['stock.move'].sudo().search([('product_id.product_tmpl_id', 'in', rec.ids)],limit=1)
                if done_moves:
                    raise UserError(("You cannot change the batch setup as there are already stock moves for this product. If you want to change batch setup, you should reverse transactions, archive this product and create a new one."))

            if 'default_code' in vals_list:
                if rec.default_code!=vals_list['default_code'] and vals_list['default_code'][-1]!='_' and rec.default_code and vals_list['default_code']:
                    if rec.default_code[-1]!='_':
                        raise UserError("You can not edit product code.")
                to_update=self.env['product.product'].search([('product_tmpl_id','=',rec.id)])
                for prod in to_update:
                    prod.write({'default_code':vals_list['default_code']})
            if 'active' in vals_list:
                if rec.reg_status == 'waiting' and not self.env.user.has_group('droga_inventory.droga_prod_app') and vals_list['active']:
                    raise UserError("You can not edit the product as it's awaiting approval.")

                if rec.active and not vals_list['active'] and rec.default_code[-1]!='_':
                    rec.write({'default_code':rec.default_code+'_'})
                if not rec.active and vals_list['active'] and rec.default_code[-1]=='_':
                    rec.write({'default_code':rec.default_code[:-1]})

        return super(droga_stock_product_extension, self).write(vals_list)

    @api.onchange('pharmacy_group_id')
    def _onchange_pharma_group(self):
        self.taxes_id=self.pharmacy_group_id.taxes_id.ids

    @api.onchange('uom_id')
    def _onchange_uom(self):
        for rec in self:
            rec.uom_po_id=rec.uom_id.id

    @api.onchange('default_code')
    def _onchange_default_code(self):
        if not self.default_code:
            return

        self.default_code=self.default_code.upper()
        domain = [('default_code', '=', self.default_code)]
        if self.id.origin:
            domain.append(('id', '!=', self.id.origin))

        if self.env['product.template'].search(domain, limit=1):
            dc=self.default_code
            self.default_code = self._origin.default_code
            return {'warning': {
                'title': ("Note:"),
                'message': ("The Internal Reference "+dc+" already exists."),
            }}
        # If user has access to MI, automatically reject changes saying ID assignment is automatic
        if self.env.user.has_group('droga_inventory.inv_prod_mi_manager') and self._origin.default_code:
            self.default_code = self._origin.default_code
            return {'warning': {
                'title': ("Note:"),
                'message': ("Assigned code can not be changed."),
            }}


    @api.model
    def create(self, vals_list):
        vals_list["prod_approver"] = self.env.ref("droga_inventory.droga_prod_app").users.ids[0] if len(
            self.env.ref("droga_inventory.droga_prod_app").users.ids) > 0 else None
        res=super(droga_stock_product_extension, self).create(vals_list)
        if not self.env.user.has_group('droga_inventory.inv_prod_mi_manager') and not self.env.user.has_group('droga_inventory.inv_prod_sc_manager') and not self.env.user.has_group('droga_inventory.inv_prod_os_manager') and not self.env.user.has_group('droga_inventory.inv_prod_ex_manager'):
            raise UserError("You can not create a product. Please contact your supervisor.")
        #If user has access to MI group, automatically assign ID
        if self.env.user.has_group('droga_inventory.inv_prod_mi_manager') and self.env.company.id==1:
            res.default_code=res.pharmacy_group_id.id_sequence+('0'*(3-len(str(res.pharmacy_group_id.id_counter))))+ str(res.pharmacy_group_id.id_counter)
            vals_list['default_code']=res.pharmacy_group_id.id_sequence+('0'*(3-len(str(res.pharmacy_group_id.id_counter))))+ str(res.pharmacy_group_id.id_counter)
            res.pharmacy_group_id.write({'id_counter': res.pharmacy_group_id.id_counter+1})
        if not vals_list['default_code']:
            raise UserError("Default code can not be empty.")
        if res.company_id.id==2:
            res.order_type='ALL'
        if res.reg_status=='draft' and not res.categ_id.name.startswith('Office') and not res.categ_id.name.startswith('Fixed') and res.company_id.id==1 and not res.from_pharma:
            res.reg_status='waiting'
            prods=self.env['product.product'].sudo().search(
                    [('product_tmpl_id', '=', res.id)])
            for pr in prods:
                pr.active=False
        else:
            res.reg_status='approved'

        return res

class product_categ_pharmacy(models.Model):
    _name='droga.prod.categ.pharma'
    _rec_name='categ'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    categ=fields.Char('Category',tracking=True)
    id_sequence=fields.Char('ID starts with')
    id_counter=fields.Integer('ID counter',default=1,tracking=True)
    taxes_id=fields.Many2many('account.tax',tracking=True)

class product_selection_field(models.Model):
    _inherit = 'product.category'
    avail_in_product_master=fields.Boolean('Available in product master file',default=False)
    off_supplies=fields.Boolean('Office supplies group',default=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=False)
    group_type=fields.Selection([
        ('MI','Medical items'),
        ('SC', 'Services'),
        ('EX','Export items'),
    ('OS', 'Office supplies')], string='Group type.')
    reservation_period=fields.Float('Reservation period in Hrs',default=0)
    batch_expiry_alert_date = fields.Float('Batch expiry alert in days', default=90)

class ResUsers(models.Model):
    _inherit = 'res.users'

    warehouse_ids_im_ws = fields.Many2many('stock.warehouse', 'stock_warehouse_access_is_ws', 'uid', 'warehouse_id',domain="[('wh_type', '!=', 'PH')]",
                                            string='Stock warehouse access')
    warehouse_ids_ph = fields.Many2many('stock.warehouse', 'stock_warehouse_access_ph', 'uid', 'warehouse_id',
                                           domain="[('wh_type', '=', 'PH')]",
                                           string='Stock warehouse access')
    warehouse_ids_ph_disp=fields.Many2many('stock.warehouse', 'stock_warehouse_access_ph_disp', 'uid', 'warehouse_id',
                                           domain="[('wh_type', '=', 'PH'),('has_dispensary_location','=',True)]",
                                           string='Pharmacy sales access')
    warehouse_ids_pt_disp = fields.Many2many('stock.warehouse', 'stock_warehouse_access_pt_disp', 'uid', 'warehouse_id',
                                             domain="[('wh_type', '=', 'PT')]",
                                             string='Physiotherapy sales access')


class prod(models.Model):
    _inherit = 'product.product'
    import_uom_new=fields.Many2one('uom.uom',related='product_tmpl_id.import_uom_new')
    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state')
    @api.depends_context(
        'lot_id', 'owner_id', 'package_id', 'from_date', 'to_date',
        'location', 'warehouse',
    )
    def _compute_quantities(self):
        products = self.with_context(prefetch_fields=False).filtered(lambda p: p.type != 'service').with_context(
            prefetch_fields=True)
        res = products._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'),
                                                self._context.get('package_id'), self._context.get('from_date'),
                                                self._context.get('to_date'))
        for product in products:
            if product.product_tmpl_id.import_uom_new.factor==0:
                rate=1
            else:
                rate=product.product_tmpl_id.uom_id.factor/product.product_tmpl_id.import_uom_new.factor
            product.update(res[product.id])
            product.qty_available=product.qty_available/rate
            product.incoming_qty = product.incoming_qty / rate
            product.outgoing_qty = product.outgoing_qty / rate
            product.virtual_available = product.virtual_available / rate
            product.free_qty = product.free_qty / rate
        # Services need to be set with 0.0 for all quantities
        services = self - products
        services.qty_available = 0.0
        services.incoming_qty = 0.0
        services.outgoing_qty = 0.0
        services.virtual_available = 0.0
        services.free_qty = 0.0