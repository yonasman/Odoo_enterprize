
from odoo import api, fields, models
from io import BytesIO
import xlsxwriter
from datetime import date
from odoo.exceptions import UserError

try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes

#class tender_master_xls(models.AbstractModel):     Default type
#My point is to have a transient model inherit the report.report_xlsx.abstract and immplement all logic and use interface from here as well
class inventory_stock_card_xls(models.TransientModel):
    _name='droga.inventory.reports.stocktake.excel'

    warehouse=fields.Many2one('stock.warehouse','Warehouse')
    fileout = fields.Binary('File', readonly=True)

    def action_get_xls(self):
        if not self.warehouse:
            raise UserError("Warehouse field must be selected.")

        #This generates our excel file
        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)
        self.generate_xlsx_report(workbook)
        workbook.close()

        #The file to download will be stored under fileout field
        self.fileout = encodebytes(file_io.getvalue())
        file_io.close()

        #The file name is stored under filename
        datetime_string = self.env.cr.now().strftime("%Y%m%d_%H%M%S")
        filename = '%s_%s_%s' % ('Stock take',self.warehouse.name, datetime_string)
        filename += '%2Exlsx'

        #This downloads file. The file is fileout and the name if filename
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + filename,
        }

    def generate_xlsx_report(self, workbook):
        sheet = workbook.add_worksheet('StockTake')
        num_format = workbook.add_format({'num_format': 43})

        row_start=0
        loc_ids_under_wh=self.env['stock.location'].search([('warehouse_id', '=', self.warehouse.id),('usage', '=', 'internal')])

        stock_take_data = self.env['stock.quant'].search(
            [ ('location_id', 'in', loc_ids_under_wh.ids)], order="product_id desc").sorted(key=lambda r: r.product_id.default_code)

        self.get_droga_stockcard_sheet_with_header(sheet, workbook)

        for quant in stock_take_data:
            row_start+=1
            sheet.write(row_start, 0, quant.get_metadata()[0].get('xmlid') if quant.get_metadata()[0].get('xmlid') else quant.export_data(['id']).get('datas')[0][0])
            sheet.write(row_start, 1, quant.product_id.default_code)
            sheet.write(row_start, 2, quant.product_id.product_tmpl_id.name)
            sheet.write(row_start, 3, quant.lot_id.name if quant.lot_id else ' ')
            sheet.write(row_start, 4, quant.product_uom_id.name if self.warehouse.wh_type=='PH' else quant.import_uom.name)
            sheet.write(row_start, 5,
                        quant.quantity if self.warehouse.wh_type == 'PH' else quant.import_quant,num_format)
            sheet.write(row_start, 6,
                        0, num_format)

    def get_droga_stockcard_sheet_with_header(self, sheet,workbook):

        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 18)
        sheet.set_column('C:C', 30)
        sheet.set_column('D:D', 18)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 18)
        sheet.set_column('G:G', 18)

        #region excel_formats
        bold = workbook.add_format({'bold': True})
        green = workbook.add_format({'bold': True,'fg_color': '#3CB371'})


        sheet.write(0, 0, 'External ID', green)
        sheet.write(0, 1, 'Product code', bold)
        sheet.write(0, 2, 'Product description', bold)
        sheet.write(0, 3, 'Lot/Serial', bold)
        sheet.write(0, 4, 'UOM', bold)
        sheet.write(0, 5, 'On hand quantity', bold)
        sheet.write(0, 6, 'inventory_quantity' if self.warehouse.wh_type == 'PH' else 'import_counted', green)

        return sheet

