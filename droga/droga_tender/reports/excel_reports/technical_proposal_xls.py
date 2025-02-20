import base64
import io

from odoo import api, fields, models
from io import BytesIO
import xlsxwriter
import datetime
from odoo.exceptions import UserError

try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes

#class tender_master_xls(models.AbstractModel):     Default type
#My point is to have a transient model inherit the report.report_xlsx.abstract and immplement all logic and use interface from here as well
class tender_technical_proposal_master_xls(models.TransientModel):
    _name='droga.tender.reports.technical.proposal'

    tender_id=fields.Many2one('droga.tender.master','Tender')
    lot_no = fields.Char('Lot number')
    item_number = fields.Char('Item number')

    fileout = fields.Binary('File', readonly=True)
    #fileout_filename = fields.Char('Filename', readonly=True)

    def action_get_xls(self):
        if not self.tender_id:
            raise UserError("Tender must be selected.")

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
        filename = '%s_%s_%s' % ('Technical proposal ',self.tender_id['ten_name'], datetime_string)
        filename += '%2Exlsx'

        #This downloads file. The file is fileout and the name if filename
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + filename,
        }

    def generate_xlsx_report(self, workbook):
        sheet = workbook.add_worksheet('Technical proposal')

        sheet.set_column('A:A', 10.5)
        sheet.set_column('B:B', 35)
        sheet.set_column('C:C', 11)
        sheet.set_column('D:D', 18)
        sheet.set_column('E:E', 18)
        sheet.set_column('F:F', 18)
        sheet.set_column('G:G', 16)
        row_start=12
        date_format = workbook.add_format({'num_format': 'd mmm yyyy', 'border': 7})
        num_format = workbook.add_format({'num_format': 43, 'border': 7})
        cent_format = workbook.add_format({'num_format': 41, 'border': 7})
        border = workbook.add_format({'border': 7})
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format({
            'bold': 1,
            'border': 7,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 22})
        medium_header_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 23})
        big_header_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#d5d5dd',
            'font_size': 36})
        small_header_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 14})
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
            'align': 'center',
            'valign': 'vcenter',
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

        if self.env.company.logo_web:
            company_image = io.BytesIO(base64.b64decode(self.env.company.logo_web))
            sheet.insert_image(0, 0, "test_image.png", {'image_data': company_image, 'y_scale': 0.16, 'y_offset': 0})

        sheet.merge_range('A1:G1', 'Droga Pharma P.L.C', big_header_format)
        sheet.merge_range('A2:C2', 'Importer and Distributor  For:', medium_header_format)

        sheet.merge_range('A3:C3', 'Medicines', small_header_format)
        sheet.merge_range('A4:C4', 'Medical Supplies', small_header_format)
        sheet.merge_range('A5:C5', 'Medical devices', small_header_format)
        sheet.merge_range('A6:C6', 'Medical Equipments', small_header_format)
        sheet.merge_range('A7:C7', 'Laboratory Reagents and supplies', small_header_format)
        sheet.merge_range('A8:C8', 'Laboratory device and equipements', small_header_format)
        sheet.merge_range('A9:C9', 'Chemicals', small_header_format)
        sheet.merge_range('A10:C10', 'Preventive healthcare materials', small_header_format)

        sheet.merge_range('A12:C12', 'Ref No:__________________________', small_header_format)

        sheet.merge_range('E2:G2', 'Addis Ketema subcity,Wo 6,H.No:133', small_header_format)
        sheet.merge_range('E3:G3', 'Office:+251-112-73-45-54', small_header_format)
        sheet.merge_range('E4:G4', 'Mobile:+2519-13-66-75-37', small_header_format)
        sheet.merge_range('E5:G5', '             :+2519-29-90-85-65/66', small_header_format)
        sheet.merge_range('E6:G6', 'Fax:(+251)112-73-52-71', small_header_format)
        sheet.merge_range('E7:G7', 'E-mail: pharmadroga@gmail.com', small_header_format)
        sheet.merge_range('E8:G8', '           :contact@drogapharma.com', small_header_format)
        sheet.merge_range('E9:G9', 'Website:www.drogapharma.com', small_header_format)
        sheet.merge_range('E10:G10', 'Addis Ababa, Ethiopia', small_header_format)

        sheet.merge_range('E12:G12', 'Date - ' + self.env.cr.now().strftime("%B %d,%Y"), small_header_format)

        sheet.merge_range('A' + str(row_start + 1) + ':I' + str(row_start + 1), self.tender_id['customer'].name, header_format)
        sheet.merge_range('A' + str(row_start + 2) + ':I' + str(row_start + 2), self.tender_id['procurement_title'] if self.tender_id['procurement_title'] else ' ',header_format)
        sheet.merge_range('A' + str(row_start + 3) + ':I' + str(row_start + 3), 'Technical proposal',main_title_format)

        sheet.write(row_start+4, 0, 'S.No',title_format)
        sheet.write(row_start + 4, 1, 'Items', title_format)
        sheet.write(row_start + 4, 2, 'Unit', title_format)
        sheet.write(row_start + 4, 3, 'Item/spec requested.', title_format)
        sheet.write(row_start + 4, 4, 'Item/spec proposed', title_format)
        sheet.write(row_start + 4, 5, 'Supplier', title_format)
        sheet.write(row_start + 4, 6, 'Brand', title_format)
        sheet.write(row_start + 4, 7, 'Bidder compliance remark', title_format)
        sheet.write(row_start + 4, 8, 'Qty', title_format)
        sheet.write(row_start + 4, 9, 'Remark', title_format)
        row_start=row_start+5

        tot_amount=0

        recs=self.tender_id['detail_submissions_fin']
        if self.lot_no:
            recs=recs.filtered(
            lambda m: m.lot_number == self.lot_no)
        if self.item_number:
            recs=recs.filtered(
            lambda m: m.item_num == self.item_number)

        for rec in recs:
            sheet.write(row_start, 0, rec.item_num,border)
            item=rec.item_pro if rec.item_pro else rec.type_item.type_or_item_name
            sheet.write(row_start, 1, item if item else ' ',border)
            uom=rec.uom_reg_field
            sheet.write(row_start, 2, uom.uom_name if uom else ' ',border)

            sheet.write(row_start, 3, rec.item_des if rec.item_des else ' ',border)
            sheet.write(row_start, 4, rec.item_pro if rec.item_pro else ' ',border)
            sheet.write(row_start, 5, rec.supplier_new if rec.supplier_new else ' ',border)
            sheet.write(row_start, 6, rec.brand_model if rec.brand_model else ' ',border)
            sheet.write(row_start, 7, ' ', border)
            sheet.write(row_start, 8, rec.quantity,num_format)
            tot_amount+=rec.amount
            sheet.write(row_start, 9, rec.remark if rec.remark else ' ',border)

            row_start+=1

            for rec_detail in rec.tender_specs:
                sheet.write(row_start, 3, rec_detail.spec_requested if rec_detail.spec_requested else ' ', border)
                sheet.write(row_start, 4, rec_detail.spec_offered if rec_detail.spec_offered else ' ', border)
                sheet.write(row_start, 7, rec_detail.bidder_compliance_remark if rec_detail.bidder_compliance_remark else ' ', border)
                sheet.write(row_start, 9, rec_detail.remark if rec_detail.remark else ' ', border)
                row_start += 1

        row_start+=2

        sheet.write(row_start, 1, 'The Price is Valid for a period of 60 days.')
        sheet.write(row_start+1, 1, 'The Price include all the cost to the purchaser store.')
        sheet.write(row_start + 2, 1, 'Terms of Payment: Cash up on delivery or as per  the purchaser payment policy.')
        sheet.write(row_start + 3, 1, 'Delivery time: with in 3-5  days.')
        sheet.write(row_start + 5, 1, 'Prepared by: __________________________')
        sheet.write(row_start + 5, 4, 'Approved by: __________________________')