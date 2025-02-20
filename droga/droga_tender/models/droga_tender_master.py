from email.policy import default
import pandas as pd

from odoo import models, fields, api
from datetime import datetime, date, timedelta

from odoo.exceptions import ValidationError
from ..custom_libraries import eth_to_greg_date_conv


class droga_tender_master(models.Model):
    _name = 'droga.tender.master'
    _description = 'Tender master file'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ten_name'

    # region fields definition
    # Date fields
    posted_date_gre = fields.Date("Posted/floated date GRE", required=True, compute="conv_posted_date", store=True,
                                  inverse='inverse_posted_date', help="Time should be in Ethiopian format not AM/PM.")
    latest_invoice_date=fields.Date('Invoice date')

    @api.depends("posted_date_eth")
    def conv_posted_date(self):
        try:
            converted_date = eth_to_greg_date_conv.converter.eth_to_greg_convert(
                int(self.posted_date_eth.split("-")[0]), int(self.posted_date_eth.split("-")[1]),
                2000 + int(self.posted_date_eth.split("-")[2]))
            self.posted_date_gre = converted_date
        except Exception as e:
            self.posted_date_eth = ""

    def inverse_posted_date(self):
        pass

    closing_date_gre = fields.Datetime("Closing date and time GRE", required=True, compute="conv_close_date",
                                       store=True, inverse='inverse_close_date',
                                       help="Time should be in Ethiopian format not AM/PM.")

    @api.depends("closing_date_eth", "float_period", "posted_date_gre", "open_date_gre","period_type")
    def conv_close_date(self):
        for rec in self:
            try:
                if rec.closing_date_eth == '':
                    if rec.period_type=='wd':
                        date_adder=rec.posted_date_gre
                        fp=int(rec.float_period)
                        while fp>0:
                            date_adder += timedelta(days=1)
                            if date_adder.weekday() >= 5:  # sunday = 6
                                continue
                            fp -= 1

                        rec.closing_date_gre=date_adder + timedelta(days=int(rec.get_ext_days_add(rec.posted_date_gre, date_adder)))
                        #if date_to.weekday()!=4:
                        #    rec.closing_date_gre=rec.closing_date_gre+timedelta(days=int(rec.get_ext_days_add(date_to,rec.closing_date_gre)))
                        if rec.closing_date_gre.weekday()==5 or rec.closing_date_gre.weekday()==6:
                            rec.closing_date_gre = rec.closing_date_gre + timedelta(days=7-rec.closing_date_gre.weekday())
                    else:
                        rec.closing_date_gre = rec.posted_date_gre + timedelta(days=int(rec.float_period))
                else:
                    converted_date = eth_to_greg_date_conv.converter.eth_to_greg_convert(
                        int(rec.closing_date_eth.split("-")[0]), int(rec.closing_date_eth.split("-")[1]),
                        2000 + int(rec.closing_date_eth.split("-")[2]))
                    rec.closing_date_gre = converted_date
            except Exception as e:
                rec.closing_date_eth = ""

    def inverse_close_date(self):
        pass

    open_date_gre = fields.Datetime("Opening date and time GRE", compute="conv_open_date", store=True,
                                    inverse='inverse_open_date', help="Time should be in Ethiopian format not AM/PM.")

    @api.depends("open_date_eth", 'posted_date_gre', 'float_period', 'closing_date_gre')
    def conv_open_date(self):
        try:
            if self.open_date_eth == '':
                self.open_date_gre = self.closing_date_gre
            else:
                converted_date = eth_to_greg_date_conv.converter.eth_to_greg_convert(
                    int(self.open_date_eth.split("-")[0]), int(self.open_date_eth.split("-")[1]),
                    2000 + int(self.open_date_eth.split("-")[2]))
                self.open_date_gre = converted_date
        except Exception as e:
            self.open_date_eth = ""

    def inverse_open_date(self):
        pass

    extension_date_gre = fields.Datetime("Extension date and time GRE", compute="conv_ext_date", store=True,
                                         inverse='inverse_ext_date',
                                         help="Time should be in Ethiopian format not AM/PM.")

    @api.depends("extension_date_eth", "closing_date_gre", "ext_period","period_type")
    def conv_ext_date(self):
        for rec in self:
            if not rec.ext_period:
                return
            try:
                if rec.extension_date_eth == '' and rec.period_type=='wd':
                    date_adder = rec.closing_date_gre
                    fp = int(rec.ext_period)
                    while fp > 0:
                        date_adder += timedelta(days=1)
                        if date_adder.weekday() >= 5:  # sunday = 6
                            continue
                        fp -= 1

                    rec.extension_date_gre = date_adder + timedelta(
                        days=int(rec.get_ext_days_add(rec.closing_date_gre, date_adder)))
                    # if date_to.weekday()!=4:
                    #    rec.closing_date_gre=rec.closing_date_gre+timedelta(days=int(rec.get_ext_days_add(date_to,rec.closing_date_gre)))
                    if rec.extension_date_gre.weekday() == 5 or rec.extension_date_gre.weekday() == 6:
                        rec.extension_date_gre = rec.extension_date_gre + timedelta(days=7 - rec.extension_date_gre.weekday())
                elif rec.extension_date_eth == '' and rec.period_type=='cd':
                    rec.extension_date_gre = rec.extension_date_gre + timedelta(days=int(rec.ext_period))
                else:
                    converted_date = eth_to_greg_date_conv.converter.eth_to_greg_convert(
                        int(rec.extension_date_eth.split("-")[0]), int(rec.extension_date_eth.split("-")[1]),
                        2000 + int(rec.extension_date_eth.split("-")[2]))
                    rec.extension_date_gre = converted_date
            except Exception as e:
                rec.extension_date_eth = ""

    def inverse_ext_date(self):
        pass

    # Text fields
    extension_date_eth = fields.Char("Extension date ETH(dd-mm-yy)", default='')
    posted_date_eth = fields.Char("Floated date ETH(dd-mm-yy)", default='')
    open_date_eth = fields.Char("Opening date ETH(dd-mm-yy)", default='')
    closing_date_eth = fields.Char("Closing date ETH(dd-mm-yy)", default='')
    float_period = fields.Char("Float period in days")
    ext_period = fields.Char("Extension period in days")
    remark = fields.Char("Remark")
    customer_tender_no = fields.Char("Customer tender no")
    procurement_title = fields.Char('Procurement title')
    ten_id = fields.Char('Droga tender ID')
    ten_name = fields.Char('Tender description', compute='_get_tender_description',store=True)

    # Selection fields
    period_type = fields.Selection([('wd', 'Working days'), ('cd', 'Calendar days')],default='cd')
    ext_period_type = fields.Selection([('wd', 'Working days'), ('cd', 'Calendar days')],
                                       string='Extension period type')
    bid_type = fields.Selection([('f', 'Foreign'), ('l', 'Local'), ('F+L', 'F+L')])
    status = fields.Selection([('active', 'Active'), ('closed', 'Closed')], compute="get_status")

    def get_ext_days_add(self,date_fromp,date_top):
        holidays=self.env['resource.calendar.leaves'].search([ '|','|','&',('date_to','>=',date_fromp),('date_from','<=',date_fromp),'&',('date_to','>=',date_top),('date_from','<=',date_top),'&',('date_from','>=',date_fromp),('date_to','<=',date_top)])
        days=0
        for hd in holidays:
            if hd.date_from.date()<date_fromp:
                if hd.date_to.date()>date_top:
                    days=days+(date_top-date_fromp).days
                else:
                    days = days + (hd.date_to.date() - date_fromp).days+1
            else:
                if hd.date_to.date()>date_top:
                    days=days+(date_top-hd.date_from.date()).days
                else:
                    days = days + (hd.date_to.date() - hd.date_from.date()).days+1

        #return days + self.count_weekends_pandas(date_fromp,date_top)
        return days

    def count_weekends_pandas(self,start_date, end_date):
        dates = pd.date_range(start_date, end_date)
        weekends = dates[dates.weekday.isin([5, 6])]
        return weekends.shape[0]
    @api.depends("closing_date_gre")
    def get_status(self):
        for record in self:
            if record.closing_date_gre:
                if (record.closing_date_gre < datetime.today()):
                    record.status = 'closed'
                else:
                    record.status = 'active'
            else:
                record.status = 'closed'

    # decimal fields
    bid_doc_purch_price = fields.Float("Bid document purchase price")
    price_validity_period = fields.Integer("Price validity period")

    security_period_in_days = fields.Integer('Bid sec. period in days')
    # bool fields
    refloat = fields.Boolean("Is refloated tender?", default=False)
    alert_sent = fields.Boolean("Alert sent?", default=False)
    active = fields.Boolean("Active", default=True)

    # relational fields selection
    media = fields.Many2one('droga.tender.settings.media', string='Media')
    bid_submit_place = fields.Many2one('droga.tender.settings.submission.place', string="Bid submission place")
    customer = fields.Many2one('droga.tender.settings.customers', string='Customer', required=True)
    customer_type=fields.Many2one('droga.cust.type',string='Customer type',related='customer.customer_type',store=True)
    assigned_person = fields.Many2one('hr.employee', string='Assigned Person')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    # relational fields models
    detail_tenders = fields.One2many('droga.tender.master.detail', 'parent_tender', required=True)
    detail_submissions_tec = fields.One2many('droga.tender.submission.detail', 'parent_tender_submission',
                                             required=True)
    detail_submissions_fin = fields.One2many('droga.tender.submission.detail', 'parent_tender_submission',domain=[('item_pro', '!=', False)])
    detail_submissions_additional = fields.One2many('droga.tender.submission.detail', 'parent_tender_submission')
    bid_security = fields.One2many('droga.tender.security.detail', 'bid_security')
    detail_performance = fields.One2many('droga.tender.performance.evaluation', 'parent_tender_performance')
    detail_contract = fields.One2many('droga.tender.contract', 'parent_tender_contract')

    # endregion

    def bid_security_open(self):
        return {
            'name': 'Bid security',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.tender.master',
            'view_id': self.env.ref('droga_tender.droga_tender_bid_view_form').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
            'context': {
                'default_tender_id': self.id,
                'default_security_for': 'Bid security'
            }
        }

    def sub_detail_open(self):
        return {
            'name': 'Tender submission details',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.tender.master',
            'view_id': self.env.ref('droga_tender.droga_tender_upcoming_view_form').id,
            'type': 'ir.actions.act_window',

            # This will pass the detail ID if a record is present
            'res_id': self.id,

            # When target is new, it will popup else it will use it's own form, wow ferenj
            # 'target': 'new',
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
                'default_tender_origin_form': self.id,
            },
            'domain':
                ([('tender_origin_form', '=', self.id)])
        }

    def pur_req_open(self):
        return {
            'name': 'Purchase request',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'droga.purchase.request.local',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {
                'default_tender_origin_form_tender': self.id,
            },
            'domain':
                ([('tender_origin_form_tender', '=', self.id)])
        }

    def open_tender(self):
        test=''
        return {
            'name': 'Tender',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'droga.tender.master',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'res_id':self.id
        }

    def order_sales(self):
        if not self.customer.master_cust_id:
            raise ValidationError("Please register customer before raising a sales order.!")
        else:
            order_lines = []
            lines_to_raise = self.env['droga.tender.performance.evaluation'].search(
                [('parent_tender_performance.id', '=', self.id), ('init_sales_order', '=', True),
                 ('droga_product', '!=', False)])
            for line in lines_to_raise:
                order_lines.append({
                    'name': line.droga_product.name,
                    'product_template_id': line.droga_product.id,
                    'product_uom': line.droga_product.uom_id.id,
                    'product_id':self.env['product.product'].search([('product_tmpl_id','=',line.droga_product.id)])[0].id ,
                    'product_uom_qty': line.award_quantity - line.ordered_qty,
                    'price_unit': line.unit_price,
                    'tender_line': line.id
                })
                line.init_sales_order=False
            return {
                'name': 'Sales order',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'sale.order',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'context': {
                    'default_tender_origin_form_tender': self.id,
                    'default_partner_id': self.customer.master_cust_id.id,
                    'default_order_line': order_lines,
                    'default_manual_price':True
                },
                'domain':
                    ([('tender_origin_form_tender','=', self.id)])
            }

    def bond_request(self):
        return {
            'name': 'Bond request',
            'view_type': 'tree',
            'view_mode': 'tree,form',
            'res_model': 'droga.bond.requests',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {
                'default_tender': self.id,
                'default_client': self.customer.master_cust_id.id,
                'default_request_type': self.bid_type,
                'default_po_number':self.customer_tender_no,
            },
            'domain':
                ([('tender', '=', self.id)])
        }

    def consignment_open(self):
        return {
            'name': 'Sample request',
            'view_type': 'tree',
            'view_mode': 'tree,form',
            'res_model': 'droga.inventory.consignment.issue',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {
                'default_tender_origin_form': self.id,
                'default_issue_type': 'SIF',
                'default_customer':self.customer.master_cust_id.id,
                'default_menu_from':'SR'
            },
            'domain':
                ([('tender_origin_form', '=', self.id)])
        }

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id,
                 record.customer["name"] + ' - ' + record.ten_id + " for " + record.closing_date_gre.strftime(
                     "%B %d,%Y")))
        return result

    @api.depends('customer')
    def _get_tender_description(self):
        for rec in self:
            rec.ten_name = rec.customer["name"] + ' - ' + rec.ten_id + " for " + rec.closing_date_gre.strftime(
                "%B %d,%Y")

    @api.model
    def create(self, vals_list):
        vals_list['ten_id'] = self.env['ir.sequence'].next_by_code(
            'droga.tender.master.custom.sequence')

        return super().create(vals_list)


    def action_set_archive(self):
        for rec in self:
            if rec.active:
                rec.active = False
            else:
                rec.active = True
