from odoo import models,fields

#class tender_master_xls(models.AbstractModel):     Default type
#My point is to have a transient model inherit the report.report_xlsx.abstract and immplement all logic and use interface from here as well
class tender_master_xls(models.TransientModel):
    _name='report.droga_tender.tender_master_xls_rep'
    #_inherit = 'report.report_xlsx.abstract'

    posted_date_from=fields.Date('Posted date from')
    posted_date_to = fields.Date('Posted date to')

    def generate_xlsx_report(self, workbook, data, tenders):

        sheet = workbook.add_worksheet('Tender master list')
        bold = workbook.add_format({'bold': True})
        sheet.write(0, 1, 'Tender master file', bold)
        sheet.write(2, 0, 'Customer name',bold)

        sheet.write(2, 1, 'Media',bold)
        sheet.write(2, 2, 'Posted date',bold)
        row=3
        for obj in tenders:
            sheet.write(row, 0, obj.customer.name)
            sheet.write(row, 1, obj.media.media_name)
            sheet.write(row, 2, obj.posted_date_gre)
            row=row+1


