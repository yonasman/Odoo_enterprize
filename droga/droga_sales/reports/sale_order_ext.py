from odoo import models, fields, api
from odoo.http import request
from odoo.tools import drop_view_if_exists


class sales_report_fields(models.Model):
    _inherit = 'sale.order'
    cust_location = fields.Many2one('droga.crm.settings.city', related='partner_id.city_name', store=True)
    fs_number=fields.Char('FS Number')
    cust_area = fields.Many2one('droga.crm.settings.area',related='partner_id.area',store=True)
    print(cust_area)

class sales_report_det_fields(models.Model):
    _inherit = 'sale.order.line'
    cust_location = fields.Many2one('droga.crm.settings.city', related='order_id.cust_location', store=True)
    cust_type_ext_det = fields.Many2one('droga.cust.type', string='Customer type', related='order_id.cust_type_ext',
                                        store=True)

    fs_number=fields.Char(compute='_get_fs_no',store=True)

    print(cust_location)

    @api.depends('order_id.fs_number')
    def _get_fs_no(self):
        for rec in self:
            rec.fs_number=rec.order_id.fs_number

    date_order_det = fields.Datetime('Date', related='order_id.date_order', store=True)
    order_type_det = fields.Selection([
        ('IM', 'Import'),
        ('WS', 'Wholesale'), ('PT', 'Physiotherapy')], string='Order from (IMP/WHS)', related='order_id.order_type', store=True)
    order_from_det = fields.Char('Order from', compute='_get_order_from', store=True)
    payment_term_det = fields.Many2one('account.payment.term',
                                       string="Payment Terms", related='order_id.payment_term_id', store=True)
    cash_or_credit = fields.Char(compute='_cash_or_credit')

    invoice_ids = fields.Many2many(related="order_id.invoice_ids")
    invoice_no = fields.Char(compute="_get_invoice_no")

    def _get_invoice_no(self):
        for record in self:
            if len(record.invoice_ids)>0:
                for invoice in record.invoice_ids:
                    record.invoice_no = invoice.name
            else:
                record.invoice_no='0'

    @api.depends('order_id.order_from')
    def _get_order_from(self):
        for rec in self:
            rec.order_from_det = rec.order_id.order_from

    def _cash_or_credit(self):
        for rec in self:
            if rec.payment_term_det.apply_credit_limit:
                rec.cash_or_credit = 'Credit'
            else:
                rec.cash_or_credit = 'Cash'

    crm_group1 = fields.Many2one('droga.crm.settings.prod_group', related='product_id.crm_group', store=True)
    has_group_access=fields.Boolean('Has CRM product group access',related='product_id.product_tmpl_id.crm_group.has_group_access')

    is_core = fields.Boolean(related='product_id.is_core_product', store=True)

    itemcode = fields.Char(related='product_id.default_code',store=True)
    itemdesc = fields.Char(related='product_id.name',store=True)
    manufacturing=fields.Char(related='product_id.manufacturing',store=True)
    itemcateg = fields.Many2one('product.category', related='product_id.categ_id')

    invoiced_amt = fields.Float('Invoiced Amount', compute='_get_invoiced_amount', store=True)
    #unit_cost = fields.Float('Unit Cost', compute='_get_cost')
    #total_cost = fields.Float('Total Cost', compute='_get_cost')
    #margin = fields.Float('Profit Margin', compute='_get_cost')
    #margin_pct = fields.Float('Profit Margin %', compute='_get_cost')
    fs_num = fields.Char(compute='_get_fs_num')

    def _get_cost(self):
        for rec in self:
            uc = self.env['droga.sales.cost.of.sales'].search(
                [('sale_line_id', '=', rec.id)])
            if not uc:
                rec.unit_cost = 0
                rec.total_cost = 0
                rec.margin = 0
                rec.margin_pct = 0
            else:
                rec.unit_cost = sum(uc.mapped('unit_cost'))/len(uc)
                rec.total_cost = rec.qty_invoiced * rec.unit_cost
                rec.margin = rec.invoiced_amt - rec.total_cost
                rec.margin_pct = (rec.margin / rec.invoiced_amt) * 100 if rec.invoiced_amt != 0 else 0

    @api.depends('qty_invoiced', 'price_unit')
    def _get_invoiced_amount(self):
        for rec in self:
            rec.invoiced_amt = rec.qty_invoiced * rec.price_unit

    sales_initiator_det = fields.Char(related='order_id.sales_initiator')
    sales_dept = fields.Char(compute='_get_sales_dep')

    def _get_sales_dep(self):
        for rec in self:
            if not rec.sales_initiator_det:
                rec.sales_dept = ' '
            elif rec.sales_initiator_det.startswith('SR'):
                rec.sales_dept = 'Marketing'
            elif rec.sales_initiator_det.startswith('Ten') or rec.sales_initiator_det.startswith('TEN'):
                rec.sales_dept = 'Tender'
            else:
                rec.sales_dept = 'Employee'

    invoice_date = fields.Date('Invoice date',store=True)
class droga_sales_cost_of_sales_view(models.Model):
    _name = 'droga.sales.cost.of.sales'

    _auto = False
    product_id=fields.Integer('product_id')
    product_code = fields.Char('Product Code')
    product_descr = fields.Char('Product Description')
    product_categ = fields.Char('Product Category')
    sales_ref = fields.Char('Sales Ref')
    order_from = fields.Char('Profit / Cost Center')
    sales_date=fields.Date('Sales Date')
    sale_line_id = fields.Integer('sale_order_line')
    invoiced_amt=fields.Float('Invoiced amount')
    qty_invoiced=fields.Float('Quantity Invoiced')
    price_unit = fields.Float('Unit Price')
    profit = fields.Float('Profit')
    company_id = fields.Integer('Company ID')
    profit_margin = fields.Float('Profit Margin')
    profit_margin_progress_bar = fields.Float('Profit Margin')
    amount = fields.Float("Total cost")
    quantity = fields.Float("Quantity")
    unit_cost = fields.Float("Unit Cost")

    def init(self):
        drop_view_if_exists(self.env.cr, 'droga_sales_cost_of_sales')
        self.env.cr.execute("""
                   create or replace view droga_sales_cost_of_sales as (
                        select row_number() over () as id,g.* from (
select m.company_id,m.product_id,m.product_descr,m.product_code,m.sales_ref,m.order_from,m.product_categ,m.sales_date,m.sale_line_id,avg(m.invoiced_amt) as invoiced_amt,avg(m.qty_invoiced) as qty_invoiced,avg(m.price_unit) as price_unit,round((avg(m.invoiced_amt)-sum(m.amount))::decimal,2) as profit,
case when sum(m.invoiced_amt)!=0 then round((((avg(m.invoiced_amt)-sum(m.amount))/avg(m.invoiced_amt))*100)::decimal,2) else 0 end as profit_margin_progress_bar,case when sum(m.invoiced_amt)!=0 then round((((avg(m.invoiced_amt)-sum(m.amount))/avg(m.invoiced_amt))*100)::decimal,2) else 0 end as profit_margin,sum(m.quantity) as quantity,avg(m.unit_cost) as unit_cost,sum(m.amount) as amount from (											
select c.id as product_id,(select y.name->>'en_US' from product_template y where y.id=(select m.product_tmpl_id from product_product m where m.id=a.product_id)) as product_descr,b.value,
(select m.default_code from product_product m where m.id=a.product_id) as product_code,(select m.name from sale_order m where m.id=c.order_id) as sales_ref,(select m.order_from from sale_order m where m.id=c.order_id) as order_from,c.company_id,
(select i.name from product_category i where i.id=(select y.categ_id from product_template y where y.id=(select m.product_tmpl_id from product_product m where m.id=a.product_id))) as product_categ,
(c.date_order_det) as sales_date,invoiced_amt,qty_invoiced,c.price_unit,round((invoiced_amt+b.value)::decimal,2) as profit,case when invoiced_amt!=0 then round((((invoiced_amt+b.value)/invoiced_amt)*100)::decimal,2) else 0 end as profit_margin,
a.sale_line_id,b.quantity*-1 as quantity,round(b.unit_cost::decimal,2) as unit_cost,round(b.value*-1::decimal,2) as amount from stock_move a,stock_valuation_layer b,sale_order_line c where a.id=b.stock_move_id 
                        and a.sale_line_id is not null and c.id=a.sale_line_id) m where m.company_id=1 group by m.company_id,m.product_id,m.product_descr,m.product_code,m.sales_ref,m.order_from,m.product_categ,m.sales_date,m.sale_line_id) g 
                   )""")



                        #update account_move_line set product_id=4823 where product_id=2222
						#update sale_order_line set product_id=4823 where product_id=2222
						#delete from product_product where id=2222