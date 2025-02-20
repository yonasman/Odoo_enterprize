
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
    _name='droga.inventory.reports.sc.excel'

    warehouse=fields.Many2one('stock.warehouse','Warehouse')
    product = fields.Many2one('product.product','Product')
    date_from=fields.Date('Date from', default=date(2022, 12, 20))
    date_to = fields.Date('Date to',default=fields.Date.today())
    per_location = fields.Binary('Per location?')
    fileout = fields.Binary('File', readonly=True)
    #fileout_filename = fields.Char('Filename', readonly=True)

    def action_get_xls(self):
        if not self.date_from:
            raise UserError("Date from field must be selected.")
        if not self.date_to:
            raise UserError("Date to field must be selected.")
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
        filename = '%s_%s_%s' % ('Stock card',self.warehouse.name, datetime_string)
        filename += '%2Exlsx'

        #This downloads file. The file is fileout and the name if filename
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + filename,
        }

    def generate_xlsx_report(self, workbook):
        sheet = workbook.add_worksheet('StockCard')
        #Header row count is 10

        row_start=0
        loc_ids_under_wh=self.env['stock.location'].search([('warehouse_id', '=', self.warehouse.id),('usage', '=', 'internal')])
        if self.product:
            stock_move_data=self.env['stock.move.line'].search(['|',('location_id', 'in', loc_ids_under_wh.ids),('location_dest_id', 'in', loc_ids_under_wh.ids),('state','=','done'),('date','>=',self.date_from),('date','<=',self.date_to),('product_id','=',self.product.id)],order="move_id desc").sorted(key=lambda r: r.date)
        else:
            stock_move_data = self.env['stock.move.line'].search(
                ['|', ('location_id', 'in', loc_ids_under_wh.ids), ('location_dest_id', 'in', loc_ids_under_wh.ids),
                 ('state', '=', 'done'), ('date', '>=', self.date_from), ('date', '<=', self.date_to)],
                order="move_id desc").sorted(key=lambda r: r.move_id.date)
        stock_products=list(dict.fromkeys(stock_move_data.sorted(key=lambda r: r.product_id.name)['product_id']))
        for prod in stock_products:
            self.get_droga_stockcard_sheet_with_header(sheet, workbook, prod,row_start)
            row_start+=11
            date_format = workbook.add_format({'num_format': 'd mmm yyyy', 'border': 7})
            num_format = workbook.add_format({'num_format': 43, 'border': 7})
            cent_format = workbook.add_format({'num_format': 41, 'border': 7})
            border = workbook.add_format({'border': 7})
            balance = 0
            #self.generate_stockcard_per_item(sheet,workbook,row_start,stock_move_data.sorted(key=lambda r: r.move_id.date),loc_ids_under_wh)
            for move_line in stock_move_data:
                if move_line['product_id'].id==prod.id:
                    sheet.write(row_start, 0, move_line['move_id'].date, date_format)
                    sheet.write(row_start, 1,
                                move_line['origin'] if move_line['origin'] else move_line['reference'])
                    # This avoids internal transfers from printed in the system
                    if move_line['location_id'].id in loc_ids_under_wh.ids and move_line[
                        'location_dest_id'].id in loc_ids_under_wh.ids:
                        continue
                    if move_line['location_id'] in loc_ids_under_wh:
                        sheet.write(row_start, 2, move_line.move_id.sale_line_id.order_id.partner_id.name if move_line.move_id.sale_line_id else move_line['location_dest_id'].complete_name)
                    else:
                        sheet.write(row_start, 2, move_line['location_id'].complete_name)

                    if move_line['location_id'] in loc_ids_under_wh:
                        if move_line['location_dest_id'].usage == 'inventory':
                            sheet.write(row_start, 5, move_line['import_quant'] * -1, num_format)
                            balance -= move_line['import_quant']
                            sheet.write(row_start, 3, 0, num_format)
                            sheet.write(row_start, 4, 0, num_format)
                        else:
                            sheet.write(row_start, 4, move_line['import_quant'], num_format)
                            balance -= move_line['import_quant']
                            sheet.write(row_start, 3, 0, num_format)
                            sheet.write(row_start, 5, 0, num_format)
                    else:
                        if move_line['location_id'].usage == 'inventory':
                            sheet.write(row_start, 5, move_line['import_quant'], num_format)
                            balance += move_line['import_quant']
                            sheet.write(row_start, 4, 0, num_format)
                            sheet.write(row_start, 3, 0, num_format)
                        else:
                            sheet.write(row_start, 3, move_line['import_quant'], num_format)
                            balance += move_line['import_quant']
                            sheet.write(row_start, 4, 0, num_format)
                            sheet.write(row_start, 5, 0, num_format)

                    sheet.write(row_start, 6, balance, num_format)

                    sheet.write(row_start, 7, int(move_line['product_id'].list_price), num_format)
                    sheet.write(row_start, 8, (move_line['product_id'].list_price - int(
                        move_line['product_id'].list_price)) * 100, cent_format)
                    if move_line['lot_id'].name:
                        sheet.write(row_start, 9, move_line['lot_id'].name)
                    if move_line['expiration_date']:
                        sheet.write(row_start, 10, move_line['expiration_date'], date_format)
                    if move_line['fs_number']:
                        sheet.write(row_start, 11, move_line['fs_number'], date_format)
                    row_start+=1
            row_start+=5


    def generate_stockcard_per_item(self,sheet,workbook,row_start,stock_move_data,loc_ids):
        date_format = workbook.add_format({'num_format': 'd mmm yyyy','border': 7})
        num_format = workbook.add_format({'num_format': 43,'border': 7})
        cent_format = workbook.add_format({'num_format': 41,'border': 7})
        border=workbook.add_format({'border': 7})
        balance=0

        for stock_move in stock_move_data:
            sheet.write(row_start, 0, stock_move['move_id'].date,date_format)
            sheet.write(row_start, 1, stock_move['origin'] if stock_move['origin'] else stock_move['reference'])
            #This avoids internal transfers from printed in the system
            if stock_move['location_id'].id in loc_ids.ids and stock_move['location_dest_id'].id in loc_ids.ids:
                continue
            if stock_move['location_id'] in loc_ids:
                sheet.write(row_start, 2, stock_move['location_dest_id'].complete_name)
            else:
                sheet.write(row_start, 2, stock_move['location_id'].complete_name)

            if stock_move['location_id'] in loc_ids:
                if stock_move['location_dest_id'].usage=='inventory':
                    sheet.write(row_start, 5, stock_move['import_quant']*-1, num_format)
                    balance-=stock_move['import_quant']
                    sheet.write(row_start, 3, 0, num_format)
                    sheet.write(row_start, 4, 0, num_format)
                else:
                    sheet.write(row_start, 4, stock_move['import_quant'],num_format)
                    balance += stock_move['import_quant']
                    sheet.write(row_start, 3, 0,num_format)
                    sheet.write(row_start, 5, 0, num_format)
            else:
                if stock_move['location_id'].usage == 'inventory':
                    sheet.write(row_start, 5, stock_move['import_quant'], num_format)
                    balance += stock_move['import_quant']
                    sheet.write(row_start, 4, 0, num_format)
                    sheet.write(row_start, 3, 0, num_format)
                else:
                    sheet.write(row_start, 3, stock_move['import_quant'],num_format)
                    balance += stock_move['import_quant']
                    sheet.write(row_start, 4, 0,num_format)
                    sheet.write(row_start, 5,0, num_format)

            sheet.write(row_start, 6, balance, num_format)

            sheet.write(row_start, 7, int(stock_move['product_id'].list_price), num_format)
            sheet.write(row_start, 8, (stock_move['product_id'].list_price-int(stock_move['product_id'].list_price))*100, cent_format)
            if stock_move['lot_id'].name:
                sheet.write(row_start, 9, stock_move['lot_id'].name)
            if stock_move['expiration_date']:
                sheet.write(row_start, 10, stock_move['expiration_date'])

        return 1

    def get_droga_stockcard_sheet_with_header(self, sheet,workbook,prod,row_start):

        sheet.set_column('A:A', 12)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 30)
        sheet.set_column('D:D', 10)
        sheet.set_column('E:E', 10)
        sheet.set_column('F:F', 10)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:H', 10)
        sheet.set_column('I:I', 10)
        sheet.set_column('J:J', 15)
        sheet.set_column('K:K', 12)
        sheet.set_column('L:L', 12)

        #region excel_formats
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
            'text_wrap':1,
            'fg_color': '#F6F5F5'})
        #endregion


        #sheet.insert_image(row_start,8,"logo.png",{'image_data':droga_logo})

        #Sets row height to 30
        sheet.set_row(row_start, 30)
        sheet.set_row(row_start+1, 30)

        sheet.merge_range('A'+str(row_start+1)+':L'+str(row_start+1), 'DROGA PHARMA P.L.C' if self.env.company.id==1 else self.env.company.name, header_format)
        sheet.merge_range('A'+str(row_start+2)+':L'+str(row_start+2), 'Stock record card', main_title_format)
        sheet.merge_range('A'+str(row_start+3)+':L'+str(row_start+3), 'Product name, strength and dosage form : '+prod.default_code+'-'+prod.name, parameter_format)

        sheet.merge_range('A'+str(row_start+4)+':F'+str(row_start+4), 'Unit of measure : '+prod.product_tmpl_id.import_uom_new.name, parameter_format)
        sheet.merge_range('G'+str(row_start+4)+':L'+str(row_start+4), 'Location : '+self.warehouse.name, parameter_format)

        sheet.merge_range('A'+str(row_start+5)+':F'+str(row_start+5), 'Maximum stock level : '+str(prod.reordering_max_qty), parameter_format)
        sheet.merge_range('G'+str(row_start+5)+':L'+str(row_start+5), 'Emergency order point : '+str(prod.reordering_max_qty), parameter_format)

        sheet.merge_range('A'+str(row_start+6)+':F'+str(row_start+6), 'Average monthly consumption (AMC) : ', parameter_format)
        sheet.merge_range('G'+str(row_start+6)+':L'+str(row_start+6), 'Product category : '+prod.categ_id.name, parameter_format)

        sheet.merge_range('A' + str(row_start + 7) + ':F' + str(row_start + 7), 'Date from : '+str(self.date_from),parameter_format)
        sheet.merge_range('G' + str(row_start + 7) + ':L' + str(row_start + 7), 'Date to : '+str(self.date_to), parameter_format)

        sheet.merge_range('A'+str(row_start+8)+':L'+str(row_start+8), '', separator_format)

        sheet.merge_range('A'+str(row_start+9)+':A'+str(row_start+11), 'Date', title_format)
        sheet.merge_range('B'+str(row_start+9)+':B'+str(row_start+11), 'Doc No.\n(Receiving\nor Issue)', title_format)
        sheet.merge_range('C'+str(row_start+9)+':C'+str(row_start+11), 'Received\nfrom or\nIssued to', title_format)

        sheet.merge_range('D'+str(row_start+9)+':G'+str(row_start+10), 'Quantity', title_format)
        sheet.write(row_start+10, 3, 'Received',title_format)
        sheet.write(row_start+10, 4, 'Issued', title_format)
        sheet.write(row_start+10, 5, 'Loss/Adj.', title_format)
        sheet.write(row_start+10, 6, 'Balance', title_format)

        sheet.merge_range('H'+str(row_start+9)+':I'+str(row_start+10), 'Unit Price', title_format)
        sheet.write(row_start+10, 7, 'Birr', title_format)
        sheet.write(row_start+10, 8, 'Cent', title_format)

        sheet.merge_range('J'+str(row_start+9)+':J'+str(row_start+11), 'Batch #', title_format)
        sheet.merge_range('K'+str(row_start+9)+':K'+str(row_start+11), 'Expiry\nDate', title_format)
        sheet.merge_range('L'+str(row_start+9)+':L'+str(row_start+11), 'FS Number', title_format)

        return sheet

