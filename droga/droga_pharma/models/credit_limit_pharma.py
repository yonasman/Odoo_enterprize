import io
from datetime import date
from io import BytesIO
import xlsxwriter
import base64
import re
try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes
from odoo import models, fields, api

class pharma_res_partner(models.Model):
    _name='res.partner.pharma2'
    _rec_name = 'name'
    partner=fields.Many2one('res.partner',required=True)
    name=fields.Char(string='Name',compute='_get_name',store=True)

    @api.depends('partner.name','partner.mobile')
    def _get_name(self):
        for rec in self:
            rec.name=(rec.partner.name if rec.partner.name else '')+(' - '+str(str(rec.partner.mobile).replace(" ","")).replace("251","0") if rec.partner.mobile else '')+(' - '+str(str(rec.partner.phone).replace(" ","")).replace("251","0") if rec.partner.phone else '')
class pharma_credit(models.Model):
    _inherit = 'res.partner'
    cust_credit_limit_pharma = fields.Float(string='Credit limit', tracking=True)
    unsettled_amount_pharma = fields.Monetary(compute='_compute_balance_pharma', string='Unsettled amount')
    available_amount_pharma = fields.Float(string='Credit balance', compute='_compute_balance_pharma')
    allowed_credit_terms=fields.Many2many('account.payment.term')
    manual_sales_extension_date=fields.Date('Manual sales extension date',tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ("requested", "Requested"),
        ("active", "Activated"),
    ], string='Status', default="draft", readonly=True, tracking=True)
    phar_approver=fields.Many2one('res.users',compute='_get_approver')

    @api.model
    def create(self, vals):
        result = super(pharma_credit, self).create(vals)
        self.env['res.partner.pharma2'].create({
            'partner':result.id
        })
        return result

    def visit_detail_open(self):
        return {
            'name': 'Health professional approval',
            # 'view_type': 'form',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'res.partner',
            'view_id': self.env.ref('droga_pharma.pharma_partner_view').id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
        }
    @api.depends('state')
    def _get_approver(self):
        for rec in self:
            rec.phar_approver = self.env.ref("droga_pharma.pharma_director").users.filtered(
                lambda m: self.env.company.id in m.company_ids.ids and m.id not in (2,51)).ids[0] if len(
                self.env.ref("droga_pharma.pharma_director").users.filtered(
                    lambda m: self.env.company.id in m.company_ids.ids and m.id not in (2,51)).ids) > 0 else None
    def open_price_hist(self):
        return {
            'name': 'Price lists',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'droga.pharma.price.list.header',
            'views': [[self.env.ref('droga_pharma.droga_pharma_price_list_tree').id, 'tree'],
                      [self.env.ref('droga_pharma.droga_pharma_price_list_form').id, 'form']],
            'type': 'ir.actions.act_window',
            'context': {
                'default_customer': self.id,
            },
            'domain': [('customer', '=', self.id)],
        }

    def request(self):
        for rec in self:
            rec.state='requested'

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_id', '=', self.id)])
        for act in activity:
            act.sudo().action_done()

    def approve(self):
        self.set_activity_done()
        for rec in self:
            rec.state='active'

    def amend(self):
        self.set_activity_done()
        for rec in self:
            rec.state='draft'

    @api.depends('debit', 'credit')
    def _compute_balance_pharma(self):
        for record in self:
            if record.id in [15390, 15488]:
                matured_invoices = []
            elif record.vat != '0000000000':
                matured_invoices = self.env['account.move'].search(
                    [('state', '=', 'posted'), ('journal_id.type', '=', 'sale'),('cost_center','like','Pharmacy%'),
                     ('payment_state', 'in', ['not_paid', 'partial']), ('partner_id.vat', '=', record.vat), '|',
                     ('partner_id.active', '=', True), ('partner_id.active', '=', False)])
            else:
                matured_invoices = self.env['account.move'].search(
                    [('state', '=', 'posted'), ('journal_id.type', '=', 'sale'),('cost_center','like','Pharmacy%'),
                     ('payment_state', 'in', ['not_paid', 'partial']), ('partner_id', '=', record.id), '|',
                     ('partner_id.active', '=', True), ('partner_id.active', '=', False)])
            tot_amount = 0
            for mi in matured_invoices:
                tot_amount = tot_amount + (
                    mi['amount_total_signed'] if mi['amount_residual'] == 0 else mi['amount_residual'])
            record.unsettled_amount_pharma = tot_amount
            # record.unsettled_amount = record.credit - record.debit

            record.available_amount_pharma = record.cust_credit_limit_pharma - record.unsettled_amount_pharma

class pharma_price_list_header(models.Model):
    _name = 'droga.pharma.price.list.header'
    _descr='Price list'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    contract_no=fields.Char('Contract No')
    customer=fields.Many2one('res.partner',required=True)
    products_detail=fields.One2many('droga.pharma.price.list','header')
    date_from = fields.Date('Date from',tracking=True)
    date_to = fields.Date('Date to',tracking=True)
    status=fields.Selection([('Active', 'Active'),('Offer','Offer'), ('Closed', 'Closed')],required=True,default='Offer',tracking=True)
    pharmacy_group_id = fields.Many2many('droga.prod.categ.pharma',store=True)
    margin = fields.Float(string='Margin')
    def populate_items(self):
        for rec in self:
            rec.products_detail.unlink()
            prods=self.env['product.template'].search([('list_price_phar', '!=', 0),('list_price_phar', '!=', 1)])
            for prod in prods:
                val={'product': prod.id,
                     'header':rec.id,
                     'selling_price':prod.list_price_phar,
                     'rev_selling_price':prod.list_price_phar}
                rec.products_detail.create(val)
    def update_margin(self):
        for rec in self:
            if rec.pharmacy_group_id:
                entries=rec.products_detail.search([('pharmacy_group_id','in',rec.pharmacy_group_id.ids)])
            else:
                entries = rec.products_detail
            for det in entries:
                det.write({'margin': rec.margin,
                           'rev_selling_price':det.selling_price*(1+(rec.margin/100))})

    def generate_report(self):
        return {
            'name': 'Price list',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'droga.pharma.product',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_header_cost_list': self.id
            }
        }

class pharma_price_list(models.Model):
    _name='droga.pharma.price.list'
    header=fields.Many2one('droga.pharma.price.list.header')
    product=fields.Many2one('product.template',string='Product ID')
    uom = fields.Many2one(related='product.pharma_uom')
    selling_price=fields.Float('Selling price')
    rev_selling_price = fields.Float('Selling price')
    margin=fields.Float(default=0,string='Margin')
    pharmacy_group_id = fields.Many2one('droga.prod.categ.pharma',related='product.pharmacy_group_id',store=True)

    @api.onchange("margin")
    def _on_change_margin(self):
        for rec in self:
            rec.rev_selling_price=rec.selling_price*(1+(rec.margin/100))

class product_offering_report(models.TransientModel):
    _name='droga.pharma.product'
    prod_group=fields.Many2many('droga.prod.categ.pharma')
    fileout = fields.Binary('File', readonly=True)
    header_cost_list=fields.Many2one('droga.pharma.price.list.header')

    @staticmethod
    def generate_report(self):
        if self.prod_group:
            excel_data = self.header_cost_list.products_detail.filtered(lambda x: x.pharmacy_group_id.id in self.prod_group.ids)
        else:
            excel_data = self.header_cost_list.products_detail

        header=self.header_cost_list
        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        sheet = workbook.add_worksheet('Products offering')

        bold = workbook.add_format({'bold': True})

        header_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 22})
        main_title_format = workbook.add_format({
            'bold': 0,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 16})
        parameter_format = workbook.add_format({
            'bold': 1,
            'border': 7,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
            'fg_color': '#F6F5F5'})

        small_header_format = workbook.add_format({
            'bold': 0,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})
        num_format = workbook.add_format({'num_format': 43, 'border': 7})
        fields_format = workbook.add_format({ 'border': 7})
        # set header

        if self.env.company.logo_web:
            company_image=io.BytesIO(base64.b64decode(self.env.company.logo_web))
            sheet.insert_image(0,0,"test_image.png",{'image_data':company_image,'y_scale':0.45,'y_offset':3})

        row_start = 0
        sheet.set_row(row_start + 1, 30)
        sheet.merge_range('A' + str(row_start + 1) + ':E' + str(row_start + 1), 'DROGA PHARMA P.L.C', header_format)
        sheet.merge_range('A' + str(row_start + 2) + ':E' + str(row_start + 2), 'Products offering for '+header.customer.name, main_title_format)
        sheet.merge_range('A3:E3', 'Addis Ketema subcity,Wo 6,H.No:133. Tel:+251-112-73-45-54/2519-13-66-75-37. Website:www.drogapharma.com. Addis Ababa, Ethiopia', small_header_format)
        sheet.merge_range('A' + str(row_start + 4) + ':B' + str(row_start + 6), 'Validity from : ' + str(header.date_from),
                          parameter_format)
        sheet.merge_range('C' + str(row_start + 4) + ':E' + str(row_start + 6), 'Validity to : ' + str(header.date_to),
                          parameter_format)

        # Set column widths

        sheet.set_column(0, 0, 15)  # product_code
        sheet.set_column(1, 1, 90)  # description
        sheet.set_column(2, 2, 35)  # group
        sheet.set_column(3, 3, 15)  # uom
        sheet.set_column(4, 4, 12)  # selling price

        row = 7
        sheet.write(row, 0, 'Code', title_format)
        sheet.write(row, 1, 'Product description', title_format)
        sheet.write(row, 2, 'Category', title_format)
        sheet.write(row, 3, 'Unit', title_format)
        sheet.write(row, 4, 'Selling price', title_format)

        # Iterate over excel_data and write the values to the sheet
        for prod in excel_data:
            row = row + 1
            sheet.write(row, 0, prod.product.default_code,fields_format)
            sheet.write(row, 1, prod.product.name,fields_format)
            sheet.write(row, 2, prod.pharmacy_group_id.categ,fields_format)
            sheet.write(row, 3, prod.uom.name if prod.uom else ' ',fields_format)
            sheet.write(row, 4, prod.rev_selling_price,num_format)








        workbook.close()

        self.fileout = base64.b64encode(file_io.getvalue())
        file_io.close()

        datetime_string = fields.Datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'Products offering for {header.customer.name} {header.date_from}_{datetime_string}.xlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': f'web/content/?model={self._name}&id={self.id}&field=fileout&download=true&filename={filename}'
        }

class account_move_ext(models.Model):
    _inherit = 'account.move'
    customer_emp = fields.Many2one('droga.pharma.cust.employees', string='Customer Name',
                                   compute='_get_cust_emp',store=True)
    cust_id_linked = fields.Char('Employee ID', related='customer_emp.cust_id')

    @api.depends('name')
    def _get_cust_emp(self):
        for rec in self:
            rec.customer_emp=self.env['sale.order'].search([('name','=',rec.invoice_origin)]).customer_emp if len(self.env['sale.order'].search([('name','=',rec.invoice_origin)]))>0 else False

