import json
import os.path
import xml.dom.minidom
import xml.etree.cElementTree as ET
from datetime import datetime
import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from io import BytesIO
from dateutil import parser

try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes


class account_move(models.Model):
    _inherit = "account.move"

    logged_user_id = fields.Many2one('res.users')
    current_user_id = fields.Many2one('res.users', compute="_get_current_user_id")
    # = fields.Many2one('res.users', string='My User', default=lambda self: self.env.user)

    FPMachineID = fields.Char("Machine ID")
    FSInvoiceNumber = fields.Char("FS Invoice Number")
    EJNumber = fields.Char("EJ Number")
    FTimeStamp = fields.Datetime("TimeStamp")
    is_invoice_printed_pos = fields.Boolean("Invoice Printed POS", default=False, tracking=True)
    tin_no = fields.Char(compute="get_tin_no", string="Tin No")
    sales_type = fields.Char('Sales order type', compute='_get_so_type', store=True)
    order_from = fields.Char("Order From", compute='_compute_order_from')

    customer_name1 = fields.Char(compute='_compute_order_from', string='Customer Name')
    cust_id = fields.Char(compute='_compute_order_from', string='Customer Name')

    sales_cost = fields.Float('Sales Cost',store=True)

    pos_device_ip_address = fields.Char("POS IP Address", compute='get_pos_address')
    pos_xml_folder = fields.Char("XML Folder Path", compute='get_pos_address')
    total_amount_word = fields.Char(compute="_get_total_amount_word")

    fileout = fields.Binary('File', readonly=True)
    core_amt = fields.Float('Core amount', compute="_get_core_amt", store=True)
    non_core_amt = fields.Float('Non-core amount', compute="_get_core_amt", store=True)

    # To add tracking to tax field
    amount_tax = fields.Monetary(
        string='Tax',
        compute='_compute_amount', store=True, readonly=True, tracking=True
    )

    @api.onchange("is_invoice_printed_pos")
    def _invoice_print_status_changed(self):
        for rec in self:
            sales = self.env['sale.order'].search([('name', '=', rec.invoice_origin)])
            for sale in sales:
                if rec.is_invoice_printed_pos:
                    sale.write({'invoice_printed': 'Yes'})
                else:
                    sale.write({'invoice_printed': 'o'})

    @api.onchange("FSInvoiceNumber")
    def _fs_changed(self):
        for rec in self:
            sales = self.env['sale.order'].search([('name', '=', rec.invoice_origin)])
            for sale in sales:
                if rec.FSInvoiceNumber:
                    sale.write({'inv_number': sale.inv_number+', '+rec['FSInvoiceNumber'] if sale.inv_number else rec['FSInvoiceNumber']})

    @api.depends('invoice_line_ids.price_subtotal')
    def _get_core_amt(self):

        for rec in self:
            core_sum = 0;
            for records in rec.invoice_line_ids:
                if records.product_id.product_tmpl_id.is_core_product:
                    core_sum = core_sum + records.price_subtotal
            rec.core_amt = core_sum
            if rec.amount_untaxed == 0:
                rec.non_core_amt = rec.amount_total - core_sum
            else:
                rec.non_core_amt = rec.amount_untaxed - core_sum

    def _compute_order_from(self):

        for record in self:
            record.order_from = ''
            recs = self.env['sale.order'].search([('name', '=', record.invoice_origin)])
            record.customer_name1 = ''
            record.cust_id = ''
            for r in recs:
                # get customer name
                record.cust_id = r.cust_id
                record.customer_name1 = r.cust_name
                if r.order_type:
                    record.order_from = r.order_type
                else:
                    record.order_from = r.order_from

    def _get_current_user_id(self):
        context = self._context
        self.current_user_id = self.env.user
        # return context.get('uid')

    def _get_total_amount_word(self):
        for record in self:
            record.total_amount_word = self.convert_to_word(record.amount_total)

    # @api.depends("partner_id")
    def get_tin_no(self):
        for record in self:
            record.tin_no = record.partner_id.vat

    @api.depends('invoice_payment_term_id')
    def _get_so_type(self):
        for rec in self:
            if rec.invoice_payment_term_id.apply_credit_limit:
                rec.sales_type = 'Credit'
            elif rec.invoice_payment_term_id.name == 'Sales return':
                rec.sales_type = 'Sales return'
            else:
                rec.sales_type = 'Cash'

    def get_pos_address(self):
        employee_rec = self.env['hr.employee'].sudo().search(
            [('user_id', '=', self.env.uid)], limit=1)

        # set pos ip address
        self.pos_device_ip_address = employee_rec.pos_device_ip_address
        self.pos_xml_folder = employee_rec.pos_xml_folder

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        return super().get_view(view_id, view_type, **options)

    def view_init(self):
        pass

    def update_fs_info(self,fsmachineid,fsinvoicenum,ejnumber,timestamp,type):
        for rec in self:
            if(fsmachineid):
                rec.write({
                    'FPMachineID': fsmachineid,
                })
            if (fsinvoicenum):
                rec.write({
                    'FSInvoiceNumber': fsinvoicenum,
                })
            if (ejnumber):
                rec.write({
                    'EJNumber': ejnumber,
                })
            if(type=="printed"):
                rec.write({
                    'FTimeStamp': datetime.now(),
                })
            else:
                if (timestamp):
                    rec.write({
                        'FTimeStamp': parser.parser().parse(timestamp) ,
                    })
            rec.write({
                'is_invoice_printed_pos': "true",
            })
            sales=self.env['sale.order'].search([('name','=',rec.invoice_origin)])
            for sale in sales:
                sale.write({'invoice_printed': 'Yes',
                            'fs_number': fsinvoicenum})
    def generate_sales_xml(self):

        file_io = BytesIO()
        # get employee record

        # if not self.pos_xml_folder:
        # raise ValidationError(
        # "The POS device IP address is not set for the current user, please contact the system administrator to set it.")

        for record in self:
            m_encoding = 'UTF-8'

            # Get Payment Type
            payment_type = record.sales_type

            Invoice = ET.Element("Invoice")
            # doc = ET.SubElement(Invoice, "status", date="20210123")
            ET.SubElement(Invoice, "Invoice_Type").text = "Invoice"
            ET.SubElement(Invoice, "Reference_Number").text = record.name
            ET.SubElement(Invoice, "Invoice_Date").text = str(
                record.invoice_date.month) + "." + str(record.invoice_date.day) + "." + str(record.invoice_date.year)
            ET.SubElement(Invoice, "Customer_Code").text = str(record.partner_id.id)
            ET.SubElement(
                Invoice, "Customer_Name").text = record.partner_id.name
            ET.SubElement(Invoice, "Customer_TIN").text = record.partner_id.vat
            ET.SubElement(Invoice, "Payment_Type").text = payment_type
            ET.SubElement(Invoice, "Invoice_DiscOrAdd_Amount").text = "0.00"

            for line in record.invoice_line_ids:

                if line.price_unit == 0:
                    continue

                tax_percent = 0
                # get tax id
                for tax_id in line.tax_ids:
                    if tax_id.type_tax_use == "sale" and tax_id.real_amount == 15:
                        tax_percent = 15

                Line_Items = ET.SubElement(Invoice, "Line_Items")
                ET.SubElement(Line_Items, "Item_ID").text = line.product_id.default_code
                ET.SubElement(Line_Items, "Item_Description").text = line.product_id.name
                ET.SubElement(Line_Items, "Item_Quantity").text = str(line.quantity)
                ET.SubElement(Line_Items, "Item_UOM").text = str(line.product_uom_id.name)
                ET.SubElement(Line_Items, "Item_Unit_Price").text = str(line.price_unit)
                ET.SubElement(Line_Items, "Item_Tax_Percent").text = str(tax_percent)
                ET.SubElement(Line_Items, "Item_DiscOrAdd_Amount").text = "0.00"

            dom = xml.dom.minidom.parseString(ET.tostring(Invoice))
            xml_string = dom.toprettyxml()
            part1, part2 = xml_string.split('?>')

            self.fileout = encodebytes(xml_string.encode('utf-8'))

            # save path
            save_path = record.pos_xml_folder
            name_of_file = record.name
            # completeName = os.path.join(save_path, name_of_file + ".xml")

            ##with open(completeName, 'w') as xfile:
            ##xfile.write(
            ##part1 + 'encoding=\"{}\"?>\n'.format(m_encoding) + part2)
            ##xfile.close()

            # change text into a binary array

            # This downloads file. The file is fileout and the name if filename
            return {
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': 'web/content/?model=' + self._name + '&id=' + str(
                    self.id) + '&field=fileout&download=true&filename=' + name_of_file + ".xml",
            }

    @api.model
    def create(self, vals):
        res = super(account_move, self).create(vals)
        if res.invoice_origin:
            if res.invoice_origin.startswith('SOD'):
                res.sales_cost = abs(
                        sum(self.env['stock.valuation.layer'].search([('origin', '=', res.invoice_origin)]).mapped('value')))
        return res

    def print_to_pos_peds(self):

        context = self._context

        for record in self:

            # Get Payment Type
            payment_type = "Credit"

            if record.invoice_payment_term_id.deliv_after_payment:
                payment_type = "Credit"

            header = {
                "ThirdPartyID": "Odoo",
                "TenantId": "TenantId",
                "TransactionID": str(record.id),
                "ReferenceNumber": record.invoice_origin,
                "PaymentType": payment_type,
                "PaymentReferenceNumber": record.name,
                "BuyerName": record.partner_id.name,
                "BuyerTaxIdNumber": record.partner_id.vat,
                "AddOnType": "percentage",
                "AddOnValue": "0",
                "DiscountType": "fixed",
                "DiscountValue": "0",
                "UserName": str(self.logged_user_id.name),
                "HeaderMemo": "Free Text",
                "FooterMemo": "Welcome Message",
                "TimeStamp": str(datetime.now().strftime("%Y-%m-%d %I:%M:%S")),
                "Remark": "",
                "ApprovedBy": str(self.logged_user_id.name),
                "LineItem": [

                ]

            }

            for line in record.invoice_line_ids:
                line_id = 1

                tax_percent = 0
                # get tax id
                for tax_id in line.tax_ids:
                    if tax_id.type_tax_use == "sale":  # and tax_id.real_amount == 15:
                        tax_percent = tax_id.real_amount

                line_item = {
                    "LineIndex": str(line_id),
                    "ItemTransactionId": str(line.id),
                    "ItemID": str(line.product_id.default_code),
                    "ItemShortName": str(line.product_id.name),
                    "ItemDescription": str(line.product_id.name),
                    "UnitName": str(line.product_uom_id.name),
                    "Quantity": str('%.2f' % line.quantity),
                    "UnitPrice": str('%.2f' % line.price_unit),
                    "TaxRate": str('%.2f' % tax_percent),
                    "AddOnType": "percentage",
                    "AddOnValue": "0",
                    "DiscountType": "fixed",
                    "DiscountValue": "0"
                }
                header["LineItem"].append(line_item)
                line_id += 1

        json_string = json.dumps(header)

        headers = {'ApiKey': 'b904ea3c8a3446a0894aeec285e774b7', 'Content-Type': 'application/json'}
        request = requests.post('http://192.168.10.64:8545/pedsfpsrv/api/SalesInvoice/PrintInvoice?printCopy=false',
                                data=json_string, headers=headers)

        return True

    def print_sales_attachment(self):

        if self.env.company.id == 1:  # droga
            if self.order_from in ('IM', 'WS', 'IM-IM', 'IM-WS'):
                res1 = self.env.ref('droga_sales.droga_sales_pos_attachment_action').report_action(self)
            else:
                res1 = self.env.ref('droga_sales.droga_sales_pos_attachment_a5_action').report_action(self)
            return res1
        elif self.env.company.id == 2:
            res1 = self.env.ref('droga_sales.ema_sales_pos_attachment_action').report_action(self)
            return res1

    def set_analytic_accounts(self):
        # get analytic account
        analytic_distribution = ""
        tax_ids = ''
        for record in self.invoice_line_ids:
            if record.analytic_distribution:
                analytic_distribution = record.analytic_distribution
            if record.tax_ids:
                tax_ids = record.tax_ids

            if analytic_distribution != '' and tax_ids != '':
                break

        if analytic_distribution == '' and tax_ids == '':
            ValidationError("At least fill the first line!")

        # fill empty analytic lines
        for record in self.invoice_line_ids:
            if analytic_distribution != '':
                record.analytic_distribution = analytic_distribution
            if tax_ids != '':
                record.tax_ids = tax_ids

    def set_analytic_accounts_only(self):
        # get analytic account
        analytic_distribution = ""
        tax_ids = ''
        for record in self.invoice_line_ids:
            if record.analytic_distribution:
                analytic_distribution = record.analytic_distribution

            if analytic_distribution != '':
                break

        if analytic_distribution == '':
            raise ValidationError("At least fill the first line!")

        # fill empty analytic lines
        for record in self.invoice_line_ids:
            if analytic_distribution != '':
                record.analytic_distribution = analytic_distribution

    def convert_to_word(self, num):
        num_strings = str(num)
        numbers = num_strings.split('.')

        word = self.int_to_word(int(numbers[0])) + ' birr'

        if len(numbers) == 2:
            if int(numbers[1]) != 0:
                if len(numbers[1]) == 1:
                    numbers[1] = int(numbers[1]) * 10.0

                word = self.int_to_word(int(numbers[0])) + ' birr and ' + self.int_to_word(int(numbers[1])) + ' cents'

        return word.capitalize()

    def int_to_word(self, num):
        d = {0: 'zero', 1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five',
             6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten',
             11: 'eleven', 12: 'twelve', 13: 'thirteen', 14: 'fourteen',
             15: 'fifteen', 16: 'sixteen', 17: 'seventeen', 18: 'eighteen',
             19: 'nineteen', 20: 'twenty',
             30: 'thirty', 40: 'forty', 50: 'fifty', 60: 'sixty',
             70: 'seventy', 80: 'eighty', 90: 'ninety'}
        k = 1000
        m = k * 1000
        b = m * 1000
        t = b * 1000

        assert (0 <= num)

        if (num < 20):
            return d[num]

        if (num < 100):
            if num % 10 == 0:
                return d[num]
            else:
                return d[num // 10 * 10] + '-' + d[num % 10]

        if (num < k):
            if num % 100 == 0:
                return d[num // 100] + ' hundred'
            else:
                return d[num // 100] + ' hundred ' + self.int_to_word(num % 100)

        if (num < m):
            if num % k == 0:
                return self.int_to_word(num // k) + ' thousand'
            else:
                return self.int_to_word(num // k) + ' thousand ' + self.int_to_word(num % k)

        if (num < b):
            if (num % m) == 0:
                return self.int_to_word(num // m) + ' million'
            else:
                return self.int_to_word(num // m) + ' million ' + self.int_to_word(num % m)

        if (num < t):
            if (num % b) == 0:
                return self.int_to_word(num // b) + ' billion'
            else:
                return self.int_to_word(num // b) + ' billion ' + self.int_to_word(num % b)

        if (num % t == 0):
            return self.int_to_word(num // t) + ' trillion'
        else:
            return self.int_to_word(num // t) + ' trillion ' + self.int_to_word(num % t)

        raise AssertionError('num is too large: %s' % str(num))


class account_move_line(models.Model):
    _inherit = "account.move.line"

    @api.depends("product_id")
    def get_item_code(self):
        for record in self:
            record.item_code = record.product_id.product_tmpl_id.default_code

    item_code = fields.Char(compute="get_item_code", string="Item Code", store=True)
    item_description_alternate = fields.Char("Item Description Alternate")
    item_uom_alternate = fields.Char("UoM Alternate", default="")
    account = fields.Char(related='account_id.code', store=True)
    origin_ref = fields.Char(compute="get_origin_ref", string="Origin reference", store=True)
    profit_cost_center=fields.Char('Profit / Cost Center',compute='get_acc_move',store=True,default='-')

    @api.model
    def create(self, vals):
        ret= super(account_move_line, self).create(vals)
        for rec in ret:
            if rec.profit_cost_center=='-' and rec.account and rec.journal_id.id==2:
                if rec.account.startswith('5'):
                    analytic=self.env['stock.move.line'].search([('move_id','=',rec.move_id.stock_move_id.id)])
                    if len(analytic)>0:
                        rec.profit_cost_center=analytic[0].trans_warehouse.linked_analytic.name if analytic[0].trans_warehouse.linked_analytic else rec.profit_cost_center
        return ret

    @api.depends('analytic_distribution')
    def get_acc_move(self):
        for rec in self:
            if rec.profit_cost_center=='-' and rec.analytic_distribution:
                if rec.company_id.id==2:
                    for key, value in rec.analytic_distribution.items():
                        analytics=self.env['account.analytic.account'].search([('id','=',key),('plan_id','in',(16,19))])
                        if len(analytics)>0:
                            rec.profit_cost_center=analytics[0].name
                else:
                    for key, value in rec.analytic_distribution.items():
                        analytics = self.env['account.analytic.account'].search(
                            [('id', '=', key), ('plan_id', 'in', (1, 2))])
                        if len(analytics) > 0:
                            rec.profit_cost_center = analytics[0].profit_center.name if analytics[0].plan_id.id == 2 and analytics[
                                0].profit_center else analytics[0].name


    def get_origin_ref(self):
        for record in self:
            if record.name and record.journal_id.id in (2, 201):
                stock_move_line = self.env['stock.move.line'].search([('reference', '=', record.name.split(' - ')[0])])
                if len(stock_move_line) > 0:
                    record.origin_ref = stock_move_line[0].move_id.origin
                else:
                    record.origin_ref = '-'
            else:
                record.origin_ref = '-'

    @api.onchange('analytic_distribution')
    def analytic_distribution(self):
        ValidationError("Hello")
