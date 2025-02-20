from odoo import models, fields, api
from datetime import datetime
import xlsxwriter


class SalesReportWizard(models.TransientModel):
    _name = 'sales.report.wizard'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    item_code = fields.Many2one('product.product', string='Item Code')
    city = fields.Many2one('res.city', string='City')
    payment_type = fields.Selection([('cash', 'Cash'), ('credit', 'Credit')], string='Payment Type')
    sales_person = fields.Many2one('res.users', string='Sales Person')

    def generate_report_data(self):
        sales = self.env['sale.order'].search([
            ('date_order', '>=', self.date_from),
            ('date_order', '<=', self.date_to),
            ('order_line.product_id', '=', self.item_code.id if self.item_code else None),
            ('partner_id.city_id', '=', self.city.id if self.city else None),
            ('payment_type', '=', self.payment_type),
            ('user_id', '=', self.sales_person.id if self.sales_person else None),
            ('state', 'in', ('sale', 'done'))
        ])

        workbook = xlsxwriter.Workbook('Sales Report.xlsx')
        worksheet = workbook.add_worksheet('Sales')

        # Write the header row
        header_format = workbook.add_format({'bold': True})
        worksheet.write(0, 0, 'Order Date', header_format)
        worksheet.write(0, 1, 'Order Number', header_format)
        worksheet.write(0, 2, 'Product', header_format)
        worksheet.write(0, 3, 'Qty', header_format)
        worksheet.write(0, 4, 'Price', header_format)
        worksheet.write(0, 5, 'Total', header_format)
        worksheet.write(0, 6, 'City', header_format)
        worksheet.write(0, 7, 'Sales Person', header_format)

        # Write the sales data
        row = 1
        for sale in sales:
            for line in sale.order_line:
                worksheet.write(row, 0, sale.date_order.strftime('%Y-%m-%d'))
                worksheet.write(row, 1, sale.name)
                worksheet.write(row, 2, line.product_id.name)
                worksheet.write(row, 3, line.product_uom_qty)
                worksheet.write(row, 4, line.price_unit)
                worksheet.write(row, 5, line.price_subtotal)
                # worksheet.write(row, 6, sale.partner_id.city_id.name if sale
                row += 1

                # Close the workbook
            workbook.close()

            # Return the xlsx file as a download
