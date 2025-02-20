import io

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from io import BytesIO
import xlsxwriter
import base64
import datetime
import re


class salesWizard(models.TransientModel):
    _name = "sales.report.costing.wizard"
    _description = "Print sales Excel Report"
    fileout = fields.Binary(string='File Output')

    date_to = fields.Date(string='To Date', default=datetime.date.today() + relativedelta(weeks=0, weekday=-1))
    date_from = fields.Date(string='From Date', default=datetime.date.today() - relativedelta(weeks=1, weekday=0))

    def action_get_sales_xls(self, data):

        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)
        self.generate_sales_xls_report(workbook, data)
        workbook.close()

        self.fileout = base64.b64encode(file_io.getvalue())
        file_io.close()

        datetime_string = fields.Datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'Cost of Sales Report From {self.date_from}_{datetime_string}.xlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': f'web/content/?model={self._name}&id={self.id}&field=fileout&download=true&filename={filename}'
        }

    def generate_sales_xls_report(self, workbook, excel_data):
        sheet = workbook.add_worksheet('Cost of Sales Report')

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
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'text_wrap': 1,
            'fg_color': '#F6F5F5'})

        # set header
        row_start = 1
        sheet.set_row(row_start + 1, 30)
        sheet.merge_range('A' + str(row_start + 1) + ':O' + str(row_start + 1), 'DROGA PHARMA P.L.C', header_format)
        sheet.merge_range('A' + str(row_start + 2) + ':O' + str(row_start + 2), 'Cost of Sales', main_title_format)
        sheet.merge_range('A' + str(row_start + 3) + ':G' + str(row_start + 7), 'Date from : ' + str(self.date_from),
                          parameter_format)
        sheet.merge_range('H' + str(row_start + 3) + ':O' + str(row_start + 7), 'Date to : ' + str(self.date_to),
                          parameter_format)

        if self.env.company.logo_web:
            company_image=io.BytesIO(base64.b64decode(self.env.company.logo_web))
            sheet.insert_image(0,14,"test_image.png",{'image_data':company_image,'y_scale':0.6,'y_offset':1})

        sheet.set_column(1, 1, 30)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 25)
        sheet.set_column(4, 4, 25)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 30)
        sheet.set_column(7, 7, 30)
        sheet.set_column(8, 8, 30)
        sheet.set_column(9, 9, 30)
        sheet.set_column(10, 10, 30)
        sheet.set_column(11, 11, 30)
        sheet.set_column(12, 12, 30)
        sheet.set_column(13, 13, 30)
        sheet.set_column(14, 14, 30)

        row = 8
        col = 0
        num = 1

        sheet.write(row, col + 0, 'Index', title_format)
        sheet.write(row, col + 1, 'Product Code', title_format)
        sheet.write(row, col + 2, 'Product Description', title_format)
        sheet.write(row, col + 3, 'Product Category', title_format)
        sheet.write(row, col + 4, 'Sales Ref', title_format)
        sheet.write(row, col + 5, 'Sales Date', title_format)
        sheet.write(row, col + 6, 'Invoiced amount', title_format)
        sheet.write(row, col + 7, 'Quantity Invoiced', title_format)
        sheet.write(row, col + 8, 'Unit Cost', title_format)
        sheet.write(row, col + 9, 'Unit Price', title_format)
        sheet.write(row, col + 10, 'Quantity', title_format)
        sheet.write(row, col + 11, 'Total Cost', title_format)
        sheet.write(row, col + 12, 'Profit', title_format)
        sheet.write(row, col + 13, 'Profit Margin', title_format)
        sheet.write(row, col + 14, 'Profit Margin Progress Bar', title_format)

        for index, ed in enumerate(excel_data):
            row = row + 1
            sheet.write(row, col + 1, num, bold)
            num = num + 1
            sheet.write(row, col + 1, ed.get('product_code'), bold)
            sheet.write(row, col + 2, ed.get('product_descr'))
            sheet.write(row, col + 3, ed.get('product_categ'))
            sheet.write(row, col + 4, ed.get('sales_ref'))
            sheet.write(row, col + 5, str(ed.get('sales_date')))
            sheet.write(row, col + 6, ed.get('invoiced_amt'))
            sheet.write(row, col + 7, ed.get('qty_invoiced'))
            sheet.write(row, col + 8, ed.get('unit_cost'))
            sheet.write(row, col + 9, ed.get('quantity'))
            sheet.write(row, col + 10, ed.get('price_unit'))
            sheet.write(row, col + 11, ed.get('amount'))
            sheet.write(row, col + 12, ed.get('profit'))
            sheet.write(row, col + 13, ed.get('profit_margin'))
            sheet.write(row, col + 14, ed.get('profit_margin_progress_bar'))


    def action_wizard_print_sales_excel_report(self):
        domain = [
            ('sales_date', '>=', self.date_from),
            ('sales_date', '<=', self.date_to),
            ('company_id','=',self.env.company.id)
        ]
        excel_data = self.env['droga.sales.cost.of.sales'].search_read(domain)
        return self.action_get_sales_xls(excel_data)

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
