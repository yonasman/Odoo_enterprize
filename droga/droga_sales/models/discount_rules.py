from datetime import datetime
from datetime import timedelta, date
import simplejson
from lxml import etree
import math

import json

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.http import request

class droga_price_discount_per_type(models.Model):
    _name = 'droga.price.discount.per.type'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    cust_type = fields.Many2one('droga.cust.type', string='Customer type', tracking=True)
    product_group = fields.Many2one('product.category', string='Product category', tracking=True)
    percent = fields.Float(string='Percentage (+ve or -ve)', tracking=True, digits=(12, 9))
    core_products_or_all = fields.Selection(
        [('Core', 'Core products'), ('Noncore', 'Non-core products'), ('All', 'All')], string='Core?', required=True,
        default='Core', tracking=True)
    used_under = fields.Selection([('IM', 'Import'), ('PT', 'Physiotherapy'), ('PH', 'Pharmacy'), ('All', 'All')],
                                  string='Used under', required=True, tracking=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], required=True, default='Active',
                              tracking=True)


class droga_price_discount_per_amount(models.Model):
    _name = 'droga.price.discount.per.amount'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    payment_term = fields.Many2one('account.payment.term', string='Payment term', tracking=True)
    from_amt = fields.Float(string='From amount', tracking=True)
    to_amt = fields.Float(string='To amount', tracking=True)
    percent = fields.Float(string='Percentage (+ve or -ve)', tracking=True)
    core_products_or_all = fields.Selection(
        [('Core', 'Core products'), ('Noncore', 'Non-core products'), ('All', 'All')], string='Core?', required=True,
        default='Core', tracking=True)
    used_under = fields.Selection([('IM', 'Import'), ('PT', 'Physiotherapy'), ('PH', 'Pharmacy'), ('All', 'All')],
                                  string='Used under', required=True, tracking=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], required=True, default='Active',
                              tracking=True)


class droga_price_discount_per_product_qty(models.Model):
    _name = 'droga.price.discount.per.product.qty'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    payment_term = fields.Many2one('account.payment.term', string='Payment term', tracking=True)
    product = fields.Many2one('product.product', string='Product', tracking=True)
    from_qty = fields.Float(string='From quantity', tracking=True)
    to_qty = fields.Float(string='To quantity', tracking=True)
    percent = fields.Float(string='Percentage (+ve or -ve)', tracking=True)
    used_under = fields.Selection([('IM', 'Import'), ('PT', 'Physiotherapy'), ('PH', 'Pharmacy'), ('All', 'All')],
                                  string='Used under', required=True, tracking=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], required=True, default='Active',
                              tracking=True)


class droga_price_discount_per_product_customer(models.Model):
    _name = 'droga.price.discount.per.product.customer'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    payment_term = fields.Many2one('account.payment.term', string='Payment term', tracking=True)
    product = fields.Many2one('product.product', string='Product', tracking=True)
    cust = fields.Many2one('res.partner', string='Customer', tracking=True)
    percent = fields.Float(string='Percentage (+ve or -ve)', tracking=True)
    used_under = fields.Selection([('IM', 'Import'), ('PT', 'Physiotherapy'), ('PH', 'Pharmacy'), ('All', 'All')],
                                  string='Used under', required=True, tracking=True)
    status = fields.Selection([('Active', 'Active'), ('Closed', 'Closed')], required=True, default='Active',
                              tracking=True)

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    price_unit = fields.Float(
        string="Unit Price",
        compute='_compute_price_unit',
        inverse='_inverse_price',
        digits='Product Price',
        store=True, required=True, tracking=True,precompute=True)
    is_prod_available = fields.Char(compute='is_prod_available_method')
    selling_price=fields.Float(related='product_id.list_price_phar')
    phar_cont_price = fields.Float('Pharmacy contract price',compute='_compute_price_unit',store=True)
    phar_cont_price_marginc=fields.Char('Discount rate',compute='_get_discount')
    def _get_discount(self):
        for rec in self:
            if rec.phar_cont_price!=0:
                margin=round((rec.price_unit-rec.phar_cont_price)/rec.phar_cont_price*-100,2)
                rec.phar_cont_price_marginc=str((margin))+' %'
            else:
                rec.phar_cont_price_marginc='0 %';
    available_qty = fields.Float('Available', default=0, compute='is_prod_available_method',store=True)
    avail_char = fields.Char('Available', readonly=True, compute="is_prod_available_method")
    price_unit_before_discount = fields.Float('')
    wareh = fields.Many2one('stock.warehouse')
    store_placement = fields.Boolean('Placement', default=False)
    std_unit_price = fields.Float(readonly=True, string='UP Default')
    has_access = fields.Boolean(related='order_id.has_access')
    order_from = fields.Char(related='order_id.order_from')
    has_cust_access = fields.Boolean(related='order_id.partner_id.is_cust_available')
    product_uom_pharma_qty=fields.Float('Quantity',default=1)
    product_uom_pharma_measure=fields.Many2one('uom.uom',store=True)
    product_uom_pharma_measure_descr=fields.Char(related='product_uom.name',string='Unit')
    has_pharma_access = fields.Boolean(default=False, related='order_id.has_pharma_access')
    disc_applied=fields.Float('Discount applied',default=0)

    def write(self, vals):
        res = super(sale_order_line, self).write(vals)
        if self.order_id.state in ('sale', 'done','dispense') and ('product_uom_pharma_qty' in vals or 'price_unit' in vals):
            raise UserError("Sales order can not be updated once confirmed.")
        return res

    def _check_line_unlink(self):
        return self.filtered(
            lambda line:
                line.state in ('sale', 'done','dispense')
                and (line.invoice_lines or not line.is_downpayment)
                and not line.display_type
        )

    @api.depends('product_id', 'order_id.order_type', 'product_uom','product_uom_qty')
    def is_prod_available_method(self):
        selfsud = self.sudo()
        for rec in selfsud:
            rec.available_qty = 0

            if type(rec.order_id.order_from) is str:
                if rec.order_id.order_from == 'PH' or rec.order_id.order_from.startswith('PT'):
                    wh_list = rec.order_id.wareh
                else:
                    wh_list = selfsud.env['stock.warehouse'].search([('wh_type', '=', rec.order_id.order_type)])
            else:
                wh_list = selfsud.env['stock.warehouse'].search([('wh_type', '=', rec.order_id.order_type)])

            for wh in wh_list:
                rate = round(rec.product_uom.factor / (
                    rec.product_id.uom_id.factor if rec.product_id.uom_id.factor != 0 else (
                        rec.product_uom.factor if rec.product_uom.factor != 0 else 1)),9)
                rec.available_qty = rec.available_qty + round(((selfsud._get_avail_qty_per_warehouse(rec.product_id,
                                                                                               wh) - selfsud._get_outgoing_qty_per_warehouse(
                    rec.product_id, wh)) * (rate)),4)
                # rec.available_qty=rec.available_qty*(rec.product_uom.factor/rec.product_id.uom_id.factor)
                rec.avail_char = str(rec.available_qty)
            # rec.available_qty=rec.product_id.qty_available-rec.product_id.outgoing_qty

            if rec.product_id.detailed_type == 'service':
                rec.is_prod_available = 'True'
                return
            prodqty = sum(self.order_id.order_line.filtered(lambda x: x.product_id.id == rec.product_id.id).mapped(
                'product_uom_qty'))
            if rec.order_id.order_from=='PH' and rec.company_id.id==1:
                if rec.available_qty < prodqty:
                    rec.is_prod_available = 'False'
                elif rec.available_qty >= prodqty:
                    rec.is_prod_available = 'True'
            else:
                if (not rec.product_id.bought_locally) and rec.available_qty < prodqty:
                    rec.is_prod_available = 'False'
                # This is for out of stock products that are bought locally, they'll show up with orange color
                elif rec.product_id.bought_locally and rec.available_qty < prodqty:
                    rec.is_prod_available = 'Kinda'
                else:
                    rec.is_prod_available = 'True'

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

    def _inverse_price(self):
        pass

    def calc_sales_totals(self):
        core_sum = 0
        non_core_sum = 0
        total_before_discount = 0
        try:
            order_lines_core = self.order_id.order_line.filtered(
                lambda x: not x.display_type and x.product_id.is_core_product and x.id.ref != None)
            order_lines_non_core = self.order_id.order_line.filtered(
                lambda x: not x.display_type and not x.product_id.is_core_product and x.id.ref != None)
        except:
            order_lines_core = self.order_id.order_line.filtered(
                lambda x: not x.display_type and x.product_id.is_core_product and x.id != None)
            order_lines_non_core = self.order_id.order_line.filtered(
                lambda x: not x.display_type and not x.product_id.is_core_product and x.id != None)

        for cs in order_lines_core:
            core_sum = core_sum + (cs.product_uom_qty * cs.price_unit)
            total_before_discount = total_before_discount + (cs.product_uom_qty * cs.price_unit_before_discount)

        for ncs in order_lines_non_core:
            non_core_sum = non_core_sum + (ncs.product_uom_qty * ncs.price_unit)
            total_before_discount = total_before_discount + (ncs.product_uom_qty * ncs.price_unit_before_discount)

        self.order_id.core_sum = core_sum
        self.order_id.non_core_sum = non_core_sum
        self.order_id.total_discount = total_before_discount - (core_sum + non_core_sum)
        self.order_id.total_added = (core_sum + non_core_sum) - total_before_discount

    def _get_pharma_price_with_discount(self,line):
        line.disc_applied = 0
        rate=1
        cont_prices = self.env["droga.pharma.price.list"].search([('product', '=', line.product_id.product_tmpl_id.id),
                                                                  ('header.customer', '=', line.order_id.partner_id.id),
                                                                  ('header.date_from', '<', datetime.today()),
                                                                  ('header.date_to', '>', datetime.today()),
                                                                  ('header.status', '=', 'Active')])
        discount_per_branch_group = self.env['droga.price.discount.per.branch.group'].search(
            [('status', '=', 'Active'), ('prod_grp', '=', line.product_id.product_tmpl_id.pharmacy_group_id.id),
             ('branch', '=', line.order_id.wareh.id)])
        for disc in discount_per_branch_group:
            rate = 1 + (disc.percent / 100)

        if len(cont_prices) > 0:
            line.order_id.points_to_deduct=0
            return cont_prices[0]["selling_price"]
        elif line.order_id.partner_id.is_company:
            line.order_id.points_to_deduct = 0
            return line.product_id.list_price_phar*rate
        else:
            #Accumulated points discount
            discount_per_acc = self.env['droga.pharma.reward.issue'].search([('type','in',('Purchase reward','Discount for loyal customer')),('status','=','Active')])
            for disc in discount_per_acc:
                if len(line.order_id.ids)>0:
                    points=sum(
                        self.env['droga.pharma.points.earned'].search([('sales_ref','!=',line.order_id.ids[0]),('customer', '=', line.order_id.partner_id.id),('type','in',('Purchase reward','Discount for loyal customer')), (
                        'earned_date', '>=', date.today() + timedelta(days=-disc.reward_req_frequ))]).mapped(
                                'points_earned'))
                else:
                    points=sum(self.env['droga.pharma.points.earned'].search(
                            [('customer', '=', line.order_id.partner_id.id),
                             ('type', 'in', ('Purchase reward', 'Discount for loyal customer')), (
                                 'earned_date', '>=', date.today() + timedelta(days=-disc.reward_req_frequ))]).mapped(
                            'points_earned'))

                if line.product_id.product_tmpl_id.categ_id in disc.prod_group and disc.reward_req_points <= points:
                    rate = 1 + (disc.reward_pct / 100)
                    line.disc_applied = disc.reward_pct
                    line.order_id.points_to_deduct = disc.reward_req_points
                    line.order_id.deduct_type='Discount for loyal customer'
                    return line.product_id.list_price_phar * rate

            line.order_id.calc_sales_totals_pharma(line)

            #Breast feeders and health professionals discount
            breat_feed_children=len(self.env['droga.pharma.child'].search([('parent_cust','=',self.order_id.partner_id.id),('breat_feed_end_date','>=',datetime.today())]))
            discount_per_person=self.env['droga.breast.feed.reward.contact.type'].search([('status','=','Active')])
            partner_state='draft'
            if self.order_id.partner_id.state:
                partner_state=self.order_id.partner_id.state

            for disc in discount_per_person:
                if disc.cont_type=="hp" and self.order_id.partner_id.profession=="hp" and partner_state=='active' and line.product_id.product_tmpl_id.pharmacy_group_id.id in disc.pharmacy_group_id.ids:
                    rate=1 + (disc.discount / 100)
                    line.disc_applied=disc.discount
                    line.order_id.points_to_deduct = 1
                    line.order_id.deduct_type = 'Discount for health professional'
                elif disc.cont_type=='bp' and breat_feed_children>0 and self.order_id.partner_id.gender=='Female' and line.product_id.product_tmpl_id.pharmacy_group_id.id in disc.pharmacy_group_id.ids:
                    rate = 1 + (disc.discount / 100)
                    line.disc_applied = disc.discount
                    line.order_id.points_to_deduct = 1
                    line.order_id.deduct_type = 'Discount for breast feed'


            if rate!=1:
                return line.product_id.list_price_phar * rate

            # High value purchase discounts
            discount_per_amount = self.env['droga.pharma.high.value.pruchase'].search([('status', '=', 'Active')])
            for disc in discount_per_amount:
                if line.order_id.total_pharma_discount_groups > disc.from_amt and line.order_id.total_pharma_discount_groups < disc.to_amt and line.product_id.product_tmpl_id.categ_id in disc.prod_group:
                    rate = 1 + (disc.discount / 100)
                    line.disc_applied = disc.discount
                    line.order_id.deduct_type = 'Discount for high value purchase'
                    return line.product_id.list_price_phar * rate
            return line.product_id.list_price_phar * rate
    def _get_pharma_price(self,line):
        #Contract price
        cont_prices = self.env["droga.pharma.price.list"].search([('product', '=', line.product_id.product_tmpl_id.id),('header.customer','=',line.order_id.partner_id.id),('header.date_from','<',datetime.today()),('header.date_to','>',datetime.today()),('header.status','=','Active')])
        if len(cont_prices)>0:
            return cont_prices[0]["selling_price"]
        else:
            return line.product_id.list_price_phar

    @api.onchange('product_id')
    def _prod_changed(self):
        for rec in self:
            if rec.order_from:
                if rec.order_from.startswith('PH'):
                    rec.price_unit=self._get_pharma_price(rec)

    @api.depends('product_id', 'product_uom', 'product_uom_qty', 'tax_id', 'order_id.partner_id',
                 'order_id.payment_term_id', 'manual_price','product_uom_pharma_qty','order_id.order_line.product_uom_pharma_qty','order_id.total_disc_pharma')
    def _compute_price_unit(self):
        for line in self:
            if line.order_id.state in ('sale', 'cancel', 'done', 'fia','dispense','done'):
                return
            if line.order_from:
                if line.order_from.startswith('PH'):
                    #line.price_unit = line.product_id.list_price_phar/((line.product_uom_pharma_measure.factor if line.product_uom_pharma_measure.factor!=0 else 1)/(line.product_id.uom_id.factor if line.product_id.uom_id.factor != 0 else 1))
                    line.std_unit_price = line.product_id.list_price_phar
                    line.product_uom_qty = line.product_uom_pharma_qty
                    #line.price_unit = line.product_id.list_price_phar
                    line.phar_cont_price = self._get_pharma_price(line)
                    selling_price= self._get_pharma_price_with_discount(line)
                    if not line.order_id.manual_price_pharma:
                        line.price_unit = selling_price
                    else:
                        line.order_id.deduct_type='Manual discount'
                    if line.phar_cont_price!=0:
                        line.disc_applied=math.ceil(round(((line.phar_cont_price-line.price_unit)/line.phar_cont_price)*100,2))*-1
                    line.product_uom_pharma_measure = line.product_id.uom_id
                    line.product_uom = line.product_id.uom_id
                    line.order_id.calc_sales_totals_pharma(line)
                    return
            else:
                line.phar_cont_price = 0
        if self.order_id.company_id.id == 2:
            for line in self:
                if line.store_placement:
                    line.price_unit = 0.0
                    continue
                if not line.product_uom or not line.product_id or not line.order_id.pricelist_id:
                    line.price_unit = 0.0
                else:
                    if not line.tender_origin_form_tender and not line.manual_price:
                        price = line.with_company(line.company_id)._get_display_price()
                        line.price_unit = line.product_id._get_tax_included_unit_price(
                            line.company_id,
                            line.order_id.currency_id,
                            line.order_id.date_order,
                            'sale',
                            fiscal_position=line.order_id.fiscal_position_id,
                            product_price_unit=price,
                            product_currency=line.currency_id
                        )
                    price = line.with_company(line.company_id)._get_display_price()
                    line.std_unit_price = line.product_id._get_tax_included_unit_price(
                        line.company_id,
                        line.order_id.currency_id,
                        line.order_id.date_order,
                        'sale',
                        fiscal_position=line.order_id.fiscal_position_id,
                        product_price_unit=price,
                        product_currency=line.currency_id
                    )
        else:

            used_under = []

            if self.order_id.order_line:
                # Order_type is used for import sales
                if self.order_id.order_type:
                    used_under = ['IM', 'All']
                elif self.order_id.order_from:
                    used_under = ['PT', 'All']
                else:
                    # For some reason, order from is coming up empty for pharmacy
                    used_under = ['PH', 'All']

            for line in self:

                #Assign warehouse
                if self.order_id.order_from:
                    if self.order_id.order_from.startswith('PH'):
                        line.wareh = line.order_id.wareh
                    elif not line.wareh and line.product_id.default_warehouse.wh_type == self.order_id.order_type:
                        line.wareh = line.product_id.default_warehouse
                elif not line.wareh and line.product_id.default_warehouse.wh_type == self.order_id.order_type:
                    line.wareh = line.product_id.default_warehouse

                if not line.product_uom or line.product_uom==line.product_id.uom_id:
                    line.product_uom = line.product_id.import_uom_new
                # Get discounts/additional payments per type
                type_rates = self.env['droga.price.discount.per.type'].search(
                    [('cust_type', '=', self.order_id['partner_id']['cust_type_ext'].id), ('status', '=', 'Active'),
                     ('product_group', '=', line.product_id.categ_id.id), ('used_under', 'in', used_under)])
                core_rate = 0  # Discount rate for core products defined
                non_core_rate = 0  # Discount rate for non-core products defined
                all_rate = 0  # Discount rate for all products defined

                for rate in type_rates:
                    if rate['core_products_or_all'] == 'Core':
                        core_rate = core_rate + rate['percent']
                    elif rate['core_products_or_all'] == 'Noncore':
                        non_core_rate = non_core_rate + rate['percent']
                    elif rate['core_products_or_all'] == 'All':
                        all_rate = all_rate + rate['percent']

                # Product and customer combination discount rules
                product_customer = self.env['droga.price.discount.per.product.customer'].search(
                    ['|', ('payment_term', '=', self.order_id['payment_term_id'].id), ('payment_term', '=', False),
                     ('product', '=', line.product_id.id), ('status', '=', 'Active'),
                     ('cust', '=', self.order_id['partner_id'].id), ('used_under', 'in', used_under)])
                for rate in product_customer:
                    all_rate = all_rate + rate['percent']

                uom_rate = line.product_uom.factor / (
                    line.product_id.import_uom_new.factor if line.product_id.import_uom_new.factor != 0 else (
                        line.product_uom.factor if line.product_uom.factor != 0 else 1))
                # Product and quantity discount rules
                product_qty = self.env['droga.price.discount.per.product.qty'].search(
                    ['|', ('payment_term', '=', self.order_id['payment_term_id'].id), ('payment_term', '=', False),
                     ('product', '=', line.product_id.id), ('status', '=', 'Active'),
                     ('from_qty', '<=', line.product_uom_qty * uom_rate),
                     ('to_qty', '>=', line.product_uom_qty * uom_rate),
                     ('used_under', 'in', used_under)])
                for rate in product_qty:
                    all_rate = all_rate + rate['percent']

                if line.store_placement:
                    line.price_unit = 0.0
                    continue
                if not line.product_uom or not line.product_id or not line.order_id.pricelist_id:
                    line.price_unit = 0.0
                    line.std_unit_price = 0.0
                else:
                    price = line.product_id.list_price*(line.product_id.product_tmpl_id.import_uom_new.factor/line.product_uom.factor)
                    if not line.tender_origin_form_tender and not line.manual_price:
                        line.price_unit = price* ((1 + ((core_rate + all_rate) / 100)) if line.product_id.is_core_product else (
                                1 + ((non_core_rate + all_rate) / 100)))

                    line.std_unit_price = price * ((1 + ((core_rate + all_rate) / 100)) if line.product_id.is_core_product else (
                            1 + ((non_core_rate + all_rate) / 100)))

                line.price_unit_before_discount = line.std_unit_price

            self.calc_sales_totals()

            core_sum = self.order_id.core_sum
            non_core_sum = self.order_id.non_core_sum

            #Payment type discount rules. This is here because it's calculated after default selling price has been set
            amount_rates = self.env['droga.price.discount.per.amount'].search(
                [('payment_term', '=', self.order_id['payment_term_id'].id), ('status', '=', 'Active'),
                 ('used_under', 'in', used_under)])

            core_rate = 0
            non_core_rate = 0
            all_rate = 0
            for rate in amount_rates:
                if rate['core_products_or_all'] == 'Core' and rate['from_amt'] <= core_sum <= rate['to_amt']:
                    core_rate = core_rate + rate['percent']
                elif rate['core_products_or_all'] == 'Noncore' and rate['from_amt'] <= non_core_sum <= rate['to_amt']:
                    non_core_rate = non_core_rate + rate['percent']
                elif rate['core_products_or_all'] == 'All' and rate['from_amt'] <= core_sum + non_core_sum <= rate[
                    'to_amt']:
                    all_rate = all_rate + rate['percent']

            for lin in self.order_id.order_line:
                if not self.order_id.tender_origin_form_tender and not self.order_id.manual_price:
                    lin.price_unit = lin.price_unit_before_discount * (1 + ((core_rate + all_rate) / 100)) if lin.product_id.is_core_product else lin.price_unit_before_discount * (1 + ((non_core_rate + all_rate) / 100))
                lin.std_unit_price = lin.price_unit_before_discount * (1 + (
                                (core_rate + all_rate) / 100)) if lin.product_id.is_core_product else lin.price_unit_before_discount * (
                                1 + ((non_core_rate + all_rate) / 100))


            # self.order_id._get_sub_totals()
            super(sale_order_line, self)._compute_amount()

            self.calc_sales_totals()


class sale_order_ext(models.Model):
    _inherit = 'sale.order'
    core_sum = fields.Float('Core total', compute='_get_sub_totals')
    non_core_sum = fields.Float('Non-core total', compute='_get_sub_totals')
    state = fields.Selection(
        selection=[
            ('memb', "Member usage"),
            ('draft', "Quotation"),
            ('sent', "Quotation Sent"),
            ('price_request', "Price change approval"),
            ('price_request_pharma', "Price change approval"),
            ('req', "Operation manager"),
            ('fia', "Final approve"),
            ('cancel', "Cancelled"),
            ('sale', "Sales Order"),
            ('dispense', 'Dispensed'),
            ('done', "Locked"),
        ],
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')
    total_discount = fields.Float('Total discount')
    total_added = fields.Float('Total accrual')
    price_change_approver = fields.Many2one('res.users', compute='_get_approvers', store=True)
    operation_approver = fields.Many2one('res.users', compute='_get_approvers', store=True)
    final_approver = fields.Many2one('res.users', compute='_get_approvers', store=True)
    out_of_stock_items = fields.Char('Stock out items', compute='_get_stock_out')
    has_access = fields.Boolean(default=False, search='_has_access', compute='_compute_has_access')
    has_pharma_access = fields.Boolean(default=False, search='_has_pharma_access', compute='_compute_has_pharma_access')
    has_invoice_access = fields.Boolean(default=False, search='_has_invoice_access',
                                        compute='_compute_has_invoice_access')
    has_physio_access = fields.Boolean(default=False, search='_has_physio_access', compute='_compute_has_physio_access')
    sales_initiator = fields.Char('Sales person', store=True)
    #total_pharma = fields.Float('Total pharmacy before discount',compute='calc_sales_totals_pharma',store=True)
    #total_pharma_discount_groups = fields.Float('Total pharmacy discount apply groups', compute='calc_sales_totals_pharma', store=True)
    #total_disc_pharma = fields.Float('Total discount for pharmacy',compute='calc_sales_totals_pharma',store=True)
    total_pharma = fields.Float('Total pharmacy before discount',store=True)
    total_pharma_discount_groups = fields.Float('Total pharmacy discount apply groups', store=True)
    total_disc_pharma = fields.Float('Total discount for pharmacy',store=True)
    show_beauty_button=fields.Boolean(compute='_show_supp_vit')
    show_vit_button = fields.Boolean(compute='_show_supp_vit')
    points_to_deduct=fields.Float('Points to deduct')
    deduct_type=fields.Char('Type')
    deduct_descr=fields.Char(compute='_compute_desc')
    inv_number=fields.Char('Invoice Number')
    @api.depends('total_disc_pharma','deduct_type')
    def _compute_desc(self):
        for rec in self:
            rec.deduct_descr=(str(round(rec.total_disc_pharma,2)) if rec.total_disc_pharma else '')+', '+(rec.deduct_type if rec.deduct_type else '')
            for r in rec.order_line:
                r._compute_price_unit()

    @api.depends('order_line.price_unit', 'order_line.product_uom_qty','order_line.product_uom_pharma_qty', 'partner_id', 'payment_term_id')
    def calc_sales_totals_pharma(self,line):
        total_pharma = 0
        total_with_discount = 0
        total_pharma_discount_groups = 0
        groups = self.env['droga.pharma.high.value.pruchase'].search([('status', '=', 'Active')])[0].prod_group if len(
            self.env['droga.pharma.high.value.pruchase'].search([('status', '=', 'Active')])) > 0 else []

        for ln in line.order_id.order_line:
            total_pharma=total_pharma+(ln.product_uom_pharma_qty*ln.phar_cont_price)
            total_with_discount=total_with_discount+(ln.product_uom_pharma_qty*ln.price_unit)
            if ln.product_id.product_tmpl_id.categ_id in groups:
                total_pharma_discount_groups+=(ln.product_uom_pharma_qty if ln.product_uom_pharma_qty!=0 else line.product_uom_pharma_qty)*(ln.phar_cont_price if ln.phar_cont_price!=0 else ln.product_id.list_price_phar)
        line.order_id.total_pharma=total_pharma
        line.order_id.total_disc_pharma = total_pharma-total_with_discount
        line.order_id.total_pharma_discount_groups=total_pharma_discount_groups
    @api.depends('partner_id')
    def _show_supp_vit(self):
        for rec in self:
            rec.show_beauty_button=False
            rec.show_vit_button = False
            if rec.partner_id.is_company:
                return
            discount_per_acc = self.env['droga.pharma.reward.issue'].search([('status','=','Active'),('type','in',('Referral reward','Speciality service reward'))])
            for disc in discount_per_acc:
                if disc.reward_req_points <= sum(self.env['droga.pharma.points.earned'].search(
                            [('customer', '=', rec.partner_id.id), ('type', '=', disc.type), (
                                    'earned_date', '>=',
                                    date.today() + timedelta(days=-disc.reward_req_frequ))]).mapped(
                            'points_earned')):
                    if disc.type=="Referral reward":
                        rec.show_beauty_button=True
                    else:
                        rec.show_vit_button = True
    def get_wareh(self):
        if self.order_from=="PT":
            list=self.env.user.warehouse_ids_pt_disp
        else:
            list=self.env.user.warehouse_ids_ph_disp + self.env.user.warehouse_ids_im_ws
        return list[
            0].id if len(
            list) > 0 else False

    wareh = fields.Many2one('stock.warehouse', string='User linked pharmacy warehouse', compute='_get_pharma_wh',store=True)

    def unlink(self):
        raise ValidationError(
            "You can't delete sales transaction, either cancel it or pass a correcting entry.")
    @api.depends('name')
    def _get_pharma_wh(self):
        for rec in self:
            if rec.order_from=="PH":
                rec.wareh = self.env.user.warehouse_ids_ph_disp[
                    0].id if len(
                    self.env.user.warehouse_ids_ph_disp) > 0 else False
            elif rec.order_from=="PT":
                rec.wareh = self.env.user.warehouse_ids_pt_disp[
                    0].id if len(
                    self.env.user.warehouse_ids_pt_disp) > 0 else False
            else:
                rec.wareh = self.env.user.warehouse_ids_im_ws[
                    0].id if len(
                    self.env.user.warehouse_ids_im_ws) > 0 else False

    def _has_invoice_access(self, operator, value):
        if operator == '=':
            if self.env.user.has_group('droga_sales.sales_import_invoicer'):
                return [
                    ('id', 'in', [x.id for x in self.env['sale.order'].sudo().search([('order_from', '=', 'IM-IM')])])]
            if self.env.user.has_group('droga_sales.sales_wholesale_invoicer'):
                return [
                    ('id', 'in', [x.id for x in self.env['sale.order'].sudo().search([('order_from', '=', 'IM-WS')])])]
            if self.env.user.has_group('droga_sales.ema_invoicer'):
                return [
                    ('id', 'in', [x.id for x in self.env['sale.order'].sudo().search([('order_from', '=', 'EM-EM')])])]
            else:
                return [('id', 'in', [])]
        else:
            return [('id', 'in', [])]

    def _compute_has_invoice_access(self):
        has_import_acc = self.env.user.has_group('droga_sales.sales_import_approve_admin')
        has_ws_acc = self.env.user.has_group('droga_sales.sales_wholesale_invoicer')
        has_ema_acc = self.env.user.has_group('droga_sales.ema_invoicer')

        for rec in self:
            if (rec.order_from == "IM-IM" and has_import_acc) or (rec.order_from == "IM-WS" and has_ws_acc) or (
                    rec.order_from == "EM-EM" and has_ema_acc):
                rec.has_access = True
            else:
                rec.has_access = False

    def _compute_has_pharma_access(self):
        for rec in self:
            if rec.wareh in self.env.user.warehouse_ids_ph_disp.ids or rec.wareh in self.env.user.warehouse_ids_ph.ids:
                return True
            else:
                return False

    def _compute_has_physio_access(self):
        for rec in self:
            if rec.wareh in self.env.user.warehouse_ids_pt_disp.ids or rec.wareh in self.env.user.warehouse_ids_pt.ids:
                return True
            else:
                return False

    def _compute_has_access(self):
        if self.env.user.has_group('droga_crm.crm_cust'):
            for rec in self:
                rec.has_access = True
        elif not self.env.user.name.startswith('CRM'):
            for rec in self:
                if self.env.user.id == rec.user.id:
                    rec.has_access = True
        else:
            for rec in self:
                ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
                if ses[0].pro_id == rec.pr_sales:
                    rec.has_access = True

    def _has_access(self, operator, value):
        if operator == '=':
            if self.env.user.has_group('droga_crm.crm_cust'):
                sales = self.env['sale.order'].sudo().search([(1, '=', 1)])
                return [('id', 'in', [x.id for x in sales])]
            if not self.env.user.name.startswith('CRM'):
                sales = self.env['sale.order'].sudo().search([('user_id', '=', self.env.user.id)])
                return [('id', 'in', [x.id for x in sales])]
            ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
            if len(ses) == 0:
                return [('id', 'in', [])]
            else:
                is_rec_owner = self.env['sale.order'].sudo().search([('pr_sales', '=', ses[0].pro_id.ids[0])])
                is_rec_inside_self = self.search([]).filtered(lambda x: x.pr_sales == ses[0].pro_id)
                return ['|', ('id', 'in', [x.id for x in is_rec_owner] if is_rec_owner else False),
                        ('id', 'in', [x.id for x in is_rec_inside_self] if is_rec_inside_self else False)]
        else:
            return [('id', 'in', [])]

    def _has_pharma_access(self,operator,value):
        if operator=='=':
            sales = self.env['sale.order'].sudo().search(['|',('wareh', 'in', self.env.user.warehouse_ids_ph.ids),('wareh', 'in', self.env.user.warehouse_ids_ph_disp.ids)])
            return [('id', 'in', [x.id for x in sales])]
        else:
            return [('id', 'in', [])]

    def _has_physio_access(self,operator,value):
        if operator=='=':
            sales = self.env['sale.order'].sudo().search([('wareh', 'in', self.env.user.warehouse_ids_pt_disp.ids)])
            return [('id', 'in', [x.id for x in sales])]
        else:
            return [('id', 'in', [])]

    def conf_and_invoice(self):
        self.action_confirm()
        self.create_inv_local()

    def cancel_sales(self):
        for rec in self:
            if (rec.state=='draft' or rec.state=='sale') and len(self.env["account.move"].search([('invoice_origin', '=', rec.name)]))==0:
                rec._action_cancel()

    def _prepare_confirmation_values(self):

        return {
            'state': 'sale'
        }

    def create_inv_local(self):
        # self.action_confirm()
        x = {
            'advance_payment_method': 'delivered',
            'sale_order_ids': [self.id],
        }
        y = self.env['sale.advance.payment.inv'].create(x)
        y.create_invoices()

        invoices = self.mapped('invoice_ids')
        action = self.env['ir.actions.actions']._for_xml_id('account.action_move_out_invoice_type')
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_move_type': 'out_invoice',
        }
        if len(self) == 1:
            context.update({
                'default_partner_id': self.partner_id.id,
                'default_partner_shipping_id': self.partner_shipping_id.id,
                'default_invoice_payment_term_id': self.payment_term_id.id or self.partner_id.property_payment_term_id.id or
                                                   self.env['account.move'].default_get(
                                                       ['invoice_payment_term_id']).get('invoice_payment_term_id'),
                'default_invoice_origin': self.name,
                'default_user_id': self.user_id.id,

            })
        action['context'] = context

        #Insert reward points here

        if self.referred_by:
            if len(self.env['sale.order'].search([('state','in',('sale','dispense')),('id','!=',self.id),('referred_by','=',self.referred_by.id),('partner_id','=',self.partner_id.id)]))==0:
                points_to_earn = self.env['droga.pharma.referral.reward'].search([('from_amt','<',self.amount_total),('to_amt','>',self.amount_total)])[
                    0].points_to_gain if len(
                    self.env['droga.pharma.referral.reward'].search([('from_amt','<',self.amount_total),('to_amt','>',self.amount_total)])) > 0 else 0
                points = {
                    'type': 'Referral reward',
                    'customer': self.referred_by.id,
                    'sales_ref': self.id,
                    'earned_date': self.date_order,
                    'points_earned': points_to_earn,
                }

                self.env['droga.pharma.points.earned'].create(points)


        if self.points_to_deduct>1:
            points = {
                'type': self.deduct_type,
                'customer': self.referred_by.id,
                'sales_ref': self.id,
                'earned_date': self.date_order,
                'points_earned': self.points_to_deduct*-1,
            }

            self.env['droga.pharma.points.earned'].create(points)

        if self.partner_id.id==15488 or self.order_from!='PH' or self.partner_id.is_company or self.points_to_deduct>1:
            return action

        services_count = self.order_line.filtered(
            lambda x: x.product_id.product_tmpl_id.detailed_type == 'service')

        if len(services_count)>0:
            points_to_earn=self.env['droga.pharma.reward.gain'].search([('type','=','Services')])[0].points_to_gain if len(self.env['droga.pharma.reward.gain'].search([('type','=','Services')]))>0 else 0
            type='Speciality service reward'
        else:
            points_to_earn = self.env['droga.pharma.reward.gain'].search([('type', '=', 'Stocked')])[
                0].points_to_gain if len(
                self.env['droga.pharma.reward.gain'].search([('type', '=', 'Stocked')])) > 0 else 0
            type = 'Purchase reward'
        points = {
            'type': type,
            'customer': self.partner_id.id,
            'sales_ref': self.id,
            'earned_date': self.date_order,
            'points_earned': points_to_earn,
        }

        self.env['droga.pharma.points.earned'].create(points)

        return action

    @api.depends('order_line.product_template_id')
    def _get_stock_out(self):
        for rec in self:
            rec.out_of_stock_items = ''

    def _get_approvers(self):

        for rec in self:
            if rec.order_from:
                if rec.order_from.startswith("P"):
                    rec.price_change_approver=self.env.ref("droga_pharma.pharma_director").users.filtered(
                        lambda m: self.env.company.id in m.company_ids.ids).ids[0] if len(
                        self.env.ref("droga_pharma.pharma_director").users.filtered(
                        lambda m: self.env.company.id in m.company_ids.ids).ids) > 0 else None

                    rec.final_approver = self.env.user.id
                    rec.operation_approver = self.env.user.id
                    return

            rec.price_change_approver = self.env.ref("droga_sales.sales_price_change_admin").users.filtered(
                lambda m: self.env.company.id in m.company_ids.ids).ids[0] if len(
                self.env.ref("droga_sales.sales_price_change_admin").users.filtered(
                    lambda m: self.env.company.id in m.company_ids.ids).ids) > 0 else None

            if rec.order_type=='EX':
                rec.final_approver = self.env.ref("droga_sales.sales_droga_export_approver").users.filtered(
                    lambda m: self.env.company.id in m.company_ids.ids).ids[0] if len(
                    self.env.ref("droga_sales.sales_droga_export_approver").users.filtered(
                        lambda m: self.env.company.id in m.company_ids.ids).ids) > 0 else None
            else:
                rec.final_approver = self.env.ref("droga_sales.sales_import_final_approve").users.filtered(
                    lambda m: self.env.company.id in m.company_ids.ids).ids[0] if len(
                    self.env.ref("droga_sales.sales_import_final_approve").users.filtered(
                        lambda m: self.env.company.id in m.company_ids.ids).ids) > 0 else None
            if rec.order_type == 'IM':
                rec.operation_approver = self.env.ref("droga_sales.sales_import_approve_admin").users.filtered(
                    lambda m: self.env.company.id in m.company_ids.ids).ids[0] if len(
                    self.env.ref("droga_sales.sales_import_approve_admin").users.filtered(
                        lambda m: self.env.company.id in m.company_ids.ids).ids) > 0 else None
            else:
                rec.operation_approver = self.env.ref("droga_sales.sales_wholesale_approve_admin").users.filtered(
                    lambda m: self.env.company.id in m.company_ids.ids).ids[0] if len(
                    self.env.ref("droga_sales.sales_wholesale_approve_admin").users.filtered(
                        lambda m: self.env.company.id in m.company_ids.ids).ids) > 0 else None

    def _get_pr_sales_logged(self):
        if not request:
            return False
        ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
        return False if len(ses) == 0 else ses[0].pro_id.ids[0]

    pr_sales = fields.Many2one('droga.pro.sales.master', readonly=True, store=True, string="Promotor ID",
                               default=_get_pr_sales_logged)
    pr_sales_logged = fields.Many2one('droga.pro.sales.master', string="Promotor ID log", store=False,
                                      default=_get_pr_sales_logged)
    pr_avail_areas = fields.Many2many(related='pr_sales.p_regions')

    is_record_owner = fields.Boolean('Show plan', store=False, compute="_is_record_owner", search="_search_field")

    def action_confirm(self):

        for rec in self:
            rec.validate_form()
            if not rec.order_type and self.env.company.id == 1:
                if rec.order_from.startswith('PH'):
                    if not rec.wareh:
                        raise ValidationError("Employee is not linked to a pharmacy chain branch.")
                    for res in rec.order_line:
                        res.wareh = rec.wareh
                        res.product_id.product_tmpl_id.invoice_policy = 'order'
                    if rec.manual_price_pharma and rec.state!='price_request_pharma':
                        rec.state='price_request_pharma'
                        return
                else:
                    for res in rec.order_line:
                        #res.wareh =  32 if rec.order_from == 'PT-Bole' else 31
                        res.product_id.product_tmpl_id.invoice_policy = 'order'
            else:
                if rec.order_type:
                    rec.order_from = 'IM-' + rec.order_type
                for res in rec.order_line:
                    res.product_id.product_tmpl_id.invoice_policy = 'delivery'

        for rec in self:
            pickings=self.env['stock.picking'].search([('origin','=',rec.name),('state','!=','cancel'),('state','!=','done')])
            for pick in pickings:
                pick.action_assign()

        if self.deduct_type=='Discount for loyal customer':
            points = {
                'type': 'Discount for loyal customer',
                'customer': self.partner_id.id,
                'earned_date': self.date_order,
                'sales_ref':self.id,
                'points_earned': self.points_to_deduct * -1,
            }

            self.env['droga.pharma.points.earned'].create(points)

        return super(sale_order_ext, self).action_confirm()

    def validate_form(self):
        if self.state == "sale" or self.env.company.id not in (1,2,3):
            return
        message = ''

        #Pharmacy validations below
        if self.order_from.startswith('PH'):
            price_changed=self.order_line.filtered(lambda x: math.ceil(round(x.price_unit/(1+((x.disc_applied if x.disc_applied!=-100 else 0)/100)),2))!=math.ceil(x.phar_cont_price) or x.price_unit==0)
            if len(price_changed)>0 and not self.manual_price_pharma:
                message = message + ('\n' if message else '') + "Price can not be edited or be zero."
            if self.customer_emp:
                if self.customer_emp.parent_customer.id!=self.partner_id.id:
                    message = message + ('\n' if message else '') + "Please make sure employee is under stated customer."

        order_lines_nowareh = self.order_line.filtered(
            lambda x: not x.wareh)
        if (len(order_lines_nowareh) > 0):

            for ln in self.order_line:
                if self.order_from:
                    if self.order_from.startswith('PH'):
                        ln.wareh = ln.order_id.wareh
                    elif not ln.wareh and ln.product_id.default_warehouse.wh_type == self.order_type:
                        ln.wareh = ln.product_id.default_warehouse
                elif not ln.wareh and ln.product_id.default_warehouse.wh_type == self.order_type:
                    ln.wareh = ln.product_id.default_warehouse

            order_lines_nowareh = self.order_line.filtered(
                lambda x: not x.wareh)

            if (len(order_lines_nowareh) > 0):
                message = message + ('\n' if message else '') + "Warehouse must be filled for each order line."

        order_lines_nowareh = self.order_line.filtered(
            lambda x: x.wareh.wh_type != self.order_type)
        if (len(order_lines_nowareh) > 0 and self.order_type):
            message = message + ('\n' if message else '') + "Please check if all warehouses are under " + dict(
                self._fields['order_type'].selection).get(
                self.order_type) + "."
        self._get_approvers()
        if not self.price_change_approver:
            raise ValidationError("Price change approver is not configured for client.")
        if not self.final_approver:
            raise ValidationError("Final approver is not configured for client.")
        if not self.operation_approver:
            raise ValidationError("Operation manager is not configured for client.")
        for rec in self.order_line:
            rec.is_prod_available_method()
        order_lines_negative = self.order_line.filtered(
            lambda x: x.is_prod_available == 'False')
        if (len(order_lines_negative) > 0):
            products = ''
            for lin in order_lines_negative:
                products += lin.product_template_id.default_code + ', '
            message = message + ('\n' if message else '') + "Product quantity is out of stock for " + products
            # raise ValidationError("Product quantity is out of stock for " + products)

        for so in self:
            if not so.partner_id.cust_type_ext and not so.order_from.startswith('P'):
                message = message + "Customer type must be registered for customer!"
            if not so.partner_id.city_name and not so.order_from.startswith('P'):
                message = message + ('\n' if message else '') + message + "City must be registered for customer!"
            if not so.partner_id.vat and so.company_id.id==1:
                message = message + ('\n' if message else '') + message + "Tin No must be registered for customer!"
                # raise ValidationError("Tin No must be registered for customer!")
            if so.order_from.startswith('PH'):
                if so.partner_id.available_amount_pharma < so.amount_total and so.payment_term_id.apply_credit_limit and so.company_id.id in (1,2):
                    message = message + ('\n' if message else '') + "You cannot exceed credit limit!"
                    # raise ValidationError("You cannot exceed credit limit!")
                if so.customer_emp:
                    if so.customer_emp.employee_credit_limit!=0 and so.customer_emp.employee_credit_limit <so.amount_total and so.payment_term_id.apply_credit_limit:
                        message = message + ('\n' if message else '') + "Maximum credit limit for employee is "+str(so.customer_emp.employee_credit_limit)
                if so.mature_amount_pharma > 0:
                    message = message + (
                        '\n' if message else '') + "Please settle matured amounts before initiating another sales!"
            else:
                if so.partner_id.available_amount < so.amount_total and so.payment_term_id.apply_credit_limit and not so.partner_id.id in [
                    15390] and so.company_id.id in (1,2):
                    message = message + ('\n' if message else '') + "You cannot exceed credit limit!"
                    # raise ValidationError("You cannot exceed credit limit!")
                if so.mature_amount > 0:
                    message = message + (
                        '\n' if message else '') + "Please settle matured amounts before initiating another sales!"
                if so.payment_term_id.apply_credit_limit and so.payment_term_id.id not in so.partner_id.property_supplier_payment_term_id.allowed_terms.ids and so.company_id.id in (1,2):
                    message = message + (
                        '\n' if message else '') + "Payment term is not allowed for customer"
            if so.amount_total < so.payment_term_id.min_amount and not so.tender_origin_form_tender and (not so.order_from.startswith('PT') if type(so.order_from) is str else True) and so.company_id.id in (1,2):
                message = message + (
                    '\n' if message else '') + "Minimum order amount for " + so.payment_term_id.name + " is " + str(
                    so.payment_term_id.min_amount)
                # raise ValidationError("Minimum order amount for "+so.payment_term_id.name+" is "+str(so.payment_term_id.min_amount))
            if not so.pr_sales and self.env.user.name.startswith('CRM'):
                message = message + ('\n' if message else '') + "Please login before requesting a sales order!"
                # raise ValidationError("Please login before registering a sales order!")

                # raise ValidationError("Please settle matured amounts before initiating another sales!")

        if message:
            raise ValidationError(message)

        # This is for import or wholesale sales under Droga
        if so.order_type and self.env.company.id == 1:
            so.order_from = 'IM-' + so.order_type

    def save_request_button(self):
        self.validate_form()
        self.set_activity_done()
        self.ensure_one()

        # Physiotheraphy order automatic confirmation
        if self.order_type == 'PT':
            self.action_confirm()
        elif self.order_type=='EX':
            self.state = 'fia'
        # Manual price and discounts routing to price change approver
        elif ((self.manual_price and len(self.order_line.filtered(
                lambda x: x.std_unit_price > x.price_unit > 0)) > 0) or self.tender_origin_form_tender) and self.state == 'draft':
            self.state = 'price_request'
        elif self.state == 'draft':
            self.state = 'req'

        # self.set_activity_done()

    def reject_order(self):
        self.ensure_one()
        self.set_activity_done()
        self.state = 'draft'

    def price_approval(self):
        self.validate_form()
        self.ensure_one()
        self.set_activity_done()
        self.state = 'req'

    def operation_confirm(self):
        self.validate_form()
        self.ensure_one()
        self.set_activity_done()

        if self.order_type != 'IM':
            self.action_confirm()
        else:
            self.state = 'fia'

    def final_approval(self):
        self.validate_form()
        self.ensure_one()
        self.set_activity_done()
        self.action_confirm()

    @api.depends('pr_sales_logged')
    def _is_record_owner(self):
        for rec in self:
            if rec.pr_sales == rec.pr_sales_logged:
                rec.is_record_owner = True
            else:
                rec.is_record_owner = False

    def _search_field(self, operator, value):
        if operator == '=':
            ses = self.env['droga.pro.sales.master.visit'].search([('s_id', '=', request.session.sid)])
            if len(ses) == 0:
                return [('id', 'in', [])]
            else:
                is_rec_owner = self.env['droga.customer.visit.header'].sudo().search(
                    [('pr_sales', '=', ses[0].pro_id.ids[0])])
                is_rec_inside_self = self.search([]).filtered(lambda x: x.pr_sales == ses[0].pro_id)
                return ['|', ('id', 'in', [x.id for x in is_rec_owner] if is_rec_owner else False),
                        ('id', 'in', [x.id for x in is_rec_inside_self] if is_rec_inside_self else False)]
        else:
            return [('id', 'in', [])]

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.name)])
        for act in activity:
            act.sudo().action_done()

    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term',
        string="Payment Terms", tracking=True,
        compute='_compute_payment_term_id', required=True,
        store=True, readonly=False, precompute=True, check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    @api.depends('partner_id')
    def _compute_payment_term_id(self):
        for order in self:
            order = order.with_company(order.company_id)
            order.payment_term_id = order.partner_id.property_payment_term_id if order.partner_id.property_payment_term_id else order.payment_term_id

    @api.depends('order_line.price_unit', 'order_line.product_uom_qty', 'partner_id', 'payment_term_id')
    def _get_sub_totals(self):
        order_lines_core = None
        order_lines_non_core = None
        core_sum = 0
        non_core_sum = 0
        try:
            order_lines_core = self.order_line.filtered(
                lambda x: not x.display_type and x.product_id.is_core_product and x.id.ref != None)
            order_lines_non_core = self.order_line.filtered(
                lambda x: not x.display_type and not x.product_id.is_core_product and x.id.ref != None)
        except:
            order_lines_core = self.order_line.filtered(
                lambda x: not x.display_type and x.product_id.is_core_product and x.id != None)
            order_lines_non_core = self.order_line.filtered(
                lambda x: not x.display_type and not x.product_id.is_core_product and x.id != None)

        for cs in order_lines_core:
            core_sum = core_sum + (cs.product_uom_qty * cs.price_unit)

        for ncs in order_lines_non_core:
            non_core_sum = non_core_sum + (ncs.product_uom_qty * ncs.price_unit)

        self['core_sum'] = core_sum
        self['non_core_sum'] = non_core_sum
        self.order_line._compute_price_unit()

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):

        res = super().get_view(view_id, view_type, **options)

        doc = etree.XML(res['arch'])

        if view_type == 'form':

            for node in doc.xpath("//field"):
                if node.get("modifiers") is None or node.get("name") in ('name', 'amount_total', 'selling_price','product_uom','wareh','date_order','tax_id', 'age'):
                    continue
                modifiers = simplejson.loads(node.get("modifiers"))
                if self.user_has_groups('droga_sales.sales_price_change_admin') or self.user_has_groups(
                        'droga_sales.sales_import_approve_admin') or self.user_has_groups(
                    'droga_sales.sales_wholesale_approve_admin'):
                    modifiers['readonly'] = [['state', 'not in', ('draft', 'req', 'price_request', 'memb')]]
                else:
                    modifiers['readonly'] = [['state', 'not in', ('draft', 'memb','req')]]

                node.set('modifiers', simplejson.dumps(modifiers))
            res['arch'] = etree.tostring(doc)

        return res


class sale_order_line_mail_inherit(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line', 'mail.thread', 'mail.activity.mixin', 'image.mixin']


class account_move_inherit(models.Model):
    _inherit = 'account.move'
    account_move_linked_analytic = fields.Many2one('account.analytic.account')

    @api.model
    def create(self, vals):
        analytic=0
        if 'invoice_origin' in vals:
            if type(vals['invoice_origin']) is str:
                if vals['invoice_origin'].startswith('SO'):
                    sale_order=self.env['sale.order'].search([('name','=',str(vals['invoice_origin'])),('company_id','=',1)])
                    if len(sale_order)>0:
                        if 'invoice_line_ids' in vals:
                            for line in vals['invoice_line_ids']:
                                if sale_order[0].order_from.startswith('PH') or sale_order[0].order_from.startswith('PT'):
                                    line[2]['analytic_distribution'] = {241: 100,sale_order[0].order_line.wareh.linked_analytic.id: 100}
                                    analytic=sale_order[0].order_line.wareh.linked_analytic.id
                                elif sale_order[0].tender_origin_form_tender:
                                    line[2]['analytic_distribution'] = {23: 100, sale_order[0].order_line.wareh.linked_analytic.id: 100}
                                    analytic = sale_order[0].order_line.wareh.linked_analytic.id
                                else:
                                    line[2]['analytic_distribution'] = {24: 100, sale_order[0].order_line.wareh.linked_analytic.id: 100}
                                    analytic = sale_order[0].order_line.wareh.linked_analytic.id

                        for so_line in sale_order.order_line:
                            so_line.write({'invoice_date': datetime.now()})
                #get order type and fill analytic
        res=super(account_move_inherit, self).create(vals)
        res.account_move_linked_analytic=analytic
        return res
