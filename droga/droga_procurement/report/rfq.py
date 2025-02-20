from odoo import api, fields, models
from io import BytesIO
import xlsxwriter
import datetime
from odoo.exceptions import UserError

try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes


class RfqExcelReport(models.TransientModel):

    _name = 'droga.purchase.rfq.excel.report'

    fileout = fields.Binary('File', readonly=True)

    def action_get_xls(self, rfq_id):

        # This generates our excel file
        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        # search RFQ
        rfq = self.env['droga.purhcase.request.rfq'].search(
            [('id', '=', rfq_id)])

        self.generate_xlsx_report(workbook, rfq)
        workbook.close()

        # The file to download will be stored under fileout field
        fileout_encoded = encodebytes(file_io.getvalue())
        self.fileout = fileout_encoded
        file_io.close()

        return fileout_encoded

    def generate_xlsx_report(self, workbook, rfq):
        sheet = workbook.add_worksheet('Request For Quotation')

        sheet.set_column('A:A', 10.5)
        sheet.set_column('B:B', 35)
        sheet.set_column('C:C', 11)
        sheet.set_column('D:D', 14)
        sheet.set_column('E:E', 18)
        sheet.set_column('F:F', 18)
        sheet.set_column('G:G', 16)

        row_start = 0
        date_format = workbook.add_format(
            {'num_format': 'd mmm yyyy', 'border': 7})
        num_format = workbook.add_format({'num_format': 43, 'border': 7})
        cent_format = workbook.add_format({'num_format': 41, 'border': 7})
        border = workbook.add_format({'border': 7})
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 22})
        main_title_format = workbook.add_format({
            'bold': 1,
            'border': 0,
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

        separator_format = workbook.add_format({
            'bold': 1,
            'border': 7,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
            'fg_color': '#D9D9D9'})

        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'left',
            'valign': 'vleft',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})
        title_format_num = workbook.add_format({
            'bold': 1,
            'border': 1,
            'num_format': 43,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        sheet.merge_range('A' + str(row_start + 1) + ':G' + str(row_start + 1),
                          rfq.company_id.name, header_format)
        sheet.merge_range('A' + str(row_start + 2) + ':G' +
                          str(row_start + 2), 'Request For Quotation', main_title_format)

        # rfq ref number
        sheet.merge_range('A' + str(row_start + 3) + ':C' +
                          str(row_start + 3), 'RFQ No:-'+str(rfq.name), title_format)
        sheet.merge_range('A' + str(row_start + 4) + ':C' +
                          str(row_start + 4), 'Vendor:-'+str(rfq.supplier_id.name), title_format)
        sheet.merge_range('A' + str(row_start + 5) + ':C' +
                          str(row_start + 5), 'Currency:-'+str(rfq.currency_id.name), title_format)

        sheet.write(row_start + 5, 0, 'S.No', title_format)
        sheet.write(row_start + 5, 1, 'Product', title_format)
        sheet.write(row_start + 5, 2, 'Unit', title_format)
        sheet.write(row_start + 5, 3, 'Qty', title_format)
        sheet.write(row_start + 5, 4, 'Unit price', title_format)
        sheet.write(row_start + 5, 5, 'Total price', title_format)
        sheet.write(row_start + 5, 6, 'Remark', title_format)
        row_start = 6

        counter = 1
        for record in rfq.rfq_lines:

            unit_price_start = 'D'+str(row_start+1)
            quantity_start = 'E'+str(row_start+1)
            formula_start = 'F'+str(row_start+1)

            formula = '='+unit_price_start+'*'+quantity_start

            sheet.write(row_start, 0, counter, border)
            sheet.write(row_start, 1, record.product_id.name, border)
            sheet.write(row_start, 2, record.product_uom.name, border)
            sheet.write(row_start, 3, record.product_qty, num_format)
            sheet.write(row_start, 4, 0, num_format)
            #sheet.write(row_start, 5, 0, border)
            sheet.write_formula(formula_start, formula, num_format)
            sheet.write(row_start, 6, '', border)

            row_start += 1
            counter += 1

        sheet.write(row_start, 4, 'Total price', title_format)
        sheet.write_formula('F'+str(row_start+1),
                            '=sum(F7:F'+str(row_start)+')', num_format)
