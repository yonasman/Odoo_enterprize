from odoo import api, fields, models
from io import BytesIO
import xlsxwriter
import base64
import re


class MarketReportWizard(models.TransientModel):
    _name = "market.analysis.report.wizard"

    _description = "Print Market Analysis Excel Report"
    fileout = fields.Binary(string='File Output')

    local_agent = fields.Char(string='Local Agent')
    manufacturer = fields.Char(string='Manufacturer')


    generic_name = fields.Char(string='Generic Name')
    brand_name = fields.Char(string='Brand Name')

    product_type = fields.Selection([('medicine', 'Medicine'), ('medical_device', 'Medical Device')])

    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')

    def action_get_xls(self, data):

        file_io = BytesIO()
        f_name =[]
        f_name.append("Market Analysis Based on ")

        if self.product_type:
            f_name.append("product Type")
        if self.local_agent:
            f_name.append("Local Agent")
        if self.generic_name:
            f_name.append("Generic Name")
        if self.brand_name:
            f_name.append("Brand Name")

        file_name = ', '.join(f_name)
        file_name = str(file_name)

        workbook = xlsxwriter.Workbook(file_io)
        self.generate_xls_report(workbook, data, file_name)
        workbook.close()

        self.fileout = base64.b64encode(file_io.getvalue())
        file_io.close()

        datetime_string = fields.Datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = file_name + f' From {self.date_from} to {self.date_to}.xlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': f'web/content/?model={self._name}&id={self.id}&field=fileout&download=true&filename={filename}'
        }

    def generate_xls_report(self, workbook, excel_data, title_name):

        sheet = workbook.add_worksheet('Market Analysis')
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
        sheet.merge_range('A' + str(row_start + 2) + ':O' + str(row_start + 2), title_name, main_title_format)
        sheet.merge_range('A' + str(row_start + 3) + ':G' + str(row_start + 7), 'Date from : ' + str(self.date_from),
                          parameter_format)
        sheet.merge_range('H' + str(row_start + 3) + ':O' + str(row_start + 7), 'Date to : ' + str(self.date_to),
                          parameter_format)

        # Set column widths

        sheet.set_column(0, 0, 25)  # Local Agent
        sheet.set_column(1, 1, 25)  # manufacturer
        sheet.set_column(2, 2, 20)  # application_number
        sheet.set_column(3, 3, 25)  # generic_name
        sheet.set_column(4, 4, 35)  # brand_name
        sheet.set_column(5, 5, 30)  # unit
        sheet.set_column(6, 6, 20)  # unit_price
        sheet.set_column(7, 7, 15)  # quantity
        sheet.set_column(8, 8, 15)  # unit_price
        sheet.set_column(9, 9, 15)  # total_price

        sheet.set_column(10, 10, 15)  # unit_price
        sheet.set_column(11, 11, 15)  # pfi_date
        sheet.set_column(12, 12, 15)  # ip_approval_date
        sheet.set_column(13, 13, 15)  # date_sold
        sheet.set_column(14, 14, 15)  # product_type
        sheet.set_column(15, 15, 15)  # pharma_category

        row = 9
        col = 0
        sheet.write(row, col + 0, 'Local Agent', title_format)
        sheet.write(row, col + 1, 'Manufacturer', title_format)
        sheet.write(row, col + 2, 'Application Number', title_format)
        sheet.write(row, col + 3, 'Generic Name', title_format)
        sheet.write(row, col + 4, 'Brand Name', title_format)

        sheet.write(row, col + 5, 'Unit', title_format)
        sheet.write(row, col + 6, 'Unit Price in $', title_format)
        sheet.write(row, col + 7, 'Quantity', title_format)
        sheet.write(row, col + 8, 'Total Price in $', title_format)

        sheet.write(row, col + 9, 'Date of PFI', title_format)
        sheet.write(row, col + 10, 'Date of IP Approval', title_format)
        sheet.write(row, col + 11, 'Date Sold', title_format)
        sheet.write(row, col + 12, 'Product Type', title_format)
        sheet.write(row, col + 13, 'Pharmacological Category', title_format)

    # Iterate over excel_data and write the values to the sheet
        for index, ed in enumerate(excel_data):
            row = row + 1

            sheet.write(row, col + 0, re.sub('<[^<]+?>', '', str(ed.get('local_agent', ''))))
            sheet.write(row, col + 1, re.sub('<[^<]+?>', '', str(ed.get('manufacturer', ''))))
            sheet.write(row, col + 2, re.sub('<[^<]+?>', '', str(ed.get('application_number', ''))))
            sheet.write(row, col + 3, re.sub('<[^<]+?>', '', str(ed.get('generic_name', ''))))
            sheet.write(row, col + 4, re.sub('<[^<]+?>', '', str(ed.get('brand_name', ''))))

            sheet.write(row, col + 5, re.sub('<[^<]+?>', '', str(ed.get('unit', ''))))
            sheet.write(row, col + 6, re.sub('<[^<]+?>', '', str(ed.get('unit_price', ''))))
            sheet.write(row, col + 7, re.sub('<[^<]+?>', '', str(ed.get('quantity', ''))))
            sheet.write(row, col + 8, re.sub('<[^<]+?>', '', str(ed.get('total_price', ''))))

            sheet.write(row, col + 9, re.sub('<[^<]+?>', '', str(ed.get('pfi_date', ''))))
            sheet.write(row, col + 10, re.sub('<[^<]+?>', '', str(ed.get('ip_approval_date', ''))))
            sheet.write(row, col + 11, re.sub('<[^<]+?>', '', str(ed.get('date_sold', ''))))

            sheet.write(row, col + 12, re.sub('<[^<]+?>', '', str(ed.get('product_type', ''))))
            sheet.write(row, col + 13, re.sub('<[^<]+?>', '', str(ed.get('pharma_category', ''))))

    def action_wizard_print_excel_report(self):
        domain = []
        if self.date_to and self.date_from:
            domain = [
                ('date_sold', '>=', self.date_from),
                ('date_sold', '<=', self.date_to),
            ]

        if self.local_agent:
            domain.append(('local_agent', '=', self.local_agent))
        if self.manufacturer:
            domain.append(('manufacturer', '=', self.manufacturer))
        if self.brand_name:
            domain.append(('brand_name', '=', self.brand_name))
        if self.generic_name:
            domain.append(('generic_name', '=', self.generic_name))
        if self.product_type:
            domain.append(('product_type', '=', self.product_type))


        excel_data = self.env['add.market.sale'].search_read(domain)
        return self.action_get_xls(excel_data)

    def action_cancel(self):

        return {'type': 'ir.actions.act_window_close'}
