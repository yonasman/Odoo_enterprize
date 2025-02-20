from odoo import models, fields, api
from odoo.addons.mail.models.mail_thread import MailThread
from odoo.exceptions import UserError

class droga_tender_sale_line_extension(models.Model):
    _inherit = 'sale.order.line'
    tender_line=fields.Many2one('droga.tender.performance.evaluation')

class droga_tender_master(models.Model):
    _name = 'droga.tender.performance.evaluation'

    # Text fields
    lot_number = fields.Char("Lot #",related='parent_tender_performance_detail.lot_number')
    item_num = fields.Integer('Item #.',related='parent_tender_performance_detail.item_num')
    item_des = fields.Char("Item requested",related='parent_tender_performance_detail.item_des')
    item_des_list = fields.Many2one('droga.tender.products', string="Item requested",related='parent_tender_performance_detail.item_des_list')
    item_pro = fields.Char("Item proposed",related='parent_tender_performance_detail.item_pro',store=True)
    latest_invoice_date=fields.Date('Invoice date',store=True)

    # decimal fields
    quantity = fields.Float("Award qty",related='parent_tender_performance_detail.quantity')

    def get_award_qty(self):
        return self.parent_tender_performance_detail.quantity
    award_quantity = fields.Float("Revised qty", default=get_award_qty)

    unit_price = fields.Float("Unit price",related='parent_tender_performance_detail.unit_price')
    amount = fields.Float("Amount quoted",related='parent_tender_performance_detail.amount')

    droga_product=fields.Many2one('product.template')
    droga_old_product = fields.Many2one('product.template')

    award_cost = fields.Float("Awarded cost",readonly=1,compute="compute_award",store=True)

    def open_tender(self):
        return {
            'name': 'Tender',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.tender.master',
            'type': 'ir.actions.act_window',
            'res_id': self.parent_tender_performance.id,
        }

    @api.depends("award_quantity")
    def compute_award(self):
        for rec in self:
            if rec.award_quantity*rec.unit_price!=0:
                rec.award_cost=rec.award_quantity*rec.unit_price
            else:
                rec.award_cost=rec.amount

    perf_pct=fields.Float('% of Performance',compute="compute_performance")
    init_sales_order=fields.Boolean('Initiate S.order?',default=False)

    ordered_qty=fields.Float('Ordered qty',compute='_compute_ordered_delivered_qty')
    delivered_qty = fields.Float('Delivered qty', compute='_compute_ordered_delivered_qty')
    remaining_qty = fields.Float('Remaining qty', compute='_compute_ordered_delivered_qty')

    def _compute_ordered_delivered_qty(self):
        for rec in self:
            if len(self.env['product.product'].search([('product_tmpl_id','=',rec.droga_product.id),'|', ('active','=',True),  ('active','=',False)]))==0:
                rec.ordered_qty = 0
                rec.delivered_qty = 0
                rec.remaining_qty=rec.award_quantity
            else:
                prod_id=self.env['product.product'].search([('product_tmpl_id','=',rec.droga_product.id),'|', ('active','=',True),  ('active','=',False)]).ids
                ten_sales=self.env['sale.order'].search([('state','=','sale'),('tender_origin_form_tender','=',rec.parent_tender_performance.id)]).ids

                rec.ordered_qty=sum(self.env['sale.order.line'].search([('order_id','in',ten_sales),('product_id','in',prod_id)]).mapped('product_uom_qty'))
                rec.delivered_qty=sum(self.env['sale.order.line'].search([('order_id','in',ten_sales),('product_id','in',prod_id)]).mapped('qty_delivered'))
                rec.remaining_qty = rec.award_quantity-rec.ordered_qty
    def _get_order_status(self):
        for rec in self:
            if self.env['sale.order.line'].search([('tender_line','=',rec.id)]):
                rec.sales_order=True
            else:
                rec.sales_order = False
    @api.depends("amount", "award_cost")
    def compute_performance(self):
        for rec in self:
            try:
                rec.perf_pct = (rec.award_cost / rec.amount) * 100
            except Exception as e:
                rec.perf_pct=0.0

    @api.onchange("award_quantity")
    def _qty_change(self):
        for record in self:
            record.award_cost=record.award_quantity*record.unit_price
    # relational fields
    unit_of_measure = fields.Many2one('uom.uom', string='UOM')
    parent_tender_performance = fields.Many2one('droga.tender.master', required=True)
    customer=fields.Many2one(related='parent_tender_performance.customer')
    procurement_title=fields.Char(related='parent_tender_performance.procurement_title')
    closing_date_gre=fields.Datetime(related='parent_tender_performance.closing_date_gre')
    parent_tender_performance_detail = fields.Many2one('droga.tender.submission.detail')
    type_item = fields.Many2one('droga.tender.settings.type.item', string='Type or items',related='parent_tender_performance_detail.type_item')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 state={'done': [('readonly', True)]},related='parent_tender_performance_detail.company_id')
    performance_pct=fields.Float(compute='_compute_perf_item',string='Award %')
    total_delivered_amount=fields.Float(compute='_compute_perf_item',string='Total delivered amt')
    performance_pct_delivery=fields.Float(compute='_compute_perf_item',string='Delivery %')
    cus_type = fields.Many2one(related='parent_tender_performance.customer_type', string='Customer type', store=True)
    def _compute_perf_item(self):
        for rec in self:
            rec.performance_pct=(rec.award_cost/rec.amount)*100 if rec.amount!=0 else 0
            rec.total_delivered_amount=rec.unit_price*rec.quantity
            rec.performance_pct_delivery=((rec.unit_price*rec.delivered_qty)/rec.award_cost)*100 if rec.award_cost!=0 else 0
    def reg_products(self):
        if not self.item_pro:
            return
        channels = self.env['mail.channel'].search([('name', '=', 'Tender buisness development')])

        message = "Please develop and import product titled '" + self.item_pro + "' as our customers require it."
        message = message + '\n Product group is - ' + self.type_item.type_or_item_name if self.type_item.type_or_item_name else message
        for c in channels:
            c.message_post(
                subject="Product registration. ",
                body=message,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                author_id=self.env.user.id,
            )

        #Search this model using namea and send message
        #chat = self.env['mail.channel'].with_user(self.env.user).browse(8)

        #chat.message_post(body="Another one", message_type='comment', subtype_xmlid='mail.mt_comment')




        chat = self.env['mail.channel'].search(['&',('channel_type','=','chat'),'|',('name','=','CRMSALES_REP, Administrator'),
                                                ('name','=','Administrator, CRMSALES_REP')])
        for rec in chat:
            rec.message_post(body="Another oneeee", message_type='comment', subtype_xmlid='mail.mt_comment')

    @api.model
    def create(self, vals_list):
        if vals_list["award_cost"]==0:
            raise UserError("Awarded cost can not be zero.")
        return super().create(vals_list)

    def write(self, vals):
        if 'award_cost' in vals:
            if vals["award_cost"]==0:
                raise UserError("Awarded cost can not be zero.")
        return super().write(vals)