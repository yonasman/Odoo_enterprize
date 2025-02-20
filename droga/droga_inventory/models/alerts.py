from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api

class prod_availability(models.Model):
    _name='product.availability.pharmacy'
    prod=fields.Many2one('product.product',readonly=True)
    warehouse=fields.Many2one('stock.warehouse',readonly=True)
    stock_quantity_total = fields.Float('Stock quantity',readonly=True)
    availability = fields.Char('Availability', compute='_compute_availability', store=True)
    categ_id=fields.Many2one('product.category',string='Product category',related='prod.product_tmpl_id.categ_id',store=True)
    wh_type = fields.Selection([
        ('IM','Import'),('EX','Export'),
        ('WS', 'Wholesale'), ('PT', 'Physiotherapy'),
        ('PH', 'Pharmacy'), ('PR', 'Project')], related='warehouse.wh_type', store=True)
    batch_id=fields.Many2one('stock.lot',string='Batch ID',readonly=True)
    expiry_date=fields.Datetime('Expiry date',compute='_expiry_status',store=True)
    expiry_status=fields.Char('Expiry status',compute='_expiry_status',store=True)
    company_id = fields.Many2one('res.company', string='Company',readonly=True,
                                 default=lambda self: self.env.company.id)

    availability_import = fields.Char('Availability', compute='_compute_availability_import', store=True)
    stock_quantity_total_import = fields.Float('Stock quantity', compute='_compute_availability_import', store=True)
    @api.depends('expiry_date','batch_id.expiration_date','prod')
    def _expiry_status(self):
        for rec in self:
            rec.expiry_date=rec.batch_id.expiration_date

            if not rec.expiry_date:
                rec.expiry_status = 'No expiry'
            elif datetime.today()>rec.expiry_date:
                rec.expiry_status = 'Expired'
            elif datetime.today()+ relativedelta(days=rec.prod.product_tmpl_id.categ_id.batch_expiry_alert_date)>rec.expiry_date:
                rec.expiry_status='Near Expiry'
            else:
                rec.expiry_status = 'Up-to-Date'
    @api.depends('stock_quantity_total','prod.product_tmpl_id.import_uom_new')
    def _compute_availability_import(self):
        for rec in self:
            if rec.company_id.id == 1 and rec.prod.product_tmpl_id.import_uom_new.factor != 0:
                rec.stock_quantity_total_import = rec.stock_quantity_total / (
                            rec.prod.product_tmpl_id.uom_id.factor / rec.prod.product_tmpl_id.import_uom_new.factor)
            else:
                rec.stock_quantity_total_import = rec.stock_quantity_total

            if rec.stock_quantity_total_import == 0:
                rec.availability_import = 'Stock out'
            elif rec.stock_quantity_total_import > 0 and rec.stock_quantity_total <= rec.prod.product_tmpl_id.pharmacy_order_point:
                rec.availability_import = 'Needs reordering'
            else:
                rec.availability_import = 'Available'

    @api.depends('stock_quantity_total', 'prod.product_tmpl_id.pharmacy_order_point')
    def _compute_availability(self):
        for rec in self:
            if rec.stock_quantity_total == 0:
                rec.availability = 'Stock out'
            elif rec.stock_quantity_total > 0 and rec.stock_quantity_total <= rec.prod.product_tmpl_id.pharmacy_order_point:
                rec.availability = 'Needs reordering'
            else:
                rec.availability = 'Available'

    has_access = fields.Boolean('is_move_line_accessible', default=False, compute='_compute_has_access',
                                search='_search_has_access')
    def _search_has_access(self, operator, value):
        if operator == '=':
            has_access = self.env['product.availability.pharmacy'].sudo().search(
                ['|',('warehouse.has_access', '=', True),('warehouse.has_access', '=', True)])
            return [('id', 'in', [x.id for x in has_access] if has_access else False)]
        else:
            return [('id', 'in', [])]

    def _compute_has_access(self):
        for rec in self:
            if rec.warehouse.has_access or rec.warehouse.has_access:
                rec.has_access = True
            else:
                rec.has_access = False
class product_alerts(models.Model):
    _inherit = 'product.template'
    most_recent_so_alert_date=fields.Date('Most recent alert time',default=datetime.now().date(),store=True)
    pharmacy_order_point=fields.Float('Pharmacy emergency order point per branch')
    most_recent_order_alert_date = fields.Date('Most recent minimum level order alert time', default=datetime.now().date(), store=True)
    most_recent_trans_date=fields.Date('Most recent trans date',default=datetime.now().date(),store=True)
    stock_quantity_total=fields.Float('Stock quantity in droga')
    stock_out_detail=fields.One2many('stock.out.history','product')
    availability=fields.Char('Availability',compute='_compute_availability',store=True)
    notification_for=fields.Selection([('All', 'All'), ('Pharma', 'Pharma'),('Import','Import')],
                              tracking=True)
    adj_date=fields.Date('Adjustment date')
    tracking = fields.Selection([
        ('serial', 'By Unique Serial Number'),
        ('lot', 'By Lots'),
        ('none', 'No Tracking')],
        string="Tracking", required=True, default='none',
        # Not having a default value here causes issues when migrating.
        compute='_compute_tracking', store=True, readonly=False, precompute=True,tracking=True,
        help="Ensure the traceability of a storable product in your warehouse.")
    @api.depends('stock_quantity_total','emergency_order_point')
    def _compute_availability(self):
        for rec in self:
            if rec.stock_quantity_total==0:
                rec.availability='Stock out'
            elif rec.stock_quantity_total>0 and rec.stock_quantity_total<=rec.emergency_order_point:
                rec.availability = 'Needs reordering'
            else:
                rec.availability = 'Available'
    def open_stock_out_hist(self):
        return {
            'name': 'Stock out history',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.template',
            'view_id': self.env.ref('droga_inventory.droga_inventory_stock_out_history').id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
        }

    def open_stock_on_hand(self):
        return {
            'name': 'Stock on hand',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.quant',
            'view_id': self.env.ref('stock.view_stock_quant_tree_editable').id,
            'type': 'ir.actions.act_window',
            'domain':
                ([('product_id.product_tmpl_id', '=', self.id),('location_id.usage','=','internal')]),
            'target': 'new',
        }

    def update_qty(self):
        pros=self.env['product.template'].search([])
        for rec in pros:
            quants=self.env['stock.quant'].search([('product_id.product_tmpl_id.id','=',rec.id),('location_id.usage','=','internal')])
            rec.stock_quantity_total=sum(quants.mapped('quantity'))
            rec._compute_availability()
class stock_out_history(models.Model):
    _name='stock.out.history'
    product=fields.Many2one('product.template')
    date_from=fields.Date('Stock out date from')
    date_to = fields.Date('Stock out date to')
    duration=fields.Integer('Stock out duration',compute='_get_stock_out_duration')
    def _get_stock_out_duration(self):
        for rec in self:
            if rec.date_to:
                rec.duration=(rec.date_to-rec.date_from).days
            else:
                rec.duration = (datetime.now().date() - rec.date_from).days
class stock_out_notification(models.Model):
    _name='stock.out.notification'
    _description = 'Stock out notification'
    def generate_stock_out_alert(self):
        query = """select id from product_template where most_recent_so_alert_date<most_recent_trans_date and stock_quantity_total=0 and notification_for in ('Import','All') and company_id=1"""
        self._cr.execute(query)
        qry_res = self._cr.dictfetchall()
        stock_out_items = self.env['product.template'].browse(set(rec['id'] for rec in qry_res))

        #query_pharma = """select id from product_template where most_recent_so_alert_date<most_recent_trans_date and stock_quantity_total=0 and notification_for in ('Pharma','All') and company_id=1"""
        #self._cr.execute(query_pharma)
        #qry_res_pharma = self._cr.dictfetchall()
        #stock_out_items_pharma = self.env['product.template'].browse(set(rec['id'] for rec in qry_res_pharma))

        for rec in stock_out_items:
            rec.write({'most_recent_so_alert_date': datetime.now().date()})

            channels = self.env['mail.channel'].search([('name', '=', 'Stock out notification')])
            message = "Product '" + rec.name + "("+rec.default_code+")' is out of stock."

            for c in channels:
                c.message_post(
                    subject="Stock out notification. ",
                    body=message,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                    author_id=self.env.user.id,
                )
        """
        for rec in stock_out_items_pharma:
            rec.write({'most_recent_so_alert_date': datetime.now().date()})

            channels = self.env['mail.channel'].search([('name', '=', 'Stock out notification - Pharmacy')])
            message = "Product '" + rec.name + "(" + rec.default_code + ")' is out of stock."

            for c in channels:
                c.message_post(
                    subject="Stock out notification. ",
                    body=message,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                    author_id=self.env.user.id,
                )
        """

    def generate_min_order_alert(self):
        query = """select id from product_template where most_recent_order_alert_date<most_recent_trans_date and emergency_order_point<=stock_quantity_total and company_id=1"""
        self._cr.execute(query)
        qry_res = self._cr.dictfetchall()
        stock_out_items = self.env['product.template'].browse(set(rec['id'] for rec in qry_res))

        query_pharma = """select id from product_template where most_recent_order_alert_date<most_recent_trans_date and emergency_order_point<=stock_quantity_total and company_id=1"""
        self._cr.execute(query_pharma)
        qry_res_pharma = self._cr.dictfetchall()
        stock_out_items_pharma = self.env['product.template'].browse(set(rec['id'] for rec in qry_res_pharma))

        for rec in stock_out_items:
            rec.write({'most_recent_order_alert_date': datetime.now().date()})

            channels = self.env['mail.channel'].search([('name', '=', 'Minimum stock order level')])
            message = "Product '" + rec.name + "("+rec.default_code+")' has reached it's minimum stock order level."

            for c in channels:
                c.message_post(
                    subject="Minimum order level notification. ",
                    body=message,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                    author_id=self.env.user.id,
                )

        for rec in stock_out_items_pharma:
            rec.write({'most_recent_order_alert_date': datetime.now().date()})

            channels = self.env['mail.channel'].search([('name', '=', 'Minimum stock order level - Pharmacy')])
            message = "Product '" + rec.name + "(" + rec.default_code + ")' has reached it's minimum stock order level."

            for c in channels:
                c.message_post(
                    subject="Minimum order level notification. ",
                    body=message,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                    author_id=self.env.user.id,
                )
