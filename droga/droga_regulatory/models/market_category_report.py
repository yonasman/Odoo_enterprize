import itertools
from odoo import api, fields, models
from io import BytesIO
import xlsxwriter
import base64
import re
from itertools import groupby


class MarketReportCategoryWizard(models.TransientModel):
    _name = "market.analysis.report.category.wizard"
    _description = "Print Market Analysis Excel Report"

    fileout = fields.Binary(string='File Output')

    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')


    def action_get_xls(self, data):
        file_io = BytesIO()
        f_name = []

        file_name = "Market Analysis Based on Categories"

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

        # Create separate sheets for each category
        categories = ['Manufacturer', 'Local Agent', 'Brand Name', 'Product Type', 'Generic Name']
        for category in categories:
            print(str(category) +" , "+ str(category)+" , "+ str(category)+" , "+ str(category)+" , "+ str(category)+" , "+ str(category)+" , "+ str(category)+" , "+ str(category))
            sheet = workbook.add_worksheet(category)
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
            sheet.merge_range('H' + str(row_start + 3) + ':Q' + str(row_start + 7), 'Date to : ' + str(self.date_to),
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
            sheet.set_column(8, 8, 20)  # unit_price
            sheet.set_column(9, 9, 30)  # total_price

            sheet.set_column(10, 10, 30)  # unit_price
            sheet.set_column(11, 11, 15)  # pfi_date
            sheet.set_column(12, 12, 15)  # ip_approval_date
            sheet.set_column(13, 13, 15)  # date_sold
            sheet.set_column(14, 14, 15)  # product_type
            sheet.set_column(15, 15, 15)  # pharma_category
            sheet.set_column(16, 16, 15)  # total_sales

            row = 9
            col = 0
            sheet.write(row, col + 0, 'Local Agent', title_format)
            sheet.write(row, col + 1, 'Manufacturer', title_format)
            sheet.write(row, col + 2, 'Application Number', title_format)
            sheet.write(row, col + 3, 'Generic Name', title_format)
            sheet.write(row, col + 4, 'Brand Name', title_format)
            sheet.write(row, col + 5, 'Country', title_format)

            sheet.write(row, col + 6, 'Unit', title_format)
            sheet.write(row, col + 7, 'Unit Price in $', title_format)
            sheet.write(row, col + 8, 'Quantity', title_format)
            sheet.write(row, col + 9, 'Total Price in $', title_format)

            sheet.write(row, col + 10, 'Total Sales', title_format)

            sheet.write(row, col + 11, 'Date of PFI', title_format)
            sheet.write(row, col + 12, 'Date of IP Approval', title_format)
            sheet.write(row, col + 13, 'Date Recorded', title_format)
            sheet.write(row, col + 14, 'Dosage Form', title_format)
            sheet.write(row, col + 15, 'Product Type', title_format)
            sheet.write(row, col + 16, 'Pharmacological Category', title_format)


            category_name = ""
            if category == "Manufacturer":
                category_name = "manufacturer"
            elif category == "Local Agent":
                category_name = "local_agent"
            elif category == "Brand Name":
                category_name = "brand_name"
            elif category == "Product Type":
                category_name = "product_type"
            elif category == "Generic Name":
                category_name = "generic_name"

            total_sales = {}
            total_sales["Unidentified name"] = 0
            for entry in excel_data:
                name = entry[category_name]
                total_price = entry['total_price']

                if name and name != "False":
                    if name in total_sales:
                        total_sales[name] += total_price
                    else:
                        total_sales[name] = total_price
                else:
                    total_sales["Unidentified name"] += total_price



            for sale in total_sales:
                print (str(sale) + ": " + str(total_sales[sale]))



            print("Done Iterating over total sales")

            converted_list = [str(value) for value in excel_data]



            cat_name = ""
            if category == "Manufacturer":
                sorted_list = sorted(excel_data, key=lambda x: str(x['manufacturer']))

                cat_name = "manufacturer"
            elif category == "Local Agent":
                sorted_list = sorted(excel_data, key=lambda x: str(x['local_agent']))

                cat_name = "local_agent"
            elif category == "Brand Name":
                sorted_list = sorted(excel_data, key=lambda x: str(x['brand_name']))
                cat_name = "brand_name"
            elif category == "Product Type":
                sorted_list = sorted(excel_data, key=lambda x: str(x['product_type']))
                cat_name = "product_type"
            elif category == "Generic Name":
                sorted_list = sorted(excel_data, key=lambda x: str(x['generic_name']))
                cat_name = "generic_name"




            # Iterate over ... excel_data and write the values to the sheet
            col = 0
            for index, ed in enumerate(sorted_list):

                row = row + 1

                if ed.get('local_agent'):
                    sheet.write(row, col + 0, re.sub('<[^<]+?>', '', str(ed.get('local_agent'))))
                if ed.get('manufacturer'):
                    sheet.write(row, col + 1, re.sub('<[^<]+?>', '', str(ed.get('manufacturer', ''))))
                if ed.get('application_number'):
                    sheet.write(row, col + 2, re.sub('<[^<]+?>', '', str(ed.get('application_number', ''))))
                if ed.get('generic_name'):
                    sheet.write(row, col + 3, re.sub('<[^<]+?>', '', str(ed.get('generic_name', ''))))
                if ed.get('brand_name'):
                    sheet.write(row, col + 4, re.sub('<[^<]+?>', '', str(ed.get('brand_name', ''))))

                if ed.get('country'):
                    sheet.write(row, col + 5, re.sub('<[^<]+?>', '', str(ed.get('country', ''))))

                if ed.get('unit'):
                    sheet.write(row, col + 6, re.sub('<[^<]+?>', '', str(ed.get('unit', ''))))
                if ed.get('unit_price'):
                    sheet.write(row, col + 7, re.sub('<[^<]+?>', '', str(ed.get('unit_price', ''))))
                if ed.get('quantity'):
                    sheet.write(row, col + 8, re.sub('<[^<]+?>', '', str(ed.get('quantity', ''))))
                if ed.get('total_price'):
                    sheet.write(row, col + 9, re.sub('<[^<]+?>', '', str(ed.get('total_price', ''))))

                if ed.get('pfi_date'):
                    sheet.write(row, col + 11, re.sub('<[^<]+?>', '', str(ed.get('pfi_date', ''))))
                if ed.get('ip_approval_date'):
                    sheet.write(row, col + 12, re.sub('<[^<]+?>', '', str(ed.get('ip_approval_date', ''))))
                if ed.get('date_sold'):
                    sheet.write(row, col + 13, re.sub('<[^<]+?>', '', str(ed.get('date_sold', ''))))


                if ed.get('dosage_form'):
                    sheet.write(row, col + 14, re.sub('<[^<]+?>', '', str(ed.get('dosage_form', ''))))

                if ed.get('product_type'):
                    sheet.write(row, col + 15, re.sub('<[^<]+?>', '', str(ed.get('product_type', ''))))
                if ed.get('pharma_category'):
                    sheet.write(row, col + 16, re.sub('<[^<]+?>', '', str(ed.get('pharma_category', ''))))


                if category == "Manufacturer":
                    if ed.get('manufacturer', ''):
                        if total_sales[str(ed.get('manufacturer'))]:
                            print(str(ed.get('manufacturer', '')) + str(total_sales[ed.get('manufacturer', '')]))
                            sheet.write(row, col + 10,
                                        re.sub('<[^<]+?>', '', str(total_sales[ed.get('manufacturer', '')])))


                        else:

                            sheet.write(row, col + 10,
                                        re.sub('<[^<]+?>', '', str(total_sales[ed.get('manufacturer', '')])))
                            print(str(ed.get('manufacturer', '')) + str(total_sales[ed.get('manufacturer', '')]))


                elif category == "Local Agent":
                    if ed.get('local_agent'):
                        if total_sales[str(ed.get('local_agent', ''))]:
                            print(str(ed.get('local_agent', '')) + str(total_sales[ed.get('local_agent', '')]))
                            sheet.write(row, col + 10,
                                        re.sub('<[^<]+?>', '', str(total_sales[str(ed.get('local_agent', ''))])))

                        else:
                            sheet.write(row, col + 10,
                                        re.sub('<[^<]+?>', '', str(total_sales[str(ed.get('local_agent', ''))])))
                    else:
                        print("no local agent")

                elif category == "Brand Name":
                    if ed.get('brand_name', ''):
                        if total_sales[str(ed.get('brand_name', ''))]:
                            print(str(ed.get('brand_name', '')) + str(total_sales[ed.get('brand_name', '')]))
                            sheet.write(row, col + 10,
                                    re.sub('<[^<]+?>', '', str(total_sales[str(ed.get('brand_name', ''))])))

                        else:

                            sheet.write(row, col + 10,
                                        re.sub('<[^<]+?>', '', str(total_sales[str(ed.get('brand_name', ''))])))

                elif category == "Product Type":
                    if ed.get('product_type', ''):
                        if total_sales[str(ed.get('product_type', ''))]:
                            print(str(ed.get('product_type', '')) + str(total_sales[ed.get('product_type', '')]))
                            sheet.write(row, col + 10,
                                        re.sub('<[^<]+?>', '', str(total_sales[str(ed.get('product_type', ''))])))


                        else:
                            sheet.write(row, col + 10,
                                        re.sub('<[^<]+?>', '', str(total_sales[str(ed.get('product_type', ''))])))

                elif category == "Generic Name":
                    if ed.get('generic_name', ''):
                        if total_sales[str(ed.get('generic_name', ''))]:
                            print(str(ed.get('generic_name', '')) + str(total_sales[ed.get('generic_name', '')]))
                            sheet.write(row, col + 10,
                                        re.sub('<[^<]+?>', '', str(total_sales[str(ed.get('generic_name', ''))])))


                        else:
                            sheet.write(row, col + 10,
                                        re.sub('<[^<]+?>', '', str(total_sales[str(ed.get('generic_name', ''))])))


    def action_wizard_print_excel_report(self):
        domain = []

        if self.date_to:
            domain = [('date_sold', '<=', self.date_to)]
        if self.date_from:
            domain = [
                ('date_sold', '>=', self.date_from),
            ]
        excel_data = self.env['droga.bdr.market.analysis'].search_read(domain)
        return self.action_get_xls(excel_data)

    def action_cancel(self):
            return {'type': 'ir.actions.act_window_close'}
